import json
from datetime import UTC, datetime, time, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from .domain import ReservationError, User
from .models import Reservation, Resource, Sport
from .wiring import build_service


class ReservationPersistenceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username='customer')
        cls.sport = Sport.objects.create(name='Tennis')
        cls.resource = Resource.objects.create(
            name='Court 1', sport=cls.sport, location='Ostrava',
            opens_at=time(8), closes_at=time(22),
        )

    def create_reservation(self, **overrides):
        starts_at = timezone.now() + timedelta(days=1)
        fields = dict(
            user=self.user, resource=self.resource, starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=1), status="CONFIRMED",
        )
        fields.update(overrides)
        return Reservation.objects.create(**fields)

    def test_create_and_reload_all_fields_and_relations(self):
        saved = self.create_reservation()
        loaded = Reservation.objects.get(pk=saved.pk)
        self.assertIsNot(saved, loaded)
        self.assertEqual(loaded.user, self.user)
        self.assertEqual(loaded.resource, self.resource)
        self.assertEqual(loaded.resource.sport, self.sport)
        self.assertEqual(loaded.resource.location, 'Ostrava')
        self.assertEqual(loaded.resource.opens_at, time(8))
        self.assertEqual(loaded.resource.closes_at, time(22))
        self.assertTrue(loaded.resource.is_available)
        self.assertEqual(loaded.starts_at, saved.starts_at)
        self.assertEqual(loaded.ends_at, saved.ends_at)
        self.assertEqual(loaded.status, Reservation.Status.CONFIRMED)
        self.assertIsNotNone(loaded.created_at)
        self.assertEqual(loaded.created_at, saved.created_at)

    def test_status_updates_survive_reload(self):
        reservation = self.create_reservation()
        created_at = reservation.created_at
        for status in (Reservation.Status.CONFIRMED, Reservation.Status.CANCELLED):
            Reservation.objects.filter(pk=reservation.pk).update(status=status)
            reservation.refresh_from_db()
            self.assertEqual(reservation.status, status)
            self.assertEqual(reservation.created_at, created_at)

    def test_database_rejects_zero_or_negative_duration(self):
        starts_at = timezone.now()
        for ends_at in (starts_at, starts_at - timedelta(minutes=1)):
            with self.subTest(ends_at=ends_at):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    self.create_reservation(starts_at=starts_at, ends_at=ends_at)

    def test_database_rejects_unknown_status(self):
        for status in ('UNKNOWN', 'DRAFT'):
            with self.subTest(status=status), self.assertRaises(IntegrityError), transaction.atomic():
                self.create_reservation(status=status)

    def test_reservation_protects_related_records_from_deletion(self):
        self.create_reservation()
        for related in (self.user, self.resource, self.sport):
            with self.subTest(model=type(related).__name__):
                with self.assertRaises(ProtectedError):
                    related.delete()

    def test_database_requires_user_and_resource(self):
        for field in ('user', 'resource'):
            with self.subTest(field=field):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    self.create_reservation(**{field: None})


class ReservationApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username='customer')
        cls.staff = get_user_model().objects.create_user(
            username='manager',
            is_staff=True,
        )
        cls.sport = Sport.objects.create(name='Tennis')
        cls.resource = Resource.objects.create(
            name='Court 1',
            sport=cls.sport,
            location='Ostrava',
            opens_at=time(8),
            closes_at=time(22),
        )
        cls.approval_resource = Resource.objects.create(
            name='Court 2',
            sport=cls.sport,
            location='Ostrava',
            opens_at=time(8),
            closes_at=time(22),
            requires_approval=True,
        )

    def setUp(self):
        self.client.force_login(self.user)

    def interval(self, starts_at=None, duration=timedelta(hours=1)):
        starts_at = starts_at or timezone.localtime(timezone.now() + timedelta(days=1)).replace(
            hour=10, minute=0, second=0, microsecond=0,
        )
        return {
            'starts_at': starts_at.isoformat(),
            'ends_at': (starts_at + duration).isoformat(),
        }

    def create(self, resource=None, **interval):
        body = {
            'resource_id': (resource or self.resource).pk,
            **(interval or self.interval()),
        }
        response = self.client.post(
            '/api/reservations/',
            json.dumps(body),
            content_type='application/json',
        )
        return response

    def decide(self, reservation_id, decision, staff=True):
        if staff:
            self.client.force_login(self.staff)
        return self.client.post(
            f'/api/reservations/{reservation_id}/approve/',
            json.dumps({'decision': decision}),
            content_type='application/json',
        )

    def test_create_succeeds_and_rejects_invalid_interval(self):
        response = self.create()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['status'], 'CONFIRMED')
        self.assertEqual(Reservation.objects.count(), 1)
        invalid = self.interval(duration=timedelta(0))
        self.assertEqual(self.create(**invalid).status_code, 400)
        self.assertEqual(Reservation.objects.count(), 1)

    def test_create_pending_checks_conflicts_and_inactive_resource(self):
        response = self.create(resource=self.approval_resource)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['status'], 'PENDING_APPROVAL')
        self.assertIsNotNone(Reservation.objects.get(pk=response.json()['id']).approval_requested_at)
        self.assertEqual(self.decide(response.json()['id'], 'approve').status_code, 200)
        self.client.force_login(self.user)
        self.assertEqual(self.create(resource=self.approval_resource).status_code, 409)
        self.approval_resource.is_available = False
        self.approval_resource.save()
        self.assertEqual(self.create(resource=self.approval_resource,
                                     **self.interval(timezone.now() + timedelta(days=2))).status_code, 409)
        self.assertEqual(Reservation.objects.count(), 1)

    def test_availability_checks_confirmed_only_and_half_open_edges(self):
        start = timezone.localtime(timezone.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
        self.create(**self.interval(start))
        for offset, expected in ((-1, 'AVAILABLE'), (0.5, 'UNAVAILABLE'), (1, 'AVAILABLE')):
            response = self.client.get('/api/availability/', {
                'resource_id': self.resource.pk,
                **self.interval(start + timedelta(hours=offset)),
            })
            self.assertEqual(response.json()['availability'], expected)
        self.assertEqual(Reservation.objects.count(), 1)

    def test_approval_request_does_not_block_until_staff_approves(self):
        first = self.create(resource=self.approval_resource).json()['id']
        second = self.create(resource=self.approval_resource).json()['id']
        response = self.client.get('/api/availability/', {
            'resource_id': self.approval_resource.pk, **self.interval(),
        })
        self.assertEqual(response.json()['availability'], 'AVAILABLE')
        self.assertEqual(self.decide(first, 'approve').status_code, 200)
        self.assertEqual(Reservation.objects.get(pk=second).status, 'REJECTED')
        self.assertEqual(self.decide(second, 'approve').status_code, 409)

    def test_confirmation_rejects_only_overlapping_pending_same_resource(self):
        start = timezone.localtime(timezone.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
        ids = [self.create(resource=self.approval_resource,
                           **self.interval(start + timedelta(minutes=offset))).json()['id']
               for offset in (0, 15, 30, 60, -60)]
        other = self.create(**self.interval(start)).json()['id']
        self.assertEqual(self.decide(ids[0], 'approve').status_code, 200)
        self.assertEqual([Reservation.objects.get(pk=id).status for id in ids],
                         ['CONFIRMED', 'REJECTED', 'REJECTED', 'PENDING_APPROVAL', 'PENDING_APPROVAL'])
        self.assertEqual(Reservation.objects.get(pk=other).status, 'CONFIRMED')
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(f'/api/reservations/{ids[0]}/cancel/').status_code, 200)
        self.assertEqual(Reservation.objects.get(pk=ids[1]).status, 'REJECTED')
        self.assertEqual(Reservation.objects.get(pk=ids[2]).status, 'REJECTED')

    def test_automatic_creation_rejects_existing_pending_requests(self):
        pending = self.create(resource=self.approval_resource).json()['id']
        self.approval_resource.requires_approval = False
        self.approval_resource.save()
        result = self.create(resource=self.approval_resource)
        self.assertEqual(result.status_code, 201)
        self.assertEqual(result.json()['status'], 'CONFIRMED')
        self.assertEqual(Reservation.objects.get(pk=pending).status, 'REJECTED')

    def test_staff_can_reject_but_non_staff_cannot_decide(self):
        id = self.create(resource=self.approval_resource).json()['id']
        self.assertEqual(self.decide(id, 'approve', staff=False).status_code, 403)
        self.assertEqual(self.decide(id, 'reject').json()['status'], 'REJECTED')
        self.assertEqual(self.decide(id, 'approve').status_code, 409)

    def test_authentication_ownership_and_unknown_resource(self):
        id = self.create().json()['id']
        other = get_user_model().objects.create_user(username='other')
        self.client.force_login(other)
        self.assertEqual(self.client.post(f'/api/reservations/{id}/cancel/').status_code, 404)
        self.assertEqual(self.create(resource=type('Missing', (), {'pk': 999999})()).status_code, 404)
        self.client.logout()
        self.assertEqual(self.create().status_code, 401)
        self.assertEqual(self.client.get('/api/availability/', {
            'resource_id': self.resource.pk, **self.interval(),
        }).status_code, 401)

    def test_invalid_calendar_date_returns_error_without_creating(self):
        response = self.create(starts_at='2026-02-30T12:00:00Z', ends_at='2026-03-01T13:00:00Z')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Reservation.objects.exists())

    def test_exact_time_limits_and_exceeded_limits(self):
        now = datetime(2026, 11, 7, 9, tzinfo=UTC)
        for offset, duration, expected in (
            (timedelta(0), timedelta(hours=2), 201),
            (timedelta(days=30), timedelta(hours=2), 201),
            (timedelta(days=30, microseconds=1), timedelta(hours=1), 400),
            (timedelta(days=1), timedelta(hours=2, microseconds=1), 400),
            (timedelta(microseconds=-1), timedelta(hours=1), 400),
        ):
            with self.subTest(offset=offset, duration=duration):
                with patch('reservations.rules.TimeRules.now', return_value=now):
                    response = self.create(**self.interval(now + offset, duration))
                self.assertEqual(response.status_code, expected)

    def test_inactive_resource_and_invalid_availability(self):
        self.resource.is_available = False
        self.resource.save()
        self.assertEqual(self.create().status_code, 409)
        result = self.client.get('/api/availability/', {'resource_id': self.resource.pk, **self.interval()})
        self.assertEqual(result.json()['availability'], 'UNAVAILABLE')
        self.assertEqual(self.client.get('/api/availability/', {
            'resource_id': self.resource.pk, **self.interval(duration=timedelta(0)),
        }).status_code, 400)

    def test_cancel_confirmed_releases_resource_and_rejects_repeat(self):
        id = self.create().json()['id']
        self.assertEqual(self.client.post(f'/api/reservations/{id}/cancel/').json()['status'], 'CANCELLED')
        self.assertEqual(self.client.post(f'/api/reservations/{id}/cancel/').status_code, 409)
        self.assertEqual(self.create().status_code, 201)

    def test_owner_can_cancel_pending_approval_but_not_after_start(self):
        id = self.create(resource=self.approval_resource).json()['id']
        self.assertEqual(self.client.post(f'/api/reservations/{id}/cancel/').json()['status'], 'CANCELLED')
        self.assertEqual(self.decide(id, 'approve').status_code, 409)
        self.client.force_login(self.user)
        id = self.create().json()['id']
        row = Reservation.objects.get(pk=id)
        with patch('reservations.rules.TimeRules.now', return_value=row.starts_at):
            self.assertEqual(self.client.post(f'/api/reservations/{id}/cancel/').status_code, 409)
        self.assertEqual(Reservation.objects.get(pk=id).status, 'CONFIRMED')

    def test_delayed_approval_succeeds_after_24_hours_before_start(self):
        now = timezone.localtime(timezone.now()).replace(hour=10, minute=0, second=0, microsecond=0)
        id = self.create(resource=self.approval_resource,
                         **self.interval(now + timedelta(days=3))).json()['id']
        with patch('reservations.rules.TimeRules.now', return_value=now + timedelta(days=2)):
            self.assertEqual(self.decide(id, 'approve').json()['status'], 'CONFIRMED')

    def test_pending_request_remains_actionable_after_24_hours_until_start(self):
        now = timezone.localtime(timezone.now()).replace(hour=10, minute=0, second=0, microsecond=0)
        for action in ('cancel', 'reject', 'command'):
            self.client.force_login(self.user)
            id = self.create(resource=self.approval_resource,
                             **self.interval(now + timedelta(days=3))).json()['id']
            with patch('reservations.rules.TimeRules.now', return_value=now + timedelta(days=2)):
                if action == 'command':
                    call_command('expire_reservations')
                    expected = 'PENDING_APPROVAL'
                elif action == 'reject':
                    self.assertEqual(self.decide(id, 'reject').status_code, 200)
                    expected = 'REJECTED'
                else:
                    self.assertEqual(self.client.post(f'/api/reservations/{id}/cancel/').status_code, 200)
                    expected = 'CANCELLED'
            self.assertEqual(Reservation.objects.get(pk=id).status, expected)

    def test_expiry_exact_deadline_on_approve_cancel_and_command(self):
        start = timezone.localtime(timezone.now() + timedelta(days=3)).replace(hour=10, minute=0, second=0, microsecond=0)
        for action in ('approve', 'reject', 'cancel', 'command'):
            for offset in (timedelta(microseconds=-1), timedelta(0), timedelta(seconds=1)):
                with self.subTest(action=action, offset=offset):
                    row = Reservation.objects.create(
                        user=self.user, resource=self.approval_resource,
                        starts_at=start, ends_at=start + timedelta(hours=1),
                        status='PENDING_APPROVAL', approval_requested_at=start - timedelta(days=3),
                    )
                    before = offset < timedelta(0)
                    with patch('reservations.rules.TimeRules.now', return_value=start + offset):
                        if action == 'command':
                            call_command('expire_reservations')
                            expected = 'PENDING_APPROVAL' if before else 'EXPIRED'
                        else:
                            if action in ('approve', 'reject'):
                                response = self.decide(row.pk, action)
                            else:
                                self.client.force_login(self.user)
                                response = self.client.post(f'/api/reservations/{row.pk}/cancel/')
                            self.assertEqual(response.status_code, 200 if before else 409)
                            expected = {'approve': 'CONFIRMED', 'reject': 'REJECTED', 'cancel': 'CANCELLED'}[action] if before else 'EXPIRED'
                    self.assertEqual(Reservation.objects.get(pk=row.pk).status, expected)
                    row.delete()

    def test_invalid_approval_decision_is_rejected_without_state_change(self):
        id = self.create(resource=self.approval_resource).json()['id']
        self.assertEqual(self.decide(id, 'invalid').status_code, 400)
        with self.assertRaises(ReservationError):
            build_service().approve(id, User(self.staff.pk, True), 'invalid')
        self.assertEqual(Reservation.objects.get(pk=id).status, 'PENDING_APPROVAL')

    def test_confirm_endpoint_removed_and_terminal_states_cannot_reopen(self):
        id = self.create().json()['id']
        self.assertEqual(self.client.post(f'/api/reservations/{id}/confirm/').status_code, 404)
        self.assertEqual(self.decide(id, 'approve').status_code, 409)
        self.assertEqual(self.decide(999999, 'approve').status_code, 404)

    def test_admin_cannot_bypass_reservation_lifecycle(self):
        from .admin import ReservationAdmin
        from django.contrib.admin.sites import AdminSite
        from django.test import RequestFactory
        admin = ReservationAdmin(Reservation, AdminSite())
        request = RequestFactory().get('/')
        request.user = self.staff
        self.assertFalse(admin.has_add_permission(request))
        self.assertFalse(admin.has_change_permission(request))
        self.assertFalse(admin.has_delete_permission(request))
