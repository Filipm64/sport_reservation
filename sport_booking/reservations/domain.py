"""Reservation values and local state transitions, independent of HTTP and ORM."""
from dataclasses import dataclass
from datetime import datetime, time


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
class ResourceListing:
    id: int
    name: str
    sport_name: str
    location: str
    opens_at: str
    closes_at: str
    is_available: bool
    requires_approval: bool


@dataclass(frozen=True)
class ReservationListing:
    id: int
    resource_name: str
    location: str
    starts_at: datetime
    ends_at: datetime
    status: str
    username: str


@dataclass(frozen=True)
class Resource:
    id: int
    is_available: bool
    requires_approval: bool
    opens_at: time
    closes_at: time


@dataclass(frozen=True)
class TimeInterval:
    start: datetime
    end: datetime

    def overlaps(self, other):
        return self.start < other.end and other.start < self.end


@dataclass(frozen=True)
class HourBlock:
    key: str
    start: datetime
    end: datetime
    label: str
    available: bool
    reason: str


@dataclass(frozen=True)
class ApprovalRequest:
    requested_at: datetime

    def deadline(self, interval):
        return interval.start


@dataclass
class Reservation:
    id: int | None
    user_id: int
    resource: Resource
    interval: TimeInterval
    status: str
    approval_request: ApprovalRequest | None = None

    def is_pending(self):
        return self.status == 'PENDING_APPROVAL'

    def _transition(self, sources, target):
        if self.status not in sources:
            raise ReservationError('conflict', 'Reservation cannot change from this state.')
        self.status = target

    def confirm(self):
        self._transition(('PENDING_APPROVAL',), 'CONFIRMED')

    def reject(self):
        self._transition(('PENDING_APPROVAL',), 'REJECTED')

    def cancel(self):
        self._transition(('PENDING_APPROVAL', 'CONFIRMED'), 'CANCELLED')

    def expire(self):
        self._transition(('PENDING_APPROVAL',), 'EXPIRED')
