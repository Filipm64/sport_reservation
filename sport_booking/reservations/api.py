import json
from json import JSONDecodeError

from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .domain import ReservationError, TimeInterval
from .services import AvailabilityQueries, ReservationService


class ReservationEndpoint:
    def __init__(self, service: ReservationService, availability: AvailabilityQueries):
        self.service = service
        self.availability = availability

    def _body(self, request):
        try:
            data = json.loads(request.body)
        except (JSONDecodeError, UnicodeDecodeError):
            raise ReservationError('invalid_input', 'Request body must be valid JSON.')
        if not isinstance(data, dict):
            raise ReservationError('invalid_input', 'Request body must be a JSON object.')
        return data

    def _resource_id(self, data):
        value = data.get('resource_id')
        if isinstance(value, bool) or not isinstance(value, (str, int)):
            raise ReservationError('invalid_input', 'resource_id must be an integer.')
        try:
            value = int(value)
        except ValueError:
            raise ReservationError('invalid_input', 'resource_id must be an integer.')
        if not 0 < value <= 2**63 - 1:
            raise ReservationError('invalid_input', 'resource_id must be a positive integer.')
        return value

    def _interval(self, data):
        values = (data.get('starts_at', ''), data.get('ends_at', ''))
        if not all(isinstance(value, str) for value in values):
            raise ReservationError('invalid_input', 'Use ISO 8601 start and end datetimes.')
        try:
            start, end = (parse_datetime(value) for value in values)
        except ValueError:
            raise ReservationError('invalid_input', 'Use valid ISO 8601 start and end datetimes.')
        if start is None or end is None:
            raise ReservationError('invalid_input', 'Use ISO 8601 start and end datetimes.')
        if not timezone.is_aware(start) or not timezone.is_aware(end):
            raise ReservationError('invalid_input', 'Datetimes must include a timezone.')
        return TimeInterval(start, end)

    def _result(self, reservation, status=200):
        return JsonResponse({
            'id': reservation.id, 'status': reservation.status,
            'resource_id': reservation.resource.id,
            'starts_at': reservation.interval.start.isoformat(),
            'ends_at': reservation.interval.end.isoformat(),
        }, status=status)

    def _run(self, operation, invalid_interval_status=409):
        try:
            return operation()
        except ReservationError as error:
            status = {
                'unauthenticated': 401, 'forbidden': 403, 'not_found': 404,
                'invalid_input': 400, 'invalid_interval': invalid_interval_status,
                'conflict': 409, 'expired': 409,
            }[error.code]
            body = {'error': str(error)}
            if error.state is not None:
                body['status'] = error.state
            return JsonResponse(body, status=status)

    def create(self, request):
        def operation():
            actor = self.service.identity.authenticate(request.user)
            data = self._body(request)
            reservation = self.service.create(self._resource_id(data), self._interval(data), actor)
            return self._result(reservation, 201)
        return self._run(operation, invalid_interval_status=400)

    def check_availability(self, request):
        def operation():
            self.service.identity.authenticate(request.user)
            available = self.availability.check(
                self._resource_id(request.GET), self._interval(request.GET),
            )
            return JsonResponse({'availability': 'AVAILABLE' if available else 'UNAVAILABLE'})
        return self._run(operation, invalid_interval_status=400)

    def confirm(self, request, reservation_id):
        def operation():
            actor = self.service.identity.authenticate(request.user)
            return self._result(self.service.confirm(reservation_id, actor))
        return self._run(operation)

    def approve(self, request, reservation_id):
        def operation():
            actor = self.service.identity.authenticate(request.user)
            self.service.identity.require_approver(actor)
            decision = self._body(request).get('decision')
            if decision not in ('approve', 'reject'):
                raise ReservationError('invalid_input', "decision must be 'approve' or 'reject'.")
            return self._result(self.service.approve(reservation_id, actor, decision))
        return self._run(operation)

    def cancel(self, request, reservation_id):
        def operation():
            actor = self.service.identity.authenticate(request.user)
            return self._result(self.service.cancel(reservation_id, actor))
        return self._run(operation)
