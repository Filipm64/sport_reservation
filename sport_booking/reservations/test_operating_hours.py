import json
from datetime import UTC, datetime, time, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.utils import timezone

from .models import Reservation, Resource, Sport
from .wiring import build_portal_queries


class OperatingHoursTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = get_user_model().objects.create_user(username='customer')
        cls.staff = get_user_model().objects.create_user(username='manager', is_staff=True)
        sport = Sport.objects.create(name='Tenis')
        cls.resource = Resource.objects.create(
            name='Kurt s provozní dobou', sport=sport, location='Ostrava',
            opens_at='08:00', closes_at='22:00',
        )

    def setUp(self):
        self.client.force_login(self.customer)
        self.day = timezone.localdate() + timedelta(days=1)

    def interval(self, start_hour, end_hour, day=None):
        day = day or self.day
        start = datetime.combine(day, time(start_hour), ZoneInfo('Europe/Prague'))
        end = datetime.combine(day, time(end_hour), ZoneInfo('Europe/Prague'))
        return {'resource_id': self.resource.pk, 'starts_at': start.isoformat(), 'ends_at': end.isoformat()}

    def create(self, start_hour=10, end_hour=11):
        return self.client.post('/api/reservations/', json.dumps(self.interval(start_hour, end_hour)),
                                content_type='application/json')

    def hours_url(self):
        return f'/sportoviste/{self.resource.pk}/provozni-doba/'

    def test_api_creation_rejects_outside_hours_for_both_resource_types(self):
        for approval in (False, True):
            self.resource.requires_approval = approval
            self.resource.save()
            for start, end in ((7, 8), (7, 9), (21, 23), (22, 23)):
                with self.subTest(approval=approval, start=start, end=end):
                    response = self.create(start, end)
                    self.assertEqual(response.status_code, 409)
                    self.assertIn('operating hours', response.json()['error'])
                    self.assertFalse(Reservation.objects.exists())

    def test_exact_opening_and_closing_boundaries_are_allowed(self):
        for start, end in ((8, 9), (20, 22)):
            self.assertEqual(self.create(start, end).status_code, 201)
        self.assertEqual(Reservation.objects.count(), 2)

    def test_availability_is_unavailable_outside_operating_hours(self):
        for start, end, expected in ((7, 8, 'UNAVAILABLE'), (21, 23, 'UNAVAILABLE'),
                                     (8, 9, 'AVAILABLE'), (21, 22, 'AVAILABLE')):
            with self.subTest(start=start, end=end):
                response = self.client.get('/api/availability/', self.interval(start, end))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()['availability'], expected)
        self.assertFalse(Reservation.objects.exists())

    def test_manual_web_creation_cannot_bypass_operating_hours(self):
        data = self.interval(7, 8)
        data['starts_at'] = data['starts_at'][:16]
        data['ends_at'] = data['ends_at'][:16]
        response = self.client.post('/', {**data, 'selection_mode': 'manual', 'action': 'create'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Celá rezervace musí být v provozní době')
        self.assertFalse(Reservation.objects.exists())

    def test_week_grid_excludes_closed_rows_and_disables_partial_hours(self):
        self.resource.opens_at = time(8, 30)
        self.resource.closes_at = time(20, 30)
        self.resource.save()
        portal = build_portal_queries()
        blocks = portal.hourly_schedule(self.resource.pk, self.day, timezone.now())
        self.assertFalse(blocks[8].available)
        self.assertEqual(blocks[8].reason, 'Zavřeno')
        self.assertTrue(blocks[9].available)
        self.assertFalse(blocks[20].available)
        response = self.client.get('/', {'resource_id': self.resource.pk, 'schedule_date': self.day})
        self.assertEqual(len(response.context['schedule_week']['days']), 7)
        labels = [row['label'] for row in response.context['schedule_week']['rows']]
        self.assertEqual(labels, [f'{hour:02}:00' for hour in range(9, 20)])
        self.assertContains(response, '08:30–20:30')
        self.assertContains(response, 'class="week-table"')

    def test_week_navigation_stays_inside_booking_horizon(self):
        today = timezone.localdate()
        response = self.client.get('/')
        self.assertNotIn('previous', response.context['week_links'])
        self.assertIn('next', response.context['week_links'])
        response = self.client.get('/', {'schedule_date': today + timedelta(days=30), 'resource_id': self.resource.pk})
        self.assertNotIn('next', response.context['week_links'])
        self.assertIn('previous', response.context['week_links'])

    def test_week_selection_is_limited_to_one_day(self):
        now = datetime(2026, 11, 9, 8, tzinfo=UTC)
        day = timezone.localdate(now)
        with patch('reservations.web_views.timezone.now', return_value=now):
            response = self.client.post('/', {
                'resource_id': self.resource.pk, 'schedule_date': day.isoformat(),
                'selection_mode': 'slots', 'action': 'create',
                'selected_blocks': [f'{day}:10', f'{day + timedelta(days=1)}:10'],
            })
        self.assertEqual(response.status_code, 200)
        self.assertIn('selected_blocks', response.context['form'].errors)
        self.assertFalse(Reservation.objects.exists())

    def test_block_from_other_day_in_same_week_creates_correct_date(self):
        now = datetime(2026, 11, 9, 8, tzinfo=UTC)
        target = timezone.localdate(now) + timedelta(days=2)
        with patch('reservations.web_views.timezone.now', return_value=now):
            response = self.client.post('/', {
                'resource_id': self.resource.pk, 'schedule_date': timezone.localdate(now).isoformat(),
                'selection_mode': 'slots', 'action': 'create',
                'selected_blocks': [f'{target}:10', f'{target}:11'],
            })
        self.assertEqual(response.status_code, 302)
        row = Reservation.objects.get()
        self.assertEqual(timezone.localdate(row.starts_at), target)
        self.assertEqual(row.ends_at - row.starts_at, timedelta(hours=2))
        self.assertIn(f'schedule_date={target}', response.url)

    def test_staff_can_update_operating_hours_without_admin_model_permissions(self):
        self.client.force_login(self.staff)
        self.assertFalse(self.staff.has_perm('reservations.change_resource'))
        response = self.client.post(self.hours_url(), {'opens_at': '09:30', 'closes_at': '20:30'})
        self.assertRedirects(response, '/#staff-title')
        self.resource.refresh_from_db()
        self.assertEqual((self.resource.opens_at, self.resource.closes_at), (time(9, 30), time(20, 30)))
        self.assertContains(self.client.get('/'), 'Nastavit provozní dobu sportovišť')

    def test_customer_and_guest_cannot_update_operating_hours(self):
        self.assertEqual(self.client.post(self.hours_url(), {'opens_at': '00:00', 'closes_at': '23:59'}).status_code, 403)
        self.assertNotContains(self.client.get('/'), 'Nastavit provozní dobu sportovišť')
        self.client.logout()
        self.assertRedirects(self.client.post(self.hours_url(), {'opens_at': '00:00', 'closes_at': '23:59'}), '/prihlaseni/')
        self.resource.refresh_from_db()
        self.assertEqual(self.resource.opens_at, time(8))

    def test_invalid_operating_hours_do_not_change_configuration(self):
        self.client.force_login(self.staff)
        for opening, closing in (('22:00', '08:00'), ('08:00', '08:00'), ('bad', '22:00'), ('', '')):
            with self.subTest(opening=opening, closing=closing):
                response = self.client.post(self.hours_url(), {'opens_at': opening, 'closes_at': closing})
                self.assertRedirects(response, '/#staff-title')
                self.resource.refresh_from_db()
                self.assertEqual((self.resource.opens_at, self.resource.closes_at), (time(8), time(22)))
        self.resource.opens_at, self.resource.closes_at = time(22), time(8)
        with self.assertRaises(ValidationError):
            self.resource.full_clean()

    def test_operating_hours_update_requires_post_and_csrf(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(self.hours_url()).status_code, 405)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.staff)
        self.assertEqual(client.post(self.hours_url(), {'opens_at': '09:00', 'closes_at': '20:00'}).status_code, 403)
        client.get('/')
        response = client.post(self.hours_url(), {'opens_at': '09:00', 'closes_at': '20:00',
                                                 'csrfmiddlewaretoken': client.cookies['csrftoken'].value})
        self.assertEqual(response.status_code, 302)
        self.resource.refresh_from_db()
        self.assertEqual(self.resource.opens_at, time(9))

    def test_approval_rechecks_changed_operating_hours(self):
        self.resource.requires_approval = True
        self.resource.save()
        id = self.create().json()['id']
        self.client.force_login(self.staff)
        self.client.post(self.hours_url(), {'opens_at': '12:00', 'closes_at': '20:00'})
        response = self.client.post(f'/api/reservations/{id}/approve/', json.dumps({'decision': 'approve'}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 409)
        self.assertEqual(Reservation.objects.get(pk=id).status, 'PENDING_APPROVAL')

    def test_changing_operating_hours_does_not_cancel_existing_confirmations(self):
        id = self.create().json()['id']
        self.client.force_login(self.staff)
        self.client.post(self.hours_url(), {'opens_at': '12:00', 'closes_at': '20:00'})
        self.assertEqual(Reservation.objects.get(pk=id).status, 'CONFIRMED')

    def test_api_uses_local_operating_time_regardless_of_input_offset(self):
        data = self.interval(8, 9)
        for field in ('starts_at', 'ends_at'):
            data[field] = datetime.fromisoformat(data[field]).astimezone(UTC).isoformat()
        response = self.client.post('/api/reservations/', json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 201)

    def test_operating_hours_update_rolls_back_when_commit_fails(self):
        from django.db import DatabaseError
        from .persistence import DjangoDataStore
        self.client.force_login(self.staff)
        with patch.object(DjangoDataStore, 'commit', side_effect=DatabaseError('failure')):
            with self.assertRaises(DatabaseError):
                self.client.post(self.hours_url(), {'opens_at': '09:00', 'closes_at': '20:00'})
        self.resource.refresh_from_db()
        self.assertEqual((self.resource.opens_at, self.resource.closes_at), (time(8), time(22)))

    def test_partial_hour_manual_interval_can_fit_and_overnight_is_rejected(self):
        start = datetime.combine(self.day, time(8, 30), ZoneInfo('Europe/Prague'))
        self.resource.opens_at, self.resource.closes_at = time(8, 30), time(20, 30)
        self.resource.save()
        data = {'resource_id': self.resource.pk, 'starts_at': start.isoformat(),
                'ends_at': (start + timedelta(hours=1)).isoformat()}
        self.assertEqual(self.client.post('/api/reservations/', json.dumps(data), content_type='application/json').status_code, 201)
        start = start.replace(hour=23)
        data.update(starts_at=start.isoformat(), ends_at=(start + timedelta(hours=1)).isoformat())
        self.assertEqual(self.client.post('/api/reservations/', json.dumps(data), content_type='application/json').status_code, 409)
        self.assertEqual(Reservation.objects.count(), 1)
