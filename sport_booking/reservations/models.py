from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError


class Sport(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Resource(models.Model):
    name = models.CharField(max_length=200)
    sport = models.ForeignKey(Sport, on_delete=models.PROTECT)
    location = models.CharField(max_length=255)
    opens_at = models.TimeField()
    closes_at = models.TimeField()
    is_available = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=False)

    def clean(self):
        super().clean()
        if self.opens_at is not None and self.closes_at is not None and self.opens_at >= self.closes_at:
            raise ValidationError({'closes_at': 'Čas zavření musí být později než čas otevření.'})

    def __str__(self):
        return self.name


class Reservation(models.Model):
    class Status(models.TextChoices):
        PENDING_APPROVAL = 'PENDING_APPROVAL', 'Pending approval'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        REJECTED = 'REJECTED', 'Rejected'
        EXPIRED = 'EXPIRED', 'Expired'
        CANCELLED = 'CANCELLED', 'Cancelled'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    resource = models.ForeignKey(Resource, on_delete=models.PROTECT)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status)
    created_at = models.DateTimeField(auto_now_add=True)
    approval_requested_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(ends_at__gt=models.F('starts_at')),
                name='reservation_end_after_start',
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=[
                    'PENDING_APPROVAL', 'CONFIRMED',
                    'REJECTED', 'EXPIRED', 'CANCELLED',
                ]),
                name='reservation_valid_status',
            ),
        ]
