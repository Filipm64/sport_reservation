import json
from datetime import timedelta
from json import JSONDecodeError

from django.db import transaction
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_GET, require_POST

from .models import Reservation, Resource

APPROVAL_TIMEOUT = timedelta(hours=24)


def _login_required(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required.'}, status=401)
    return None


def _json_body(request):
    try:
        data = json.loads(request.body)
    except (JSONDecodeError, UnicodeDecodeError):
        return None, JsonResponse({'error': 'Request body must be valid JSON.'}, status=400)
    if not isinstance(data, dict):
        return None, JsonResponse({'error': 'Request body must be a JSON object.'}, status=400)
    return data, None


def _parse_interval(data):
    start_value = data.get('starts_at', '')
    end_value = data.get('ends_at', '')
    if not isinstance(start_value, str) or not isinstance(end_value, str):
        return None, None, 'Use ISO 8601 start and end datetimes.'
    starts_at = parse_datetime(start_value)
    ends_at = parse_datetime(end_value)
    if starts_at is None or ends_at is None:
        return None, None, 'Use ISO 8601 start and end datetimes.'
    if not timezone.is_aware(starts_at) or not timezone.is_aware(ends_at):
        return None, None, 'Datetimes must include a timezone.'
    return starts_at, ends_at, None


def _interval_error(starts_at, ends_at, now=None):
    now = now or timezone.now()
    if starts_at >= ends_at:
        return 'End must be after start.'
    if starts_at < now:
        return 'Reservation cannot start in the past.'
    if starts_at > now + timedelta(days=30):
        return 'Reservation cannot start more than 30 days ahead.'
    if ends_at - starts_at > timedelta(hours=2):
        return 'Reservation cannot be longer than 2 hours.'
    return None


def _has_conflict(resource, starts_at, ends_at):
    return Reservation.objects.filter(
        resource=resource,
        status=Reservation.Status.CONFIRMED,
        starts_at__lt=ends_at,
        ends_at__gt=starts_at,
    ).exists()


def _reservation_json(reservation):
    return {
        'id': reservation.pk,
        'status': reservation.status,
        'resource_id': reservation.resource_id,
        'starts_at': reservation.starts_at.isoformat(),
        'ends_at': reservation.ends_at.isoformat(),
    }


@require_POST
def create_reservation(request: HttpRequest):
    denied = _login_required(request)
    if denied:
        return denied
    data, error = _json_body(request)
    if error:
        return error
    try:
        resource_id = int(data.get('resource_id'))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'resource_id must be an integer.'}, status=400)
    starts_at, ends_at, error_message = _parse_interval(data)
    if error_message:
        return JsonResponse({'error': error_message}, status=400)
    error_message = _interval_error(starts_at, ends_at)
    if error_message:
        return JsonResponse({'error': error_message}, status=400)
    resource = get_object_or_404(Resource, pk=resource_id)
    reservation = Reservation.objects.create(
        user=request.user,
        resource=resource,
        starts_at=starts_at,
        ends_at=ends_at,
    )
    return JsonResponse(_reservation_json(reservation), status=201)


@require_GET
def check_availability(request: HttpRequest):
    denied = _login_required(request)
    if denied:
        return denied
    try:
        resource_id = int(request.GET.get('resource_id', ''))
    except ValueError:
        return JsonResponse({'error': 'resource_id must be an integer.'}, status=400)
    starts_at, ends_at, error_message = _parse_interval(request.GET)
    if error_message:
        return JsonResponse({'error': error_message}, status=400)
    error_message = _interval_error(starts_at, ends_at)
    if error_message:
        return JsonResponse({'error': error_message}, status=400)
    resource = get_object_or_404(Resource, pk=resource_id)
    available = resource.is_available and not _has_conflict(resource, starts_at, ends_at)
    return JsonResponse({'availability': 'AVAILABLE' if available else 'UNAVAILABLE'})


@require_POST
def confirm_reservation(request: HttpRequest, reservation_id: int):
    denied = _login_required(request)
    if denied:
        return denied
    with transaction.atomic():
        reservation = get_object_or_404(
            Reservation.objects.select_for_update(),
            pk=reservation_id,
            user=request.user,
        )
        if reservation.status != Reservation.Status.DRAFT:
            return JsonResponse({'error': 'Only DRAFT reservations can be confirmed.'}, status=409)
        resource = get_object_or_404(
            Resource.objects.select_for_update(),
            pk=reservation.resource_id,
        )
        error_message = _interval_error(reservation.starts_at, reservation.ends_at)
        if error_message:
            return JsonResponse({'error': error_message}, status=409)
        if not resource.is_available:
            return JsonResponse({'error': 'Resource is unavailable.'}, status=409)
        if _has_conflict(resource, reservation.starts_at, reservation.ends_at):
            return JsonResponse({'error': 'Reservation interval is already taken.'}, status=409)
        if resource.requires_approval:
            reservation.status = Reservation.Status.PENDING_APPROVAL
            reservation.approval_requested_at = timezone.now()
            reservation.save(update_fields=('status', 'approval_requested_at'))
            return JsonResponse(_reservation_json(reservation))
        reservation.status = Reservation.Status.CONFIRMED
        reservation.save(update_fields=('status',))
        return JsonResponse(_reservation_json(reservation))


@require_POST
def approve_reservation(request: HttpRequest, reservation_id: int):
    denied = _login_required(request)
    if denied:
        return denied
    if not request.user.is_staff:
        return JsonResponse({'error': 'Only a staff user can decide approval.'}, status=403)
    data, error = _json_body(request)
    if error:
        return error
    decision = data.get('decision')
    if decision not in ('approve', 'reject'):
        return JsonResponse({'error': "decision must be 'approve' or 'reject'."}, status=400)

    with transaction.atomic():
        reservation = get_object_or_404(
            Reservation.objects.select_for_update(),
            pk=reservation_id,
        )
        if reservation.status != Reservation.Status.PENDING_APPROVAL:
            return JsonResponse({'error': 'Reservation is not awaiting approval.'}, status=409)
        now = timezone.now()
        if (
            reservation.approval_requested_at is None
            or reservation.approval_requested_at + APPROVAL_TIMEOUT <= now
            or reservation.starts_at <= now
        ):
            reservation.status = Reservation.Status.EXPIRED
            reservation.save(update_fields=('status',))
            return JsonResponse(
                {'error': 'Approval request expired.', 'status': reservation.status},
                status=409,
            )
        if decision == 'reject':
            reservation.status = Reservation.Status.REJECTED
            reservation.save(update_fields=('status',))
            return JsonResponse(_reservation_json(reservation))

        resource = get_object_or_404(
            Resource.objects.select_for_update(),
            pk=reservation.resource_id,
        )
        error_message = _interval_error(reservation.starts_at, reservation.ends_at, now)
        if error_message:
            return JsonResponse({'error': error_message}, status=409)
        if not resource.is_available:
            return JsonResponse({'error': 'Resource is unavailable.'}, status=409)
        if _has_conflict(resource, reservation.starts_at, reservation.ends_at):
            return JsonResponse({'error': 'Reservation interval is already taken.'}, status=409)
        reservation.status = Reservation.Status.CONFIRMED
        reservation.save(update_fields=('status',))
        return JsonResponse(_reservation_json(reservation))


@require_POST
def cancel_reservation(request: HttpRequest, reservation_id: int):
    denied = _login_required(request)
    if denied:
        return denied
    with transaction.atomic():
        reservation = get_object_or_404(
            Reservation.objects.select_for_update(),
            pk=reservation_id,
            user=request.user,
        )
        if reservation.status not in (
            Reservation.Status.DRAFT,
            Reservation.Status.PENDING_APPROVAL,
            Reservation.Status.CONFIRMED,
        ):
            return JsonResponse({'error': 'Reservation cannot be cancelled in this state.'}, status=409)
        if timezone.now() >= reservation.starts_at:
            return JsonResponse({'error': 'Reservation has already started.'}, status=409)
        reservation.status = Reservation.Status.CANCELLED
        reservation.save(update_fields=('status',))
        return JsonResponse(_reservation_json(reservation))
