"""Runtime assembly of the logical G2 parts; no business decisions here."""
from .api import ReservationEndpoint
from .identity import IdentityAccess
from .persistence import DjangoDataStore
from .rules import TimeRules
from .services import AvailabilityQueries, ReservationService


def build_service():
    return ReservationService(DjangoDataStore, TimeRules(), IdentityAccess(DjangoDataStore))


def build_endpoint():
    service = build_service()
    availability = AvailabilityQueries(DjangoDataStore, service.rules)
    return ReservationEndpoint(service, availability)
