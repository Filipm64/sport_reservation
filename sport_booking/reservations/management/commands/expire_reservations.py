from django.core.management.base import BaseCommand

from reservations.wiring import build_service


class Command(BaseCommand):
    help = 'Expire pending approvals when their reservation starts.'

    def handle(self, *args, **options):
        count = build_service().expire_due()
        self.stdout.write(f'Expired {count} reservation(s).')
