"""C08 before-change cases; expectations are specified in the baseline document."""
import json
import sqlite3
from datetime import UTC, datetime, time, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TransactionTestCase

from .models import Resource, Sport


class CancellationBaselineTests(TransactionTestCase):
    start = datetime(2026, 11, 10, 10, tzinfo=UTC)
    end = start + timedelta(hours=1)
    created = datetime(2026, 11, 9, 9, tzinfo=UTC)

    def setUp(self):
        self.owner = get_user_model().objects.create_user(username='c08-owner')
        sport = Sport.objects.create(name='C08 Tennis')
        self.resource = Resource.objects.create(
            sport=sport, name='C08 Court', location='Ostrava',
            opens_at=time(8), closes_at=time(22), requires_approval=False,
        )
        self.client.force_login(self.owner)

    def persisted(self, reservation_id, expected_status):
        self.assertTrue(connection.get_autocommit())
        # Separate connection sees committed data, rather than an ORM object cache.
        with sqlite3.connect(str(connection.settings_dict['NAME']), uri=True) as reader:
            rows = reader.execute(
                'SELECT id, user_id, resource_id, starts_at, ends_at, status '
                'FROM reservations_reservation WHERE id = ?', (reservation_id,),
            ).fetchall()
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row[:3], (reservation_id, self.owner.pk, self.resource.pk))
        self.assertEqual(datetime.fromisoformat(row[3]).replace(tzinfo=UTC), self.start)
        self.assertEqual(datetime.fromisoformat(row[4]).replace(tzinfo=UTC), self.end)
        self.assertEqual(row[5], expected_status)
        print(f'Independent committed SQL read: {rows!r}', flush=True)

    def run_case(self, case_id, now, expected_http, expected_status):
        print(f'\n{case_id}: create_at={self.created.isoformat()}, cancel_at={now.isoformat()}', flush=True)
        body = {'resource_id': self.resource.pk,
                'starts_at': self.start.isoformat(), 'ends_at': self.end.isoformat()}
        with patch('reservations.rules.TimeRules.now', return_value=self.created):
            response = self.client.post('/api/reservations/', json.dumps(body),
                                        content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['status'], 'CONFIRMED')
        reservation_id = response.json()['id']
        print(f'Step 1: create HTTP {response.status_code}: {response.json()}', flush=True)
        self.persisted(reservation_id, 'CONFIRMED')
        with patch('reservations.rules.TimeRules.now', return_value=now):
            response = self.client.post(f'/api/reservations/{reservation_id}/cancel/')
        print(f'Step 3: cancel HTTP {response.status_code}: {response.json()}', flush=True)
        self.assertEqual(response.status_code, expected_http)
        if expected_http == 200:
            self.assertEqual(response.json()['status'], expected_status)
        self.persisted(reservation_id, expected_status)
        print(f'{case_id}: PASS', flush=True)

    def test_cancel_one_second_before_start(self):
        self.run_case('TC-C08-01', self.start - timedelta(seconds=1), 200, 'CANCELLED')

    def test_refuse_cancel_at_start(self):
        self.run_case('TC-C08-02', self.start, 409, 'CONFIRMED')
