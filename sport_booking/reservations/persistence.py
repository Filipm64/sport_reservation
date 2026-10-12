"""Request-scoped persistence port and its Django/SQLite adapter."""
from typing import Protocol

from django.contrib.auth import get_user_model
from django.db import transaction

from . import models
from .domain import ApprovalRequest, Reservation, ReservationError, Resource, TimeInterval, User


class DataStore(Protocol):
    def __enter__(self): ...
    def __exit__(self, exc_type, exc, traceback): ...
    def load_user(self, user_id) -> User: ...
    def load_protected(self, reservation_id) -> Reservation: ...
    def load_resource(self, resource_id, protected=False) -> Resource: ...
    def confirmed_intervals(self, resource_id) -> list[TimeInterval]: ...
    def pending_ids(self) -> list[int]: ...
    def save(self, reservation): ...
    def commit(self): ...
    def rollback(self): ...


class DjangoDataStore:
    def __init__(self):
        self._atomic = None
        self._rows = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        # An operation that forgot to commit must never publish a partial change.
        self.rollback()
        return False

    def _begin(self):
        if self._atomic is None:
            atomic = transaction.atomic()
            atomic.__enter__()
            self._atomic = atomic

    def load_user(self, user_id):
        try:
            user = get_user_model().objects.get(pk=user_id, is_active=True)
        except get_user_model().DoesNotExist:
            raise ReservationError('unauthenticated', 'Authentication required.')
        return User(user.pk, user.is_staff)

    def load_resource(self, resource_id, protected=False):
        if protected:
            self._begin()
        query = models.Resource.objects.all()
        if protected:
            query = query.select_for_update()
        try:
            resource = query.get(pk=resource_id)
        except models.Resource.DoesNotExist:
            raise ReservationError('not_found', 'Resource not found.')
        return Resource(resource.pk, resource.is_available, resource.requires_approval)

    def load_protected(self, reservation_id):
        self._begin()  # SQLite IMMEDIATE obtains its write lock before any state read.
        try:
            row = models.Reservation.objects.select_for_update().get(pk=reservation_id)
        except models.Reservation.DoesNotExist:
            raise ReservationError('not_found', 'Reservation not found.')
        resource = self.load_resource(row.resource_id, protected=True)
        self._rows[row.pk] = row
        return Reservation(
            row.pk, row.user_id, resource, TimeInterval(row.starts_at, row.ends_at),
            row.status,
            ApprovalRequest(row.approval_requested_at) if row.approval_requested_at else None,
        )

    def confirmed_intervals(self, resource_id):
        return [TimeInterval(start, end) for start, end in models.Reservation.objects.filter(
            resource_id=resource_id, status=models.Reservation.Status.CONFIRMED,
        ).values_list('starts_at', 'ends_at')]

    def pending_ids(self):
        self._begin()
        return list(models.Reservation.objects.filter(
            status=models.Reservation.Status.PENDING_APPROVAL,
        ).values_list('pk', flat=True))

    def save(self, reservation):
        if self._atomic is None:
            raise RuntimeError('Saving requires a protected operation.')
        requested_at = (
            reservation.approval_request.requested_at if reservation.approval_request else None
        )
        if reservation.id is None:
            row = models.Reservation.objects.create(
                user_id=reservation.user_id, resource_id=reservation.resource.id,
                starts_at=reservation.interval.start, ends_at=reservation.interval.end,
                status=reservation.status, approval_requested_at=requested_at,
            )
            reservation.id = row.pk
            self._rows[row.pk] = row
        else:
            row = self._rows[reservation.id]
            row.status = reservation.status
            row.approval_requested_at = requested_at
            row.save(update_fields=('status', 'approval_requested_at'))

    def commit(self):
        if self._atomic is None:
            raise RuntimeError('No protected operation to commit.')
        atomic, self._atomic = self._atomic, None
        try:
            atomic.__exit__(None, None, None)
        finally:
            self._rows.clear()

    def rollback(self):
        if self._atomic is not None:
            atomic, self._atomic = self._atomic, None
            try:
                transaction.set_rollback(True)
                atomic.__exit__(None, None, None)
            finally:
                self._rows.clear()
