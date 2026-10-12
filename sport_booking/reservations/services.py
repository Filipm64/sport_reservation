from .domain import Reservation, ReservationError
from .identity import IdentityAccess
from .persistence import DataStore
from .rules import TimeRules


class ReservationService:
    def __init__(self, store_factory, rules=None, identity=None):
        self.store_factory = store_factory
        self.rules = rules or TimeRules()
        self.identity = identity or IdentityAccess(store_factory)

    def create(self, resource_id, interval, actor):
        with self.store_factory() as store:
            resource = store.load_resource(resource_id, protected=True)
            self.rules.validate_interval(interval, self.rules.now())
            reservation = Reservation(None, actor.id, resource, interval)
            store.save(reservation)
            store.commit()
            return reservation

    def _decide_confirmation(self, reservation, store: DataStore, now):
        if reservation.is_pending():
            self.rules.validate_approval(reservation, now)
        else:
            self.rules.validate_interval(reservation.interval, now)
        if not reservation.resource.is_available:
            raise ReservationError('conflict', 'Resource is unavailable.')
        if self.rules.has_conflict(
            reservation.interval, store.confirmed_intervals(reservation.resource.id),
        ):
            raise ReservationError('conflict', 'Reservation interval is already taken.')

    def _expire_if_due(self, reservation, store: DataStore, now):
        if self.rules.is_expired(reservation, now):
            reservation.expire()
            store.save(reservation)
            store.commit()
            # The expiry is committed even though the requested action is refused.
            raise ReservationError('expired', 'Approval request expired.', reservation.status)

    def confirm(self, reservation_id, actor):
        with self.store_factory() as store:
            reservation = store.load_protected(reservation_id)
            self.identity.require_owner(actor, reservation)
            if reservation.status != 'DRAFT':
                raise ReservationError('conflict', 'Only DRAFT reservations can be confirmed.')
            now = self.rules.now()
            self._decide_confirmation(reservation, store, now)
            if reservation.resource.requires_approval:
                reservation.request_approval(now)
            else:
                reservation.confirm()
            store.save(reservation)
            store.commit()
            return reservation

    def approve(self, reservation_id, actor, decision='approve'):
        self.identity.require_approver(actor)
        with self.store_factory() as store:
            reservation = store.load_protected(reservation_id)
            if not reservation.is_pending():
                raise ReservationError('conflict', 'Reservation is not awaiting approval.')
            now = self.rules.now()
            self._expire_if_due(reservation, store, now)
            if decision == 'reject':
                reservation.reject()
            elif decision == 'approve':
                self._decide_confirmation(reservation, store, now)
                reservation.confirm()
            else:
                raise ReservationError('invalid_input', "decision must be 'approve' or 'reject'.")
            store.save(reservation)
            store.commit()
            return reservation

    def cancel(self, reservation_id, actor):
        with self.store_factory() as store:
            reservation = store.load_protected(reservation_id)
            self.identity.require_owner(actor, reservation)
            now = self.rules.now()
            self._expire_if_due(reservation, store, now)
            self.rules.validate_cancellation(reservation, now)
            reservation.cancel()
            store.save(reservation)
            store.commit()
            return reservation

    def expire_due(self):
        with self.store_factory() as store:
            ids = store.pending_ids()
            count = 0
            for reservation_id in ids:
                reservation = store.load_protected(reservation_id)
                if self.rules.is_expired(reservation, self.rules.now()):
                    reservation.expire()
                    store.save(reservation)
                    count += 1
            store.commit()
            return count


class AvailabilityQueries:
    def __init__(self, store_factory, rules=None):
        self.store_factory = store_factory
        self.rules = rules or TimeRules()

    def check(self, resource_id, interval):
        self.rules.validate_interval(interval, self.rules.now())
        with self.store_factory() as store:
            resource = store.load_resource(resource_id)
            return resource.is_available and not self.rules.has_conflict(
                interval, store.confirmed_intervals(resource_id),
            )
