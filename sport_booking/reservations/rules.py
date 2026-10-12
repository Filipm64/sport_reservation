from datetime import timedelta

from django.utils import timezone

from .domain import ReservationError


class TimeRules:
    def now(self):
        return timezone.now()

    def validate_interval(self, interval, now):
        error = None
        if interval.start >= interval.end:
            error = 'End must be after start.'
        elif interval.start < now:
            error = 'Reservation cannot start in the past.'
        elif interval.start > now + timedelta(days=30):
            error = 'Reservation cannot start more than 30 days ahead.'
        elif interval.end - interval.start > timedelta(hours=2):
            error = 'Reservation cannot be longer than 2 hours.'
        if error:
            raise ReservationError('invalid_interval', error)

    def is_expired(self, reservation, now):
        return reservation.is_pending() and (
            reservation.approval_request is None
            or now >= reservation.approval_request.deadline(reservation.interval)
        )

    def validate_approval(self, reservation, now):
        self.validate_interval(reservation.interval, now)

    def has_conflict(self, interval, confirmed_intervals):
        return any(interval.overlaps(existing) for existing in confirmed_intervals)

    def validate_cancellation(self, reservation, now):
        if now >= reservation.interval.start:
            raise ReservationError('conflict', 'Reservation has already started.')
