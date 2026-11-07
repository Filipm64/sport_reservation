"""Observable success, failure, role and time boundaries for REQ-07 through REQ-11."""
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.utils import timezone

from .models import Reservation, Resource, Sport


class PortalRequirementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = get_user_model().objects.create_user(
            username='customer', password='Customer-passphrase-2026!',
        )
        cls.staff = get_user_model().objects.create_user(
            username='staff', password='Manager-passphrase-2026!', is_staff=True,
        )
        cls.other = get_user_model().objects.create_user(username='other')
        sport = Sport.objects.create(name='Tenis')
        cls.resource = Resource.objects.create(
            name='Kurt A', sport=sport, location='Ostrava',
            opens_at='08:00', closes_at='22:00',
        )
        cls.approval_resource = Resource.objects.create(
            name='Kurt B', sport=sport, location='Praha',
            opens_at='09:00', closes_at='21:00', requires_approval=True,
        )

    def reservation(self, user=None, status='PENDING_APPROVAL', start=None):
        start = start or timezone.now() + timedelta(days=2)
        return Reservation.objects.create(
            user=user or self.customer, resource=self.approval_resource,
            starts_at=start, ends_at=start + timedelta(hours=1), status=status,
            approval_requested_at=start - timedelta(days=2),
        )

    def test_public_catalog_shows_metadata_and_operating_availability(self):
        self.resource.is_available = False
        self.resource.save(update_fields=('is_available',))
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        for text in ('Kurt A', 'Kurt B', 'Tenis', 'Ostrava', 'Praha',
                     '08:00–22:00', '09:00–21:00', 'Momentálně nedostupné', 'Se schválením'):
            self.assertContains(response, text)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertFalse(Reservation.objects.exists())

    def test_empty_public_catalog_is_displayed_without_error(self):
        Resource.objects.all().delete()
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Aktuálně nejsou přidaná žádná sportoviště')
        self.assertEqual(response.context['resources'], [])

    def test_registration_creates_only_customer_and_authenticates(self):
        count = get_user_model().objects.count()
        response = self.client.post('/registrace/', {
            'username': 'new-customer',
            'password1': 'New-customer-passphrase-2026!',
            'password2': 'New-customer-passphrase-2026!',
            'is_staff': 'true', 'is_superuser': 'true',
        })
        self.assertRedirects(response, '/')
        self.assertEqual(get_user_model().objects.count(), count + 1)
        user = get_user_model().objects.get(username='new-customer')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password('New-customer-passphrase-2026!'))
        self.assertEqual(self.client.session['_auth_user_id'], str(user.pk))

    def test_invalid_registration_does_not_create_or_authenticate_user(self):
        count = get_user_model().objects.count()
        for username, first, second, field in (
            ('customer', 'Valid-passphrase-2026!', 'Valid-passphrase-2026!', 'username'),
            ('new', 'Valid-passphrase-2026!', 'different', 'password2'),
            ('new', '123', '123', 'password2'),
            ('', 'Valid-passphrase-2026!', 'Valid-passphrase-2026!', 'username'),
        ):
            with self.subTest(username=username, field=field):
                response = self.client.post('/registrace/', {
                    'username': username, 'password1': first, 'password2': second,
                })
                self.assertEqual(response.status_code, 200)
                self.assertIn(field, response.context['form'].errors)
                self.assertEqual(get_user_model().objects.count(), count)
                self.assertNotIn('_auth_user_id', self.client.session)

    def test_authenticated_user_cannot_create_second_account(self):
        self.client.force_login(self.customer)
        count = get_user_model().objects.count()
        self.assertRedirects(self.client.post('/registrace/', {
            'username': 'unwanted', 'password1': 'Another-passphrase-2026!',
            'password2': 'Another-passphrase-2026!',
        }), '/')
        self.assertEqual(get_user_model().objects.count(), count)
        self.assertEqual(self.client.session['_auth_user_id'], str(self.customer.pk))

    def test_login_accepts_active_customer_and_staff(self):
        for user, password in ((self.customer, 'Customer-passphrase-2026!'),
                               (self.staff, 'Manager-passphrase-2026!')):
            with self.subTest(user=user.username):
                self.client.logout()
                self.assertRedirects(self.client.post('/prihlaseni/', {
                    'username': user.username, 'password': password,
                }), '/')
                self.assertEqual(self.client.session['_auth_user_id'], str(user.pk))

    def test_login_rejects_invalid_credentials_and_inactive_account(self):
        inactive = get_user_model().objects.create_user(
            username='inactive', password='Inactive-passphrase-2026!', is_active=False,
        )
        for username, password in (('customer', 'wrong'), ('unknown', 'wrong'),
                                   (inactive.username, 'Inactive-passphrase-2026!')):
            with self.subTest(username=username):
                response = self.client.post('/prihlaseni/', {
                    'username': username, 'password': password,
                })
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context['form'].non_field_errors())
                self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_does_not_redirect_to_untrusted_host(self):
        self.assertRedirects(self.client.post('/prihlaseni/', {
            'username': 'customer', 'password': 'Customer-passphrase-2026!',
            'next': 'https://untrusted.example/',
        }), '/')

    def test_logout_requires_post_and_ends_session(self):
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get('/odhlaseni/').status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)
        self.assertRedirects(self.client.post('/odhlaseni/'), '/')
        self.assertNotIn('_auth_user_id', self.client.session)
        response = self.client.get('/')
        self.assertEqual(response.context['reservations'], [])

    def test_account_forms_require_csrf(self):
        for path in ('/registrace/', '/prihlaseni/'):
            with self.subTest(path=path):
                client = Client(enforce_csrf_checks=True)
                self.assertEqual(client.post(path, {}).status_code, 403)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.customer)
        self.assertEqual(client.post('/odhlaseni/').status_code, 403)
        self.assertIn('_auth_user_id', client.session)

    def test_customer_sees_only_own_reservations_in_all_five_states(self):
        start = timezone.now() + timedelta(days=2)
        rows = [self.reservation(status=status, start=start + timedelta(hours=i))
                for i, status in enumerate(('PENDING_APPROVAL', 'CONFIRMED', 'REJECTED', 'CANCELLED', 'EXPIRED'))]
        other = self.reservation(user=self.other)
        self.client.force_login(self.customer)
        response = self.client.get('/')
        self.assertEqual([row.id for row in response.context['reservations']],
                         [row.pk for row in reversed(rows)])
        self.assertNotIn(other.pk, {row.id for row in response.context['reservations']})
        for label in ('Čeká na schválení', 'Potvrzeno', 'Zamítnuto', 'Zrušeno', 'Vypršelo'):
            self.assertContains(response, label)
        for row in rows:
            for text in (row.resource.name, row.resource.location,
                         timezone.localtime(row.starts_at).strftime('%H:%M'),
                         timezone.localtime(row.ends_at).strftime('%H:%M')):
                self.assertContains(response, text)

    def test_staff_personal_list_still_contains_only_own_reservations(self):
        own = self.reservation(user=self.staff)
        self.reservation(user=self.other)
        self.client.force_login(self.staff)
        response = self.client.get('/')
        self.assertEqual([row.id for row in response.context['reservations']], [own.pk])

    def test_guest_and_customer_cannot_see_staff_queue(self):
        self.reservation(user=self.other)
        for user in (None, self.customer):
            with self.subTest(user=user):
                if user:
                    self.client.force_login(user)
                response = self.client.get('/')
                self.assertEqual(response.context['pending_reservations'], [])
                self.assertNotContains(response, 'id="staff-title"')
                self.assertNotContains(response, 'other')
                if user is None:
                    self.assertEqual(response.context['reservations'], [])

    def test_customer_with_no_reservations_sees_empty_state(self):
        self.reservation(user=self.other)
        self.client.force_login(self.customer)
        response = self.client.get('/')
        self.assertEqual(response.context['reservations'], [])
        self.assertContains(response, 'Zatím žádné rezervace')

    def test_staff_queue_shows_only_pending_before_start_without_mutation(self):
        now = timezone.now()
        valid = self.reservation(user=self.other, start=now + timedelta(hours=1))
        # Its age exceeds 24 hours; only its start time determines expiry.
        Reservation.objects.filter(pk=valid.pk).update(approval_requested_at=now - timedelta(days=2))
        at_start = self.reservation(start=now)
        past_start = self.reservation(start=now - timedelta(seconds=1))
        for state in ('CONFIRMED', 'REJECTED', 'CANCELLED', 'EXPIRED'):
            self.reservation(status=state)
        before = list(Reservation.objects.order_by('pk').values())
        self.client.force_login(self.staff)
        with patch('reservations.web_views.timezone.now', return_value=now):
            response = self.client.get('/')
        self.assertEqual([row.id for row in response.context['pending_reservations']], [valid.pk])
        self.assertContains(response, 'Čekající žádosti')
        self.assertContains(response, 'other')
        self.assertContains(response, timezone.localtime(valid.ends_at).strftime('%H:%M'))
        self.assertContains(response, f'/rezervace/{valid.pk}/approve/')
        self.assertContains(response, f'/rezervace/{valid.pk}/reject/')
        self.assertNotContains(response, f'/rezervace/{at_start.pk}/approve/')
        self.assertNotContains(response, f'/rezervace/{past_start.pk}/approve/')
        self.assertEqual(list(Reservation.objects.order_by('pk').values()), before)

    def test_staff_queue_displays_empty_state(self):
        self.client.force_login(self.staff)
        response = self.client.get('/')
        self.assertEqual(response.context['pending_reservations'], [])
        self.assertContains(response, 'Žádné žádosti teď nečekají na schválení')

    def test_personal_list_displays_effective_expiry_without_writing_database(self):
        now = timezone.now()
        row = self.reservation(start=now)
        self.client.force_login(self.customer)
        with patch('reservations.web_views.timezone.now', return_value=now):
            response = self.client.get('/')
        self.assertEqual(response.context['reservations'][0].status, 'EXPIRED')
        self.assertContains(response, 'Vypršelo')
        self.assertNotContains(response, f'/rezervace/{row.pk}/cancel/')
        row.refresh_from_db()
        self.assertEqual(row.status, 'PENDING_APPROVAL')

    def test_account_forms_work_with_valid_csrf_tokens(self):
        client = Client(enforce_csrf_checks=True)
        client.get('/registrace/')
        self.assertRedirects(client.post('/registrace/', {
            'username': 'csrf-customer',
            'password1': 'Csrf-customer-passphrase-2026!',
            'password2': 'Csrf-customer-passphrase-2026!',
            'csrfmiddlewaretoken': client.cookies['csrftoken'].value,
        }), '/')
        self.assertIn('_auth_user_id', client.session)
        self.assertRedirects(client.post('/odhlaseni/', {
            'csrfmiddlewaretoken': client.cookies['csrftoken'].value,
        }), '/')
        self.assertNotIn('_auth_user_id', client.session)
        client.get('/prihlaseni/')
        self.assertRedirects(client.post('/prihlaseni/', {
            'username': 'csrf-customer', 'password': 'Csrf-customer-passphrase-2026!',
            'csrfmiddlewaretoken': client.cookies['csrftoken'].value,
        }), '/')
        self.assertIn('_auth_user_id', client.session)
        self.assertRedirects(client.get('/prihlaseni/'), '/')
