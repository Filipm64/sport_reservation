from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from reservations.models import Reservation


class Command(BaseCommand):
    help = 'Expire approval requests that have been pending for 24 hours.'

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(hours=24)
        count = Reservation.objects.filter(
            status=Reservation.Status.PENDING_APPROVAL,
        ).filter(
            Q(approval_requested_at__lte=cutoff)
            | Q(starts_at__lte=timezone.now())
        ).update(status=Reservation.Status.EXPIRED)
        self.stdout.write(f'Expired {count} reservation(s).')
