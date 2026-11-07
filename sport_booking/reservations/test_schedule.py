from datetime import UTC, date, datetime, time, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from .domain import ReservationError, Resource as DomainResource, TimeInterval
from .models import Reservation, Resource, Sport
from .rules import TimeRules
from .wiring import build_portal_queries


class HourBlockRuleTests(SimpleTestCase):
    def test_daylight_saving_days_have_real_hour_blocks(self):
        rules = TimeRules()
        resource = DomainResource(1, True, False, time.min, time(23, 59))
        for day, expected in ((date(2026, 3, 29), 23), (date(2026, 10, 25), 25)):
            with self.subTest(day=day):
                blocks = rules.hourly_blocks(day, datetime.combine(day, datetime.min.time(), UTC), resource, [])
                self.assertEqual(len(blocks), expected)
                self.assertEqual(len({block.key for block in blocks}), expected)
                for first, second in zip(blocks, blocks[1:]):
                    self.assertEqual(first.end, second.start)
                self.assertTrue(all(block.end - block.start == timedelta(hours=1) for block in blocks))
                self.assertTrue(all('UTC' in block.label for block in blocks))

    def test_two_hour_limit_uses_elapsed_time_across_dst(self):
        zone = ZoneInfo('Europe/Prague')
        rules = TimeRules()
        # 01:00–03:00 at the fall-back transition is actually three hours.
        start = datetime(2026, 10, 25, 1, tzinfo=zone)
        with self.assertRaises(ReservationError):
            rules.validate_interval(TimeInterval(start, datetime(2026, 10, 25, 3, tzinfo=zone)),
                                    start - timedelta(days=1))
        # 01:00–04:00 at the spring transition is only two elapsed hours.
        start = datetime(2026, 3, 29, 1, tzinfo=zone)
        rules.validate_interval(TimeInterval(start, datetime(2026, 3, 29, 4, tzinfo=zone)),
                                start - timedelta(days=1))

    def test_unavailable_resource_disables_all_blocks(self):
        day = date(2026, 11, 8)
        blocks = TimeRules().hourly_blocks(day, datetime(2026, 11, 7, tzinfo=UTC),
                                         DomainResource(1, False, False, time.min, time(23, 59)), [])
        self.assertEqual(len(blocks), 24)
        self.assertTrue(all(not block.available for block in blocks))

    def test_week_table_represents_dst_gap_and_repeated_hour(self):
        rules = TimeRules()
        resource = DomainResource(1, True, False, time(1), time(4))
        spring = rules.weekly_blocks(date(2026, 3, 29), datetime(2026, 3, 22, tzinfo=UTC), resource, [])
        row = next(row for row in spring['rows'] if row['label'] == '02:00')
        self.assertIsNone(row['cells'][6])
        autumn = rules.weekly_blocks(date(2026, 10, 25), datetime(2026, 10, 18, tzinfo=UTC), resource, [])
        repeated = next(row for row in autumn['rows'] if row['label'] == '02:00 ↺')
        self.assertTrue(all(cell is None for cell in repeated['cells'][:6]))
        self.assertIsNotNone(repeated['cells'][6])
        self.assertEqual(repeated['cells'][6].end - repeated['cells'][6].start, timedelta(hours=1))


class ScheduleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username='slot-customer')
        sport = Sport.objects.create(name='Tenis')
        cls.resource = Resource.objects.create(
            name='Hodinový kurt', sport=sport, location='Ostrava',
            opens_at='08:00', closes_at='22:00',
        )

    def setUp(self):
        self.client.force_login(self.user)
        self.now = timezone.now()
        self.day = timezone.localdate(self.now) + timedelta(days=1)

    def post_blocks(self, keys, **extra):
        return self.client.post('/', {
            'resource_id': self.resource.pk, 'schedule_date': self.day.isoformat(),
            'selection_mode': 'slots', 'selected_blocks': [f'{self.day.isoformat()}:{key}' for key in keys], 'action': 'create', **extra,
        })

    def blocks(self):
        return build_portal_queries().hourly_schedule(self.resource.pk, self.day, self.now)

    def test_grid_renders_hour_blocks_and_manual_option(self):
        response = self.client.get('/', {'resource_id': self.resource.pk, 'schedule_date': self.day})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['schedule_week']['days']), 7)
        self.assertEqual(len(response.context['schedule_week']['rows']), 14)
        for text in ('Hodinový rozvrh', 'Zadat přesný čas', '12:00–13:00', 'schedule.js'):
            self.assertContains(response, text)
        self.assertFalse(Reservation.objects.exists())

    def test_one_or_two_blocks_create_exact_one_or_two_hour_reservation(self):
        for keys in (['10'], ['12', '13']):
            with self.subTest(keys=keys):
                response = self.post_blocks(keys)
                self.assertRedirects(response, f'/?resource_id={self.resource.pk}&schedule_date={self.day.isoformat()}#booking-title')
                row = Reservation.objects.latest('pk')
                expected = [b for b in self.blocks() if b.key in [f'{self.day.isoformat()}:{key}' for key in keys]]
                self.assertEqual(row.starts_at, expected[0].start)
                self.assertEqual(row.ends_at, expected[-1].end)
                self.assertEqual(row.ends_at - row.starts_at, timedelta(hours=len(keys)))
                self.assertEqual(row.status, 'CONFIRMED')

    def test_three_nonadjacent_duplicate_and_unknown_blocks_are_rejected(self):
        for keys in ([], ['10', '11', '12'], ['10', '12'], ['10', '10'], ['999'], ['-1']):
            with self.subTest(keys=keys):
                response = self.post_blocks(keys)
                self.assertEqual(response.status_code, 200)
                self.assertIn('selected_blocks', response.context['form'].errors)
                self.assertFalse(Reservation.objects.exists())

    def test_confirmed_partial_overlap_blocks_whole_hour_and_edges_remain_free(self):
        blocks = self.blocks()
        Reservation.objects.create(
            user=self.user, resource=self.resource,
            starts_at=blocks[10].start + timedelta(minutes=30),
            ends_at=blocks[10].end, status='CONFIRMED',
        )
        result = self.blocks()
        self.assertFalse(result[10].available)
        self.assertEqual(result[10].reason, 'Obsazeno')
        self.assertTrue(result[9].available)
        self.assertTrue(result[11].available)
        response = self.post_blocks(['10'])
        self.assertIn('selected_blocks', response.context['form'].errors)
        self.assertEqual(Reservation.objects.count(), 1)

    def test_pending_other_resource_and_cancelled_do_not_block(self):
        start = self.blocks()[10].start
        other = Resource.objects.create(name='Jiný kurt', sport=self.resource.sport,
                                        location='Praha', opens_at='08:00', closes_at='22:00')
        for resource, status in ((self.resource, 'PENDING_APPROVAL'), (self.resource, 'CANCELLED'),
                                 (other, 'CONFIRMED')):
            Reservation.objects.create(user=self.user, resource=resource, starts_at=start,
                                       ends_at=start + timedelta(hours=1), status=status,
                                       approval_requested_at=self.now)
        self.assertTrue(self.blocks()[10].available)

    def test_approval_required_resource_creates_pending_from_blocks(self):
        self.resource.requires_approval = True
        self.resource.save()
        self.assertRedirects(self.post_blocks(['10', '11']), f'/?resource_id={self.resource.pk}&schedule_date={self.day.isoformat()}#booking-title')
        row = Reservation.objects.get()
        self.assertEqual(row.status, 'PENDING_APPROVAL')
        self.assertIsNotNone(row.approval_requested_at)

    def test_stale_schedule_does_not_bypass_atomic_conflict_check(self):
        stale = build_portal_queries().weekly_schedule(self.resource.pk, self.day, self.now)
        daily = self.blocks()
        Reservation.objects.create(user=self.user, resource=self.resource,
                                   starts_at=daily[10].start, ends_at=daily[10].end, status='CONFIRMED')
        with patch('reservations.portal.PortalQueries.weekly_schedule', return_value=stale):
            response = self.post_blocks(['10'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Reservation.objects.count(), 1)
        self.assertContains(response, 'Tuto změnu nelze provést')

    def test_invalid_resource_and_day_do_not_create_reservation(self):
        for extra in ({'resource_id': '99999'}, {'schedule_date': 'bad-date'},
                      {'schedule_date': (self.day + timedelta(days=31)).isoformat()}):
            with self.subTest(extra=extra):
                response = self.post_blocks(['10'], **extra)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context['form'].errors)
                self.assertFalse(Reservation.objects.exists())

    def test_past_and_beyond_thirty_days_are_disabled(self):
        now = self.blocks()[10].start + timedelta(minutes=1)
        blocks = build_portal_queries().hourly_schedule(self.resource.pk, self.day, now)
        self.assertFalse(blocks[10].available)
        self.assertTrue(blocks[11].available)
        future = build_portal_queries().hourly_schedule(self.resource.pk, self.day + timedelta(days=31), now)
        self.assertTrue(all(not block.available for block in future))

    def test_availability_from_blocks_is_read_only(self):
        self.assertEqual(self.post_blocks(['10'], action='availability').status_code, 200)
        self.assertFalse(Reservation.objects.exists())

    def test_manual_input_keeps_two_hour_server_limit(self):
        start = datetime.combine(self.day, datetime.min.time(), ZoneInfo('Europe/Prague')).replace(hour=10)
        response = self.client.post('/', {
            'resource_id': self.resource.pk, 'selection_mode': 'manual', 'action': 'create',
            'starts_at': start.strftime('%Y-%m-%dT%H:%M'),
            'ends_at': (start + timedelta(hours=3)).strftime('%Y-%m-%dT%H:%M'),
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Reservation.objects.exists())
        self.assertContains(response, 'nesmí přesáhnout 2 hodiny')

    def test_guest_cannot_submit_grid_booking(self):
        self.client.logout()
        self.assertRedirects(self.post_blocks(['10']), '/prihlaseni/')
        self.assertFalse(Reservation.objects.exists())

    def test_slot_interval_is_derived_on_server_not_client_values(self):
        response = self.post_blocks(['10'], starts_at='not-a-time', ends_at='2099-01-01T00:00')
        self.assertRedirects(response, f'/?resource_id={self.resource.pk}&schedule_date={self.day.isoformat()}#booking-title')
        row = Reservation.objects.get()
        block = self.blocks()[10]
        self.assertEqual(row.starts_at, block.start)
        self.assertEqual(row.ends_at - row.starts_at, timedelta(hours=1))
