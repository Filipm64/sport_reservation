"""Reservation values and local state transitions, independent of HTTP and ORM."""
from dataclasses import dataclass
from datetime import datetime, timedelta


class ReservationError(Exception):
    def __init__(self, code, message, state=None):
        super().__init__(message)
        self.code = code
        self.state = state


@dataclass(frozen=True)
class User:
    id: int
    approval_permission: bool


@dataclass(frozen=True)
class Resource:
    id: int
    is_available: bool
    requires_approval: bool


@dataclass(frozen=True)
class TimeInterval:
    start: datetime
    end: datetime

    def overlaps(self, other):
        return self.start < other.end and other.start < self.end


@dataclass(frozen=True)
class ApprovalRequest:
    requested_at: datetime

    def deadline(self, interval):
        return min(self.requested_at + timedelta(hours=24), interval.start)


@dataclass
class Reservation:
    id: int | None
    user_id: int
    resource: Resource
    interval: TimeInterval
    status: str = 'DRAFT'
    approval_request: ApprovalRequest | None = None

    def is_pending(self):
        return self.status == 'PENDING_APPROVAL'

    def _transition(self, sources, target):
        if self.status not in sources:
            raise ReservationError('conflict', 'Reservation cannot change from this state.')
        self.status = target

    def request_approval(self, now):
        self._transition(('DRAFT',), 'PENDING_APPROVAL')
        self.approval_request = ApprovalRequest(now)

    def confirm(self):
        self._transition(('DRAFT', 'PENDING_APPROVAL'), 'CONFIRMED')

    def reject(self):
        self._transition(('PENDING_APPROVAL',), 'REJECTED')

    def cancel(self):
        self._transition(('DRAFT', 'PENDING_APPROVAL', 'CONFIRMED'), 'CANCELLED')

    def expire(self):
        self._transition(('PENDING_APPROVAL',), 'EXPIRED')
