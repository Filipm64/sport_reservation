"""Use SPORT_BOOKING_TEST_DB with a disposable SQLite file for real connections."""
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor
from datetime import time, timedelta
from threading import Barrier

from django.contrib.auth import get_user_model
from django.db import connection, connections
from django.test import RequestFactory, TransactionTestCase
from django.utils import timezone

from . import views
from .models import Reservation, Resource, Sport


class ReservationConcurrencyTests(TransactionTestCase):
    def setUp(self):
        if connection.vendor != 'sqlite' or connection.is_in_memory_db():
            self.skipTest('Run with SPORT_BOOKING_TEST_DB=/tmp/sport-booking-tests.sqlite3')
        self.user = get_user_model().objects.create_user(username='customer')
        self.staff = get_user_model().objects.create_user(username='staff', is_staff=True)
        sport = Sport.objects.create(name='Tennis')
        self.resource = Resource.objects.create(
            name='Court', sport=sport, location='Ostrava',
            opens_at=time(8), closes_at=time(22),
        )
        self.start = timezone.now() + timedelta(days=1)

    def reservation(self, pending=False):
        return Reservation.objects.create(
            user=self.user, resource=self.resource, starts_at=self.start,
            ends_at=self.start + timedelta(hours=1),
            status='PENDING_APPROVAL' if pending else 'DRAFT',
            approval_requested_at=timezone.now() if pending else None,
        )

    def race(self, *operations):
        barrier = Barrier(len(operations))

        def run(operation):
            view, reservation_id, user = operation
            try:
                request = RequestFactory().post(
                    '/', json.dumps({'decision': 'approve'}),
                    content_type='application/json',
                )
                request.user = get_user_model().objects.get(pk=user.pk)
                barrier.wait(timeout=10)
                return view(request, reservation_id).status_code
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=len(operations)) as pool:
            return list(pool.map(run, operations))

    def test_conflicting_confirmations_commit_only_one_allocation(self):
        first, second = self.reservation(), self.reservation()
        results = self.race(
            (views.confirm_reservation, first.pk, self.user),
            (views.confirm_reservation, second.pk, self.user),
        )
        self.assertCountEqual(results, [200, 409])
        self.assertEqual(Reservation.objects.filter(status='CONFIRMED').count(), 1)
        self.assertEqual(Reservation.objects.filter(status='DRAFT').count(), 1)

    def test_conflicting_approvals_commit_only_one_allocation(self):
        first, second = self.reservation(pending=True), self.reservation(pending=True)
        results = self.race(
            (views.approve_reservation, first.pk, self.staff),
            (views.approve_reservation, second.pk, self.staff),
        )
        self.assertCountEqual(results, [200, 409])
        self.assertEqual(Reservation.objects.filter(status='CONFIRMED').count(), 1)
        self.assertEqual(Reservation.objects.filter(status='PENDING_APPROVAL').count(), 1)

    def test_confirm_racing_cancel_finishes_cancelled(self):
        reservation = self.reservation()
        results = self.race(
            (views.confirm_reservation, reservation.pk, self.user),
            (views.cancel_reservation, reservation.pk, self.user),
        )
        self.assertEqual(results[1], 200)
        self.assertIn(results[0], (200, 409))
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, 'CANCELLED')

    def test_confirm_racing_approval_commits_only_one_allocation(self):
        draft, pending = self.reservation(), self.reservation(pending=True)
        results = self.race(
            (views.confirm_reservation, draft.pk, self.user),
            (views.approve_reservation, pending.pk, self.staff),
        )
        self.assertCountEqual(results, [200, 409])
        self.assertEqual(Reservation.objects.filter(status='CONFIRMED').count(), 1)

    def test_approve_racing_cancel_finishes_cancelled(self):
        reservation = self.reservation(pending=True)
        results = self.race(
            (views.approve_reservation, reservation.pk, self.staff),
            (views.cancel_reservation, reservation.pk, self.user),
        )
        self.assertEqual(results[1], 200)
        self.assertIn(results[0], (200, 409))
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, 'CANCELLED')


    def test_expiration_process_racing_approval_uses_shared_database(self):
        reservation = self.reservation(pending=True)
        Reservation.objects.filter(pk=reservation.pk).update(
            approval_requested_at=timezone.now() - timedelta(hours=24),
        )
        script = """
import os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'sport_booking.settings'
from django.conf import settings
settings.DATABASES['default']['NAME'] = sys.argv[1]
import django
django.setup()
from django.core.management import call_command
print('READY', flush=True)
sys.stdin.readline()
call_command('expire_reservations')
"""
        with subprocess.Popen(
            [sys.executable, '-c', script, str(connection.settings_dict['NAME'])],
            cwd=Path(__file__).resolve().parent.parent,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True,
        ) as process:
            self.assertEqual(process.stdout.readline().strip(), 'READY')

            def expire_from_other_process(request, reservation_id):
                output, errors = process.communicate('start\n', timeout=20)
                self.assertEqual(process.returncode, 0, errors)
                self.assertIn('Expired', output)
                return SimpleNamespace(status_code=200)

            results = self.race(
                (views.approve_reservation, reservation.pk, self.staff),
                (expire_from_other_process, reservation.pk, self.staff),
            )
        self.assertEqual(results, [409, 200])
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, 'EXPIRED')
