from .domain import ApprovalRequest, Reservation, ReservationError
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
            now = self.rules.now()
            reservation = Reservation(
                None, actor.id, resource, interval,
                'PENDING_APPROVAL' if resource.requires_approval else 'CONFIRMED',
                ApprovalRequest(now) if resource.requires_approval else None,
            )
            self._decide_confirmation(reservation, store, now)
            store.save(reservation)
            if reservation.status == 'CONFIRMED':
                self._reject_competing_requests(reservation, store)
            store.commit()
            return reservation

    def _reject_competing_requests(self, winner, store: DataStore):
        for reservation_id in store.overlapping_pending_ids(winner):
            competing = store.load_protected(reservation_id)
            competing.reject()
            store.save(competing)

    def _decide_confirmation(self, reservation, store: DataStore, now):
        if reservation.is_pending():
            self.rules.validate_approval(reservation, now)
        else:
            self.rules.validate_interval(reservation.interval, now)
        if not reservation.resource.is_available:
            raise ReservationError('conflict', 'Resource is unavailable.')
        self.rules.validate_resource_hours(reservation.interval, reservation.resource)
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
            if reservation.status == 'CONFIRMED':
                self._reject_competing_requests(reservation, store)
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
            return (resource.is_available
                    and self.rules.is_within_operating_hours(interval, resource)
                    and not self.rules.has_conflict(
                interval, store.confirmed_intervals(resource_id),
            ))


class ResourceService:
    def __init__(self, store_factory, rules=None, identity=None):
        self.store_factory = store_factory
        self.rules = rules or TimeRules()
        self.identity = identity or IdentityAccess(store_factory)

    def update_operating_hours(self, resource_id, actor, opens_at, closes_at):
        self.identity.require_approver(actor)
        self.rules.validate_operating_hours(opens_at, closes_at)
        with self.store_factory() as store:
            store.load_resource(resource_id, protected=True)
            store.set_operating_hours(resource_id, opens_at, closes_at)
            store.commit()
