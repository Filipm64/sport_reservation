"""Read-only queries used to build the customer and staff portal."""


class PortalQueries:
    def __init__(self, store_factory):
        self.store_factory = store_factory

    def resources(self):
        with self.store_factory() as store:
            return store.list_resources()

    def reservations_for_user(self, user_id):
        with self.store_factory() as store:
            return store.list_reservations(user_id=user_id)

    def pending_reservations(self):
        with self.store_factory() as store:
            return store.list_reservations()
