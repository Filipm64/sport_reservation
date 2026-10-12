import json
from datetime import time, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from .models import Reservation, Resource, Sport


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
            ends_at=starts_at + timedelta(hours=1),
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
        self.assertEqual(loaded.status, Reservation.Status.DRAFT)
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
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.create_reservation(status='UNKNOWN')

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
        starts_at = starts_at or timezone.now() + timedelta(days=1)
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
        reservation = Reservation.objects.get(pk=response.json()['id'])
        self.assertEqual(reservation.status, Reservation.Status.DRAFT)

        starts_at = timezone.now() + timedelta(days=1)
        invalid = self.create(
            starts_at=starts_at.isoformat(),
            ends_at=starts_at.isoformat(),
        )
        self.assertEqual(invalid.status_code, 400)

    def test_availability_checks_confirmed_only_and_half_open_edges(self):
        existing = Reservation.objects.create(
            user=self.user,
            resource=self.resource,
            starts_at=timezone.now() + timedelta(days=1),
            ends_at=timezone.now() + timedelta(days=1, hours=1),
            status=Reservation.Status.CONFIRMED,
        )
        adjacent = {
            'resource_id': self.resource.pk,
            **self.interval(starts_at=existing.ends_at),
        }
        response = self.client.get('/api/availability/', adjacent)
        self.assertEqual(response.json()['availability'], 'AVAILABLE')

        overlapping = {
            'resource_id': self.resource.pk,
            **self.interval(starts_at=existing.starts_at + timedelta(minutes=30)),
        }
        response = self.client.get('/api/availability/', overlapping)
        self.assertEqual(response.json()['availability'], 'UNAVAILABLE')

        self.create(resource=self.approval_resource)
        draft_query = {
            'resource_id': self.approval_resource.pk,
            **self.interval(),
        }
        response = self.client.get('/api/availability/', draft_query)
        self.assertEqual(response.json()['availability'], 'AVAILABLE')

    def test_confirm_conflict_is_rejected_and_normal_confirm_succeeds(self):
        first = self.create()
        first_id = first.json()['id']
        self.assertEqual(
            self.client.post(f'/api/reservations/{first_id}/confirm/').status_code,
            200,
        )
        second = self.create()
        self.assertEqual(
            self.client.post(
                f"/api/reservations/{second.json()['id']}/confirm/"
            ).status_code,
            409,
        )
        self.assertEqual(
            Reservation.objects.get(pk=second.json()['id']).status,
            Reservation.Status.DRAFT,
        )

    def test_approval_request_does_not_block_until_staff_approves(self):
        request = self.create(resource=self.approval_resource)
        reservation_id = request.json()['id']
        response = self.client.post(f'/api/reservations/{reservation_id}/confirm/')
        self.assertEqual(response.json()['status'], Reservation.Status.PENDING_APPROVAL)

        query = {
            'resource_id': self.approval_resource.pk,
            **self.interval(),
        }
        response = self.client.get('/api/availability/', query)
        self.assertEqual(response.json()['availability'], 'AVAILABLE')

        self.assertEqual(self.decide(reservation_id, 'approve').status_code, 200)
        self.assertEqual(
            Reservation.objects.get(pk=reservation_id).status,
            Reservation.Status.CONFIRMED,
        )

    def test_delayed_approval_succeeds_before_timeout(self):
        request = self.create(resource=self.approval_resource)
        reservation_id = request.json()['id']
        self.client.post(f'/api/reservations/{reservation_id}/confirm/')
        reservation = Reservation.objects.get(pk=reservation_id)
        reservation.approval_requested_at -= timedelta(hours=23)
        reservation.save(update_fields=('approval_requested_at',))

        response = self.decide(reservation_id, 'approve')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], Reservation.Status.CONFIRMED)

    def test_new_conflict_prevents_approval_and_leaves_request_pending(self):
        request = self.create(resource=self.approval_resource)
        reservation_id = request.json()['id']
        self.client.post(f'/api/reservations/{reservation_id}/confirm/')
        pending = Reservation.objects.get(pk=reservation_id)
        Reservation.objects.create(
            user=self.user,
            resource=self.approval_resource,
            starts_at=pending.starts_at,
            ends_at=pending.ends_at,
            status=Reservation.Status.CONFIRMED,
        )

        response = self.decide(reservation_id, 'approve')
        self.assertEqual(response.status_code, 409)
        pending.refresh_from_db()
        self.assertEqual(pending.status, Reservation.Status.PENDING_APPROVAL)

    def test_staff_can_reject_but_non_staff_cannot_decide(self):
        request = self.create(resource=self.approval_resource)
        reservation_id = request.json()['id']
        self.client.post(f'/api/reservations/{reservation_id}/confirm/')

        denied = self.decide(reservation_id, 'approve', staff=False)
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(self.decide(reservation_id, 'reject').status_code, 200)
        self.assertEqual(
            Reservation.objects.get(pk=reservation_id).status,
            Reservation.Status.REJECTED,
        )

    def test_expired_approval_cannot_be_approved(self):
        request = self.create(resource=self.approval_resource)
        reservation_id = request.json()['id']
        self.client.post(f'/api/reservations/{reservation_id}/confirm/')
        reservation = Reservation.objects.get(pk=reservation_id)
        reservation.approval_requested_at = timezone.now() - timedelta(hours=24)
        reservation.save(update_fields=('approval_requested_at',))

        response = self.decide(reservation_id, 'approve')
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['status'], Reservation.Status.EXPIRED)

    def test_expiry_management_command_updates_old_requests(self):
        request = self.create(resource=self.approval_resource)
        reservation_id = request.json()['id']
        self.client.post(f'/api/reservations/{reservation_id}/confirm/')
        reservation = Reservation.objects.get(pk=reservation_id)
        reservation.approval_requested_at = timezone.now() - timedelta(hours=24)
        reservation.save(update_fields=('approval_requested_at',))

        call_command('expire_reservations')
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.Status.EXPIRED)

    def test_owner_can_cancel_pending_approval_but_not_after_start(self):
        request = self.create(resource=self.approval_resource)
        reservation_id = request.json()['id']
        self.client.post(f'/api/reservations/{reservation_id}/confirm/')
        cancelled = self.client.post(f'/api/reservations/{reservation_id}/cancel/')
        self.assertEqual(cancelled.json()['status'], Reservation.Status.CANCELLED)
        self.assertTrue(Reservation.objects.filter(pk=reservation_id).exists())
        self.assertEqual(self.decide(reservation_id, 'approve').status_code, 409)

        started = Reservation.objects.create(
            user=self.user,
            resource=self.resource,
            starts_at=timezone.now() - timedelta(minutes=1),
            ends_at=timezone.now() + timedelta(minutes=59),
            status=Reservation.Status.CONFIRMED,
        )
        self.client.force_login(self.user)
        rejected = self.client.post(f'/api/reservations/{started.pk}/cancel/')
        self.assertEqual(rejected.status_code, 409)


    def test_invalid_calendar_date_returns_error_without_creating(self):
        response = self.create(starts_at='2026-02-30T12:00:00Z',
                               ends_at='2026-02-30T13:00:00Z')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Reservation.objects.count(), 0)

    def test_exact_time_limits_and_exceeded_limits(self):
        now = timezone.now()
        with patch('reservations.rules.TimeRules.now', return_value=now):
            for offset, duration, expected in (
                (timedelta(0), timedelta(hours=2), 201),
                (timedelta(days=30), timedelta(hours=2), 201),
                (timedelta(days=30, microseconds=1), timedelta(hours=1), 400),
                (timedelta(days=1), timedelta(hours=2, microseconds=1), 400),
                (timedelta(microseconds=-1), timedelta(hours=1), 400),
            ):
                with self.subTest(offset=offset, duration=duration):
                    response = self.create(**self.interval(now + offset, duration))
                    self.assertEqual(response.status_code, expected)

    def test_authentication_ownership_and_unknown_resource(self):
        reservation_id = self.create().json()['id']
        self.client.logout()
        self.assertEqual(self.create().status_code, 401)
        self.assertEqual(self.client.get('/api/availability/').status_code, 401)
        other = get_user_model().objects.create_user(username='other')
        self.client.force_login(other)
        for operation in ('confirm', 'cancel'):
            self.assertEqual(self.client.post(
                f'/api/reservations/{reservation_id}/{operation}/'
            ).status_code, 404)
        response = self.client.post('/api/reservations/', json.dumps({
            'resource_id': 999999, **self.interval(),
        }), content_type='application/json')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Reservation.objects.count(), 1)

    def test_inactive_resource_and_invalid_availability(self):
        reservation_id = self.create().json()['id']
        self.resource.is_available = False
        self.resource.save()
        query = {'resource_id': self.resource.pk, **self.interval()}
        self.assertEqual(self.client.get('/api/availability/', query).json()
                         ['availability'], 'UNAVAILABLE')
        self.assertEqual(self.client.post(
            f'/api/reservations/{reservation_id}/confirm/').status_code, 409)
        query['ends_at'] = query['starts_at']
        self.assertEqual(self.client.get('/api/availability/', query).status_code, 400)
        self.assertEqual(Reservation.objects.get(pk=reservation_id).status, 'DRAFT')

    def test_cancel_draft_and_confirmed_releases_resource_and_rejects_repeat(self):
        for confirmed in (False, True):
            with self.subTest(confirmed=confirmed):
                reservation_id = self.create().json()['id']
                if confirmed:
                    self.assertEqual(self.client.post(
                        f'/api/reservations/{reservation_id}/confirm/').status_code, 200)
                self.assertEqual(self.client.post(
                    f'/api/reservations/{reservation_id}/cancel/').status_code, 200)
                self.assertEqual(self.client.post(
                    f'/api/reservations/{reservation_id}/cancel/').status_code, 409)
                self.assertEqual(Reservation.objects.get(pk=reservation_id).status, 'CANCELLED')
                query = {'resource_id': self.resource.pk, **self.interval()}
                self.assertEqual(self.client.get('/api/availability/', query).json()
                                 ['availability'], 'AVAILABLE')

    def test_cancel_at_exact_start_is_rejected(self):
        reservation_id = self.create().json()['id']
        reservation = Reservation.objects.get(pk=reservation_id)
        with patch('reservations.rules.TimeRules.now', return_value=reservation.starts_at):
            response = self.client.post(f'/api/reservations/{reservation_id}/cancel/')
        self.assertEqual(response.status_code, 409)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, 'DRAFT')

    def test_expiry_exact_deadline_on_approve_cancel_and_command(self):
        now = timezone.now()
        for action in ('approve', 'cancel', 'command'):
            for deadline in ('timeout', 'start'):
                with self.subTest(action=action, deadline=deadline):
                    reservation = Reservation.objects.create(
                        user=self.user, resource=self.approval_resource,
                        starts_at=now if deadline == 'start' else now + timedelta(days=1),
                        ends_at=now + timedelta(days=1, hours=1),
                        status='PENDING_APPROVAL',
                        approval_requested_at=now - timedelta(hours=24 if deadline == 'timeout' else 1),
                    )
                    with patch('reservations.rules.TimeRules.now', return_value=now):
                        if action == 'command':
                            call_command('expire_reservations')
                        elif action == 'approve':
                            self.assertEqual(self.decide(reservation.pk, 'approve').status_code, 409)
                        else:
                            self.client.force_login(self.user)
                            self.assertEqual(self.client.post(
                                f'/api/reservations/{reservation.pk}/cancel/').status_code, 409)
                    reservation.refresh_from_db()
                    self.assertEqual(reservation.status, 'EXPIRED')

    def test_approve_then_cancel_and_cancel_then_approve(self):
        first = self.create(resource=self.approval_resource).json()['id']
        self.client.post(f'/api/reservations/{first}/confirm/')
        self.assertEqual(self.decide(first, 'approve').status_code, 200)
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(f'/api/reservations/{first}/cancel/').status_code, 200)
        second = self.create(resource=self.approval_resource).json()['id']
        self.client.post(f'/api/reservations/{second}/confirm/')
        self.assertEqual(self.client.post(f'/api/reservations/{second}/cancel/').status_code, 200)
        self.assertEqual(self.decide(second, 'approve').status_code, 409)

    def test_admin_cannot_bypass_reservation_lifecycle(self):
        from django.contrib import admin
        from django.test import RequestFactory
        reservation = Reservation.objects.get(pk=self.create().json()['id'])
        request = RequestFactory().get('/admin/')
        request.user = self.staff
        model_admin = admin.site._registry[Reservation]
        self.assertFalse(model_admin.has_add_permission(request))
        self.assertFalse(model_admin.has_delete_permission(request, reservation))
        for field in ('status', 'resource', 'user', 'starts_at', 'ends_at'):
            self.assertIn(field, model_admin.get_readonly_fields(request, reservation))
