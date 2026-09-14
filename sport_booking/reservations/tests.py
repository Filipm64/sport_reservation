from datetime import time, timedelta

from django.contrib.auth import get_user_model
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
