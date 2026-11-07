# H2 — Zaměřený návrhový třídní diagram

```mermaid
classDiagram
    class ReservationService {
        +create(resource_id, interval, actor)
        +approve(reservation_id, actor, decision)
        +cancel(reservation_id, actor)
        +expire_due()
        -_decide_confirmation(reservation, store, now)
        -_reject_competing_requests(winner, store)
    }
    class Reservation {
        +status
        +confirm()
        +reject()
        +cancel()
        +expire()
    }
    class DataStore {
        <<interface>>
        +load_resource(id, protected)
        +load_protected(id)
        +confirmed_intervals(resource_id)
        +overlapping_pending_ids(winner)
        +save(reservation)
        +commit()
        +rollback()
    }
    class DjangoDataStore
    class TimeRules {
        +now()
        +validate_interval(interval, now)
        +validate_approval(reservation, now)
        +is_expired(reservation, now)
        +has_conflict(interval, intervals)
    }
    class IdentityAccess {
        +authenticate(session_user)
        +require_owner(actor, reservation)
        +require_approver(actor)
    }
    ReservationService --> Reservation
    ReservationService --> TimeRules
    ReservationService --> IdentityAccess
    ReservationService --> DataStore
    DjangoDataStore ..|> DataStore
```

## Vlastníci operací z H1

| Část | Odpovědnost |
| --- | --- |
| Vstupní rozhraní | Validuje transportní vstupy a identifikuje aktéra |
| ReservationService | Volí počáteční stav, kontroluje dostupnost a kolize, řídí schválení a zamítnutí konkurentů |
| Reservation | Vynucuje povolené přechody jednoho objektu |
| TimeRules | Časová pravidla, polouzavřené intervaly a expirace při začátku |
| DataStore / DjangoDataStore | Chráněné čtení, výběr konkurentů a transakční uložení |

## Důležité smlouvy

Create i Approve mají vlastní kontext ukládání a společnou kontrolu `_decide_confirmation()`. Při vzniku `CONFIRMED` následuje `_reject_competing_requests()` před `commit()`. Výběr konkurentů používá stejné sportoviště, stav `PENDING_APPROVAL` a polouzavřený překryv. Vítěz je z výběru vyloučen.

`Reservation.confirm()` lze volat pouze na `PENDING_APPROVAL`. Automaticky potvrzená rezervace vzniká rovnou v cílovém stavu. Veřejná metoda `ReservationService.confirm()` ani odpovídající HTTP operace neexistují.

## Mapování na realizovaný kód

[Generované vazby na konkrétní symboly a testy](../verification/coverage.md) · [Sekvence](approval-sequence.md) · [Doménový model](domain-model.md)
