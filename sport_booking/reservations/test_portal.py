from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from .models import Reservation, Resource, Sport


class PortalTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username='customer',
            password='Customer-pass-9876!',
        )
        cls.staff = get_user_model().objects.create_user(
            username='manager',
            password='Manager-pass-9876!',
            is_staff=True,
        )
        sport = Sport.objects.create(name='Tenis')
        cls.resource = Resource.objects.create(
            name='Centrální kurt',
            sport=sport,
            location='Praha',
            opens_at='08:00',
            closes_at='22:00',
        )
        cls.approval_resource = Resource.objects.create(
            name='Hala',
            sport=sport,
            location='Praha',
            opens_at='08:00',
            closes_at='22:00',
            requires_approval=True,
        )

    def booking_data(self, resource=None):
        start = timezone.localtime(timezone.now() + timedelta(days=1))
        start = start.replace(hour=15, minute=0, second=0, microsecond=0)
        return {
            'resource_id': (resource or self.resource).pk,
            'starts_at': start.strftime('%Y-%m-%dT%H:%M'),
            'ends_at': (start + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M'),
        }

    def create_booking(self, resource=None):
        self.client.force_login(self.user)
        response = self.client.post('/', {
            **self.booking_data(resource),
            'action': 'create',
        })
        self.assertRedirects(response, '/')
        return Reservation.objects.get(user=self.user)

    def test_home_displays_public_venue_catalog(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Centrální kurt')
        self.assertContains(response, 'Praha')
        self.assertContains(response, 'Vytvořit účet')

    def test_customer_can_register_and_is_logged_in(self):
        response = self.client.post('/registrace/', {
            'username': 'new-customer',
            'password1': 'Safe-passphrase-2026!',
            'password2': 'Safe-passphrase-2026!',
        })

        self.assertRedirects(response, '/')
        self.assertIn('_auth_user_id', self.client.session)
        self.assertEqual(
            self.client.session['_auth_user_id'],
            str(get_user_model().objects.get(username='new-customer').pk),
        )

    def test_booking_creation_confirms_in_one_step(self):
        self.client.force_login(self.user)
        created = self.client.post('/', {
            **self.booking_data(),
            'action': 'create',
        })
        self.assertRedirects(created, '/')
        reservation = Reservation.objects.get(user=self.user)
        self.assertEqual(reservation.status, Reservation.Status.CONFIRMED)

        self.assertNotContains(self.client.get('/'), f'/rezervace/{reservation.pk}/confirm/')

    def test_approval_resource_waits_for_staff_decision(self):
        reservation = self.create_booking(self.approval_resource)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.Status.PENDING_APPROVAL)

        self.client.force_login(self.staff)
        response = self.client.post(f'/rezervace/{reservation.pk}/approve/')

        self.assertRedirects(response, '/')
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.Status.CONFIRMED)

    def test_non_staff_cannot_approve_pending_reservation(self):
        reservation = self.create_booking(self.approval_resource)

        response = self.client.post(f'/rezervace/{reservation.pk}/approve/')

        self.assertRedirects(response, '/')
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.Status.PENDING_APPROVAL)

    def test_customer_cannot_cancel_another_users_reservation(self):
        reservation = self.create_booking()
        other_user = get_user_model().objects.create_user(username='other')
        reservation.user = other_user
        reservation.save(update_fields=('user',))

        self.client.post(f'/rezervace/{reservation.pk}/cancel/')

        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.Status.CONFIRMED)

    def test_availability_check_does_not_create_reservation(self):
        self.client.force_login(self.user)

        response = self.client.post('/', {
            **self.booking_data(),
            'action': 'availability',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Termín vypadá volně')
        self.assertFalse(Reservation.objects.exists())

    def test_unknown_booking_action_does_not_create_reservation(self):
        self.client.force_login(self.user)

        response = self.client.post('/', {
            **self.booking_data(),
            'action': 'unexpected',
        })

        self.assertRedirects(response, '/')
        self.assertFalse(Reservation.objects.exists())

    def test_staff_approval_rejects_competing_web_request(self):
        self.client.force_login(self.user)
        for _ in range(2):
            self.client.post('/', {**self.booking_data(self.approval_resource), 'action': 'create'})
        first, second = Reservation.objects.order_by('pk')
        self.client.force_login(self.staff)
        self.assertRedirects(self.client.post(f'/rezervace/{first.pk}/approve/'), '/')
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(first.status, 'CONFIRMED')
        self.assertEqual(second.status, 'REJECTED')

    def test_conflicting_web_creation_does_not_create_second_record(self):
        self.create_booking()
        self.client.post('/', {**self.booking_data(), 'action': 'create'})
        self.assertEqual(Reservation.objects.count(), 1)
        self.assertEqual(Reservation.objects.get().status, 'CONFIRMED')
