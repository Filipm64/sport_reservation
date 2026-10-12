from .domain import ReservationError


class IdentityAccess:
    def __init__(self, store_factory):
        self.store_factory = store_factory

    def authenticate(self, session_user):
        if not session_user.is_authenticated:
            raise ReservationError('unauthenticated', 'Authentication required.')
        with self.store_factory() as store:
            return store.load_user(session_user.pk)

    def can_approve(self, actor):
        return actor.approval_permission

    def require_owner(self, actor, reservation):
        if actor.id != reservation.user_id:
            # Preserve the existing API policy: do not expose another user's reservation.
            raise ReservationError('not_found', 'Reservation not found.')

    def require_approver(self, actor):
        if not self.can_approve(actor):
            raise ReservationError('forbidden', 'Only a staff user can decide approval.')
