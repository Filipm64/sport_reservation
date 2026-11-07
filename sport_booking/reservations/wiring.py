"""Runtime assembly of the logical G2 parts; no business decisions here."""
from .api import ReservationEndpoint
from .identity import IdentityAccess
from .persistence import DjangoDataStore
from .portal import PortalQueries
from .rules import TimeRules
from .services import AvailabilityQueries, ReservationService, ResourceService


def build_service():
    return ReservationService(DjangoDataStore, TimeRules(), IdentityAccess(DjangoDataStore))


def build_endpoint():
    service = build_service()
    availability = AvailabilityQueries(DjangoDataStore, service.rules)
    return ReservationEndpoint(service, availability)


def build_portal_queries():
    return PortalQueries(DjangoDataStore, TimeRules())


def build_resource_service():
    return ResourceService(DjangoDataStore, TimeRules(), IdentityAccess(DjangoDataStore))
