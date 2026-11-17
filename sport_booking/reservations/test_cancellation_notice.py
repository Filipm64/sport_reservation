"""C09 accepted cancellation contract, using real HTTP/service/SQLite writes."""
import json
import sqlite3
from datetime import UTC, datetime, time, timedelta
from types import SimpleNamespace
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db import DatabaseError, connection
from django.test import Client, SimpleTestCase, TransactionTestCase

from .models import Reservation, Resource, Sport
from .domain import ReservationError
from .rules import TimeRules
from .persistence import DjangoDataStore


class CancellationNoticeTests(TransactionTestCase):
    start = datetime(2026, 11, 20, 10, tzinfo=UTC)
    created = start - timedelta(days=1)

    def setUp(self):
        self.owner = get_user_model().objects.create_user(username='notice-owner')
        self.staff = get_user_model().objects.create_user(username='notice-staff', is_staff=True)
        self.staff.user_permissions.add(Permission.objects.get(codename='change_resource'))
        self.resource = Resource.objects.create(
            name='Notice court', sport=Sport.objects.create(name='Notice tennis'),
            location='Ostrava', opens_at=time(8), closes_at=time(22),
        )
        self.client.force_login(self.owner)

    def create(self, *, start=None, extra=None, web=False):
        start = start or self.start
        body = {'resource_id': self.resource.pk, 'starts_at': start.isoformat(),
                'ends_at': (start + timedelta(hours=1)).isoformat(), **(extra or {})}
        with patch('reservations.rules.TimeRules.now', return_value=self.created):
            if web:
                local = start.astimezone(ZoneInfo('Europe/Prague'))
                body.update(starts_at=local.strftime('%Y-%m-%dT%H:%M'),
                            ends_at=(local + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M'),
                            action='create', selection_mode='manual')
                response = self.client.post('/', body)
                self.assertEqual(response.status_code, 302)
                return Reservation.objects.latest('pk').pk
            response = self.client.post('/api/reservations/', json.dumps(body),
                                        content_type='application/json')
        self.assertEqual(response.status_code, 201, response.content)
        return response.json()['id']

    def cancel(self, pk, now, web=False):
        with patch('reservations.rules.TimeRules.now', return_value=now):
            return self.client.post(f'/rezervace/{pk}/cancel/' if web
                                    else f'/api/reservations/{pk}/cancel/')

    def committed(self, pk, status, minutes, start=None):
        self.assertTrue(connection.get_autocommit())
        with sqlite3.connect(str(connection.settings_dict['NAME']), uri=True) as reader:
            row = reader.execute(
                'SELECT id, user_id, resource_id, starts_at, ends_at, status, '
                'cancellation_notice_minutes FROM reservations_reservation WHERE id = ?',
                (pk,),
            ).fetchone()
        self.assertEqual(row[:3], (pk, self.owner.pk, self.resource.pk))
        self.assertEqual(datetime.fromisoformat(row[3]).replace(tzinfo=UTC), start or self.start)
        self.assertEqual(datetime.fromisoformat(row[4]).replace(tzinfo=UTC),
                         (start or self.start) + timedelta(hours=1))
        self.assertEqual(row[5:], (status, minutes))
        print(f'C09 independent committed SQL: {row!r}', flush=True)

    def test_cancellation_exact_boundaries_for_multiple_notices(self):
        for minutes in (120, 240):
            for offset, http, status in ((-1, 200, 'CANCELLED'), (0, 200, 'CANCELLED'),
                                          (1, 409, 'CONFIRMED')):
                with self.subTest(minutes=minutes, offset=offset):
                    self.resource.cancellation_notice_minutes = minutes
                    self.resource.save()
                    pk = self.create()
                    self.committed(pk, 'CONFIRMED', minutes)
                    response = self.cancel(pk, self.start - timedelta(minutes=minutes)
                                           + timedelta(seconds=offset))
                    self.assertEqual(response.status_code, http)
                    if http == 409:
                        self.assertIn(str(minutes), response.json()['error'])
                    self.committed(pk, status, minutes)
                    Reservation.objects.all().delete()

    def test_zero_notice_and_started_reservations(self):
        for minutes in (0, 120):
            for offset in (-1, 0, 1):
                with self.subTest(minutes=minutes, offset=offset):
                    self.resource.cancellation_notice_minutes = minutes
                    self.resource.save()
                    pk = self.create()
                    allowed = minutes == 0 and offset == -1
                    self.assertEqual(self.cancel(pk, self.start + timedelta(seconds=offset)).status_code,
                                     200 if allowed else 409)
                    self.committed(pk, 'CANCELLED' if allowed else 'CONFIRMED', minutes)
                    Reservation.objects.all().delete()

    def test_pending_can_be_withdrawn_until_start_then_expires(self):
        self.resource.requires_approval = True
        for minutes in (0, 120, 240):
            self.resource.cancellation_notice_minutes = minutes
            self.resource.save()
            for offset in (-1, 0, 1):
                with self.subTest(minutes=minutes, offset=offset):
                    pk = self.create()
                    self.assertEqual(self.cancel(pk, self.start + timedelta(seconds=offset)).status_code,
                                     200 if offset < 0 else 409)
                    self.committed(pk, 'CANCELLED' if offset < 0 else 'EXPIRED', minutes)

    def admin_data(self, minutes):
        return {'name': self.resource.name, 'sport': self.resource.sport_id,
                'location': self.resource.location, 'opens_at': '08:00', 'closes_at': '22:00',
                'is_available': 'on', 'requires_approval': 'on' if self.resource.requires_approval else '',
                'cancellation_notice_minutes': minutes, '_save': 'Uložit'}

    def set_notice_in_admin(self, minutes):
        admin_client = Client()
        admin_client.force_login(self.staff)
        return admin_client.post(f'/admin/reservations/resource/{self.resource.pk}/change/',
                                 self.admin_data(minutes))

    def test_admin_change_affects_only_future_reservations(self):
        first = self.create()
        self.assertEqual(self.set_notice_in_admin(240).status_code, 302)
        self.resource.refresh_from_db()
        self.assertEqual(self.resource.cancellation_notice_minutes, 240)
        second_start = self.start + timedelta(hours=2)
        second = self.create(start=second_start)
        self.committed(first, 'CONFIRMED', 120)
        self.committed(second, 'CONFIRMED', 240, start=second_start)
        self.assertEqual(self.cancel(first, self.start - timedelta(hours=2)).status_code, 200)
        self.assertEqual(self.cancel(second, second_start - timedelta(hours=4)
                                     + timedelta(seconds=1)).status_code, 409)
        self.committed(second, 'CONFIRMED', 240, start=second_start)

    def test_approval_preserves_saved_notice_after_configuration_change(self):
        for minutes in (0, 120):
            with self.subTest(minutes=minutes):
                self.resource.requires_approval = True
                self.resource.cancellation_notice_minutes = minutes
                self.resource.save()
                pk = self.create()
                self.assertEqual(self.set_notice_in_admin(240).status_code, 302)
                self.client.force_login(self.staff)
                with patch('reservations.rules.TimeRules.now', return_value=self.start - timedelta(hours=1)):
                    response = self.client.post(f'/api/reservations/{pk}/approve/',
                                                json.dumps({'decision': 'approve'}),
                                                content_type='application/json')
                self.assertEqual(response.status_code, 200)
                self.committed(pk, 'CONFIRMED', minutes)
                self.client.force_login(self.owner)
                self.assertEqual(self.cancel(pk, self.start - timedelta(seconds=1)).status_code,
                                 200 if minutes == 0 else 409)
                Reservation.objects.all().delete()

    def test_invalid_or_unauthorized_setting_does_not_change_resource(self):
        for value in ('-1', '1.5', 'abc', '', str(2**63)):
            with self.subTest(value=value):
                response = self.set_notice_in_admin(value)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context['adminform'].form.errors)
                self.resource.refresh_from_db()
                self.assertEqual(self.resource.cancellation_notice_minutes, 120)
        for user in (self.owner, get_user_model().objects.create_user(username='staff-no-perm', is_staff=True)):
            self.client.force_login(user)
            response = self.client.post(f'/admin/reservations/resource/{self.resource.pk}/change/',
                                        self.admin_data(0))
            self.assertIn(response.status_code, (302, 403))
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.staff)
        self.assertEqual(csrf_client.post(f'/admin/reservations/resource/{self.resource.pk}/change/',
                                          self.admin_data(0)).status_code, 403)
        self.resource.refresh_from_db()
        self.assertEqual(self.resource.cancellation_notice_minutes, 120)

    def test_customer_cannot_choose_notice_via_api_or_web(self):
        for web in (False, True):
            with self.subTest(web=web):
                pk = self.create(extra={'cancellation_notice_minutes': 0}, web=web)
                self.committed(pk, 'CONFIRMED', 120)
                Reservation.objects.all().delete()

    def test_stale_web_page_cannot_bypass_deadline(self):
        pk = self.create()
        with patch('reservations.web_views.timezone.now', return_value=self.start - timedelta(hours=2)):
            page = self.client.get('/')
        self.assertContains(page, f'/rezervace/{pk}/cancel/')
        self.assertEqual(self.cancel(pk, self.start - timedelta(hours=2) + timedelta(seconds=1),
                                     web=True).status_code, 302)
        self.committed(pk, 'CONFIRMED', 120)
        with patch('reservations.web_views.timezone.now', return_value=self.start - timedelta(hours=1)):
            page = self.client.get('/')
        self.assertNotContains(page, f'/rezervace/{pk}/cancel/')
        self.assertContains(page, 'Storno lhůta této rezervace již uplynula.')
        self.assertContains(page, '120 minut před začátkem')

    def test_web_notice_and_read_only_listing_use_saved_value(self):
        pk = self.create()
        self.assertEqual(self.set_notice_in_admin(240).status_code, 302)
        with patch('reservations.web_views.timezone.now', return_value=self.created):
            page = self.client.get('/', {'resource_id': self.resource.pk})
        self.assertContains(page, 'nejpozději 240 minut před začátkem')
        self.assertContains(page, '120 minut před začátkem.')
        self.assertContains(page, '20. 11. 2026 09:00:00 CET')
        self.committed(pk, 'CONFIRMED', 120)

    def test_late_cancellation_keeps_allocation_and_rejected_competitors(self):
        self.resource.requires_approval = True
        self.resource.save()
        pending = self.create()
        self.resource.requires_approval = False
        self.resource.save()
        confirmed = self.create()
        self.assertEqual(Reservation.objects.get(pk=pending).status, 'REJECTED')
        self.assertEqual(self.cancel(confirmed, self.start - timedelta(hours=1)).status_code, 409)
        self.committed(confirmed, 'CONFIRMED', 120)
        with patch('reservations.rules.TimeRules.now', return_value=self.created):
            body = {'resource_id': self.resource.pk, 'starts_at': self.start.isoformat(),
                    'ends_at': (self.start + timedelta(hours=1)).isoformat()}
            self.assertEqual(self.client.post('/api/reservations/', json.dumps(body),
                                              content_type='application/json').status_code, 409)
        self.assertEqual(self.cancel(confirmed, self.start - timedelta(hours=3)).status_code, 200)
        replacement = self.create()
        self.committed(replacement, 'CONFIRMED', 120)
        self.committed(pending, 'REJECTED', 120)

    def test_saved_notice_is_read_only_in_reservation_admin(self):
        pk = self.create()
        self.staff.user_permissions.add(Permission.objects.get(codename='change_reservation'))
        self.client.force_login(self.staff)
        response = self.client.post(f'/admin/reservations/reservation/{pk}/change/',
                                    {'cancellation_notice_minutes': 0, '_save': 'Uložit'})
        self.assertEqual(response.status_code, 302)
        self.committed(pk, 'CONFIRMED', 120)

    def test_both_serial_orders_of_approval_and_cancellation_after_deadline(self):
        self.resource.requires_approval = True
        self.resource.save()
        for first_action in ('approve', 'cancel'):
            with self.subTest(first_action=first_action):
                pk = self.create()
                for action in (first_action, 'cancel' if first_action == 'approve' else 'approve'):
                    self.client.force_login(self.staff if action == 'approve' else self.owner)
                    with patch('reservations.rules.TimeRules.now',
                               return_value=self.start - timedelta(hours=1)):
                        response = self.client.post(f'/api/reservations/{pk}/{action}/',
                                                    json.dumps({'decision': 'approve'}),
                                                    content_type='application/json')
                    self.assertEqual(response.status_code, 200 if action == first_action else 409)
                self.committed(pk, 'CONFIRMED' if first_action == 'approve' else 'CANCELLED', 120)
                Reservation.objects.all().delete()
                self.client.force_login(self.owner)

    def test_cancellation_failure_rolls_back_status_and_saved_notice(self):
        pk = self.create()
        for method in ('save', 'commit'):
            with self.subTest(method=method):
                with patch.object(DjangoDataStore, method, side_effect=DatabaseError('write failure')):
                    with self.assertRaises(DatabaseError):
                        self.cancel(pk, self.created)
                self.committed(pk, 'CONFIRMED', 120)

    def test_ownership_authentication_and_repeat_preserve_saved_terms(self):
        pk = self.create()
        self.client.logout()
        self.assertEqual(self.cancel(pk, self.created).status_code, 401)
        self.client.force_login(self.staff)
        self.assertEqual(self.cancel(pk, self.created).status_code, 404)
        self.committed(pk, 'CONFIRMED', 120)
        self.client.force_login(self.owner)
        self.assertEqual(self.cancel(pk, self.created).status_code, 200)
        self.assertEqual(self.cancel(pk, self.created).status_code, 409)
        self.committed(pk, 'CANCELLED', 120)

    def test_dst_deadline_is_displayed_in_correct_local_offset(self):
        zone = ZoneInfo('Europe/Prague')
        for start, expected in ((datetime(2027, 3, 28, 4, tzinfo=zone), '28. 3. 2027 01:00:00 CET'),
                                (datetime(2027, 10, 31, 3, tzinfo=zone), '31. 10. 2027 02:00:00 CEST')):
            with self.subTest(start=start):
                Reservation.objects.create(
                    user=self.owner, resource=self.resource, starts_at=start,
                    ends_at=start.astimezone(UTC) + timedelta(hours=1),
                    status='CONFIRMED', cancellation_notice_minutes=120,
                )
                with patch('reservations.web_views.timezone.now',
                           return_value=start.astimezone(UTC) - timedelta(days=1)):
                    # The simulated date is months ahead; create the session at that date too.
                    self.client.force_login(self.owner)
                    page = self.client.get('/')
                self.assertContains(page, expected)
                Reservation.objects.all().delete()


class CancellationClockTests(SimpleTestCase):
    def test_dst_uses_elapsed_utc_minutes_and_shared_display_rule(self):
        zone = ZoneInfo('Europe/Prague')
        rules = TimeRules()
        for start, deadline in ((datetime(2027, 3, 28, 4, tzinfo=zone),
                                 datetime(2027, 3, 28, 0, tzinfo=UTC)),
                                (datetime(2027, 10, 31, 3, tzinfo=zone),
                                 datetime(2027, 10, 31, 0, tzinfo=UTC))):
            with self.subTest(start=start):
                self.assertEqual(rules.cancellation_deadline(start, 120), deadline)
                reservation = SimpleNamespace(interval=SimpleNamespace(start=start),
                                              status='CONFIRMED', cancellation_notice_minutes=120)
                listing = SimpleNamespace(starts_at=start, status='CONFIRMED',
                                          cancellation_notice_minutes=120)
                rules.validate_cancellation(reservation, deadline.astimezone(zone))
                self.assertTrue(rules.can_cancel(listing, deadline.astimezone(zone)))
                with self.assertRaisesMessage(ReservationError, '120 minutes'):
                    rules.validate_cancellation(reservation, deadline + timedelta(seconds=1))
                self.assertFalse(rules.can_cancel(listing, deadline + timedelta(seconds=1)))

    def test_large_valid_notice_does_not_overflow_deadline(self):
        rules = TimeRules()
        self.assertEqual(rules.cancellation_deadline(datetime(2026, 1, 1, tzinfo=UTC), 2**31 - 1),
                         datetime.min.replace(tzinfo=UTC))
