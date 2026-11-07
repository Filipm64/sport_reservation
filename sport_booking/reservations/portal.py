"""Read-only queries used to build the customer and staff portal."""
from dataclasses import replace

from .rules import TimeRules


class PortalQueries:
    def __init__(self, store_factory, rules=None):
        self.store_factory = store_factory
        self.rules = rules or TimeRules()

    def resources(self):
        with self.store_factory() as store:
            return store.list_resources()

    def reservations_for_user(self, user_id, now):
        with self.store_factory() as store:
            reservations = store.list_reservations(user_id=user_id)
        return [replace(row, status=self.rules.display_status(row, now))
                for row in reservations]

    def pending_reservations(self, now):
        with self.store_factory() as store:
            return store.list_pending_reservations(now)

    def hourly_schedule(self, resource_id, day, now):
        with self.store_factory() as store:
            resource = store.load_resource(resource_id)
            confirmed = store.confirmed_intervals(resource_id)
        return self.rules.hourly_blocks(day, now, resource, confirmed)

    def weekly_schedule(self, resource_id, day, now):
        with self.store_factory() as store:
            resource = store.load_resource(resource_id)
            confirmed = store.confirmed_intervals(resource_id)
        return self.rules.weekly_blocks(day, now, resource, confirmed)
