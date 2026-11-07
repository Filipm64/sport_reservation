# H1 — Návrhový sekvenční diagram

Dvě žádosti X a Y stejného sportoviště mají překrývající se interval a vznikly rovnou jako `PENDING_APPROVAL`. Správce schválí X.

```mermaid
sequenceDiagram
    actor Admin as Správce
    participant API as Vstupní rozhraní
    participant Service as ReservationService
    participant Store as DataStore
    participant Rules as TimeRules
    Admin->>API: approve(X)
    API->>Service: approve(X, actor, approve)
    Service->>Service: require_approver(actor)
    Service->>Store: load_protected(X)
    Store-->>Service: X a sportoviště; ochrana proti souběhu
    Service->>Rules: now(), is_expired(X, now)
    alt Dosažen začátek
        Service->>Service: X.expire()
        Service->>Store: save(X), commit()
        Service-->>API: expired; stav EXPIRED
    else Platná čekající žádost
        Service->>Rules: validate_approval(X, now)
        Service->>Store: confirmed_intervals(resource)
        Store-->>Service: potvrzené intervaly
        Service->>Rules: has_conflict(interval, intervals)
        alt Sportoviště nedostupné nebo kolize
            Service->>Store: rollback()
            Service-->>API: conflict
        else Bez kolize
            Service->>Service: X.confirm()
            Service->>Store: save(X)
            Service->>Store: overlapping_pending_ids(X)
            Store-->>Service: Y a další překrývající se čekající žádosti
            loop Každý konkurent
                Service->>Store: load_protected(id)
                Service->>Service: competing.reject()
                Service->>Store: save(competing)
            end
            Service->>Store: commit()
            Service-->>API: X CONFIRMED; konkurenti REJECTED
        end
    end
    API-->>Admin: Výsledek
```

Pozdější nebo souběžné Approve Y uvidí `REJECTED` a vrátí 409. Nemůže obnovit žádost. Pokud kterékoli uložení selže, vrátí se celá transakce včetně změny X a všech konkurentů.

Create bez schvalování používá stejnou kontrolu dostupnosti a stejnou proceduru zamítnutí konkurentů. SQLite IMMEDIATE získává ochranu před prvním chráněným čtením; ochrana platí mezi požadavky i procesy.

[Statická architektura](../architecture/static-structure.md) · [Třídy](design-classes.md) · [Ověření souběhu](../verification/coverage.md#req-04)
