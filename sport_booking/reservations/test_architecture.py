import ast
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from django.db import DatabaseError, transaction
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from .models import Reservation
from .persistence import DjangoDataStore
from .tests import ReservationApiTests


class ArchitectureDependencyTests(SimpleTestCase):
    def test_entry_points_do_not_access_orm_or_mutate_reservation_state(self):
        def violations(source):
            problems = []
            for node in ast.walk(ast.parse(source)):
                modules = []
                if isinstance(node, ast.Import):
                    modules = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    modules = [module] + [
                        f'{module}.{alias.name}'.strip('.') for alias in node.names
                    ]
                if any(module.startswith('django.db')
                       or module.split('.')[-1] in ('models', 'persistence')
                       for module in modules):
                    problems.append(f'line {node.lineno}: direct persistence import')
                if isinstance(node, ast.Attribute):
                    if node.attr == 'objects':
                        problems.append(f'line {node.lineno}: ORM manager access')
                    if node.attr in ('status', 'state') and isinstance(node.ctx, ast.Store):
                        problems.append(f'line {node.lineno}: direct lifecycle assignment')
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                        and node.func.id == 'setattr' and len(node.args) >= 2
                        and isinstance(node.args[1], ast.Constant)
                        and node.args[1].value in ('status', 'state')):
                    problems.append(f'line {node.lineno}: dynamic lifecycle assignment')
            return problems

        root = Path(__file__).parent
        for filename in ('views.py', 'api.py', 'management/commands/expire_reservations.py'):
            with self.subTest(file=filename):
                self.assertEqual(violations((root / filename).read_text()), [], filename)

        # Check that the guard actually rejects representative forbidden changes.
        forbidden_examples = (
            'from .models import Reservation',
            'from . import models',
            'import django.db.models as orm',
            'from .persistence import DjangoDataStore',
            "Reservation.objects.filter(id=1).update(status='CONFIRMED')",
            "reservation.status = 'CONFIRMED'",
            "setattr(reservation, 'status', 'CONFIRMED')",
        )
        for source in forbidden_examples:
            with self.subTest(forbidden=source):
                self.assertTrue(violations(source), source)
        self.assertEqual(violations(
            "result = service.approve(reservation_id, actor)\n"
            "body = {'status': result.status}"
        ), [])

    def test_only_allowed_dependencies_are_used_by_logical_parts(self):
        root = Path(__file__).parent
        allowed_local = {
            'domain': set(), 'rules': {'domain'},
            'identity': {'domain'}, 'persistence': {'models', 'domain'},
            'services': {'domain', 'identity', 'persistence', 'rules'},
            'api': {'domain', 'services'}, 'views': {'wiring'},
            'wiring': {'api', 'identity', 'persistence', 'rules', 'services'},
        }
        for module, allowed in allowed_local.items():
            tree = ast.parse((root / f'{module}.py').read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.level:
                    imported = (node.module or '').split('.')[0]
                    if not imported:
                        imported = node.names[0].name
                    self.assertIn(imported, allowed, f'{module} imports {imported}')
                if isinstance(node, ast.ImportFrom) and node.module:
                    if module in ('api', 'views', 'services', 'rules', 'identity', 'domain'):
                        self.assertFalse(node.module.startswith('django.db'), module)
                    if module in ('services', 'rules', 'identity', 'domain'):
                        self.assertFalse(node.module.startswith('django.http'), module)
        service_tree = ast.parse((root / 'services.py').read_text())
        self.assertNotIn('DjangoDataStore', {
            name.id for name in ast.walk(service_tree) if isinstance(name, ast.Name)
        })
        command_tree = ast.parse((root / 'management/commands/expire_reservations.py').read_text())
        imports = {n.module for n in ast.walk(command_tree) if isinstance(n, ast.ImportFrom)}
        self.assertEqual(imports, {'django.core.management.base', 'reservations.wiring'})


class PersistenceFailureTests(TestCase):
    setUpTestData = classmethod(ReservationApiTests.setUpTestData.__func__)
    setUp = ReservationApiTests.setUp
    interval = ReservationApiTests.interval
    create = ReservationApiTests.create
    def test_failed_save_rolls_back_and_never_reports_success(self):
        reservation_id = self.create().json()['id']
        original_save = DjangoDataStore.save

        def fail_after_save(store, reservation):
            original_save(store, reservation)
            raise DatabaseError('simulated write failure')

        with patch.object(DjangoDataStore, 'save', fail_after_save):
            with self.assertRaises(DatabaseError):
                self.client.post(f'/api/reservations/{reservation_id}/confirm/')
        self.assertEqual(Reservation.objects.get(pk=reservation_id).status, 'DRAFT')
        self.assertFalse(transaction.get_rollback())
        self.assertEqual(self.client.post(
            f'/api/reservations/{reservation_id}/confirm/').status_code, 200)

    def test_failed_commit_rolls_back(self):
        reservation_id = self.create().json()['id']
        with patch.object(DjangoDataStore, 'commit', side_effect=DatabaseError('commit failure')):
            with self.assertRaises(DatabaseError):
                self.client.post(f'/api/reservations/{reservation_id}/confirm/')
        self.assertEqual(Reservation.objects.get(pk=reservation_id).status, 'DRAFT')

    def test_expiration_is_idempotent_and_preserves_terminal_states(self):
        from .wiring import build_service
        reservation_id = self.create(resource=self.approval_resource).json()['id']
        self.client.post(f'/api/reservations/{reservation_id}/confirm/')
        now = timezone.now()
        Reservation.objects.filter(pk=reservation_id).update(
            approval_requested_at=now - timedelta(hours=24),
        )
        with patch('reservations.rules.TimeRules.now', return_value=now):
            self.assertEqual(build_service().expire_due(), 1)
            self.assertEqual(build_service().expire_due(), 0)
        self.assertEqual(Reservation.objects.get(pk=reservation_id).status, 'EXPIRED')

    def test_invalid_resource_identifier_is_rejected_without_creating(self):
        import json
        for resource_id in (True, 1.5, 2**100):
            response = self.client.post('/api/reservations/', json.dumps({
                'resource_id': resource_id, **self.interval(),
            }), content_type='application/json')
            self.assertEqual(response.status_code, 400)
        self.assertFalse(Reservation.objects.exists())
