from datetime import timedelta

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone


class ReservationLifecycleMigrationTests(TransactionTestCase):
    def test_legacy_drafts_are_preserved_as_cancelled(self):
        previous = ('reservations', '0002_remove_reservation_reservation_valid_status_and_more')
        current = ('reservations', '0003_remove_draft_lifecycle')
        executor = MigrationExecutor(connection)
        executor.migrate([previous])
        try:
            apps = executor.loader.project_state([previous]).apps
            user = apps.get_model('auth', 'User').objects.create(username='legacy')
            sport = apps.get_model('reservations', 'Sport').objects.create(name='Legacy sport')
            resource = apps.get_model('reservations', 'Resource').objects.create(
                name='Legacy court', sport=sport, location='Ostrava',
                opens_at='08:00', closes_at='22:00',
            )
            model = apps.get_model('reservations', 'Reservation')
            now = timezone.now()
            rows = [model.objects.create(
                user=user, resource=resource, starts_at=now + timedelta(days=1),
                ends_at=now + timedelta(days=1, hours=1), status=status,
            ) for status in ('DRAFT', 'CONFIRMED', 'REJECTED')]
            executor = MigrationExecutor(connection)
            executor.migrate([current])
            new_model = executor.loader.project_state([current]).apps.get_model('reservations', 'Reservation')
            self.assertEqual([new_model.objects.get(pk=row.pk).status for row in rows],
                             ['CANCELLED', 'CONFIRMED', 'REJECTED'])
            self.assertEqual(new_model.objects.count(), 3)
        finally:
            executor = MigrationExecutor(connection)
            executor.migrate(executor.loader.graph.leaf_nodes())


class CancellationNoticeMigrationTests(TransactionTestCase):
    def test_existing_terms_survive_migration_and_new_creation_uses_resource_notice(self):
        previous = ('reservations', '0003_remove_draft_lifecycle')
        current = ('reservations', '0004_cancellation_notice')
        executor = MigrationExecutor(connection)
        executor.migrate([previous])
        try:
            apps = executor.loader.project_state([previous]).apps
            user = apps.get_model('auth', 'User').objects.create(username='notice-legacy')
            sport = apps.get_model('reservations', 'Sport').objects.create(name='Legacy notice sport')
            resource = apps.get_model('reservations', 'Resource').objects.create(
                name='Legacy notice court', sport=sport, location='Ostrava',
                opens_at='08:00', closes_at='22:00',
            )
            start = timezone.localtime(timezone.now() + timedelta(days=1)).replace(
                hour=10, minute=0, second=0, microsecond=0)
            model = apps.get_model('reservations', 'Reservation')
            rows = [model.objects.create(
                user=user, resource=resource, starts_at=start, ends_at=start + timedelta(hours=1),
                status=status, approval_requested_at=timezone.now() if status == 'PENDING_APPROVAL' else None,
            ) for status in ('PENDING_APPROVAL', 'CONFIRMED', 'REJECTED', 'EXPIRED', 'CANCELLED')]
            fields = ('id', 'user_id', 'resource_id', 'starts_at', 'ends_at', 'status',
                      'created_at', 'approval_requested_at')
            before = list(model.objects.order_by('pk').values_list(*fields))
            executor = MigrationExecutor(connection)
            executor.migrate([current])
            apps = executor.loader.project_state([current]).apps
            new_model = apps.get_model('reservations', 'Reservation')
            self.assertEqual(list(new_model.objects.order_by('pk').values_list(*fields)), before)
            self.assertEqual(list(new_model.objects.values_list('cancellation_notice_minutes', flat=True)),
                             [0] * len(rows))
            self.assertEqual(apps.get_model('reservations', 'Resource').objects.get(
                pk=resource.pk).cancellation_notice_minutes, 120)
            from .domain import TimeInterval, User
            from .wiring import build_service
            reservation = build_service().create(
                resource.pk, TimeInterval(start + timedelta(hours=2), start + timedelta(hours=3)),
                User(user.pk, False),
            )
            self.assertEqual(new_model.objects.get(pk=reservation.id).cancellation_notice_minutes, 120)
            print('C09 migration: all five legacy states and fields preserved; notices 0, new creation 120.')
        finally:
            executor = MigrationExecutor(connection)
            executor.migrate(executor.loader.graph.leaf_nodes())
