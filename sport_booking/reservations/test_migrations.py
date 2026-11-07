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
            MigrationExecutor(connection).migrate([current])
