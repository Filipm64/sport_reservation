"""HTTP routing adapters; business decisions belong to ReservationService."""
from django.views.decorators.http import require_GET, require_POST

from .wiring import build_endpoint

endpoint = build_endpoint()


@require_POST
def create_reservation(request):
    return endpoint.create(request)


@require_GET
def check_availability(request):
    return endpoint.check_availability(request)


@require_POST
def confirm_reservation(request, reservation_id):
    return endpoint.confirm(request, reservation_id)


@require_POST
def approve_reservation(request, reservation_id):
    return endpoint.approve(request, reservation_id)


@require_POST
def cancel_reservation(request, reservation_id):
    return endpoint.cancel(request, reservation_id)
