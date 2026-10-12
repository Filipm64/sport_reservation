# H1 — Návrhový sekvenční diagram

Používáme [stejný scénář](architecture-decision.md#průchod-scénářem--dvě-současná-schválení):
dvě žádosti X a Y o stejné sportoviště a interval. Po Create a Confirm
jsou obě PENDING_APPROVAL; původní požadavky už skončily.
Později je dva oprávnění správci schválí současně, před deadline.
Sportoviště je dostupné a nemá jinou potvrzenou rezervaci.

Diagram realizuje variantu A z ADR-01 pomocí prvků [G2](static-architecture.md).

```mermaid
%%{init: {"sequence": {"actorMargin": 25, "mirrorActors": false, "wrap": true}}}%%
sequenceDiagram
    actor SX as Správce X
    actor SY as Správce Y
    participant V as Vstupní<br/>rozhraní
    participant I as Identita<br/>a oprávnění
    participant R as Správa<br/>rezervací
    participant T as Časová<br/>pravidla
    participant U as Ukládání<br/>dat

    Note over R,U: X a Y jsou uložené<br/>jako PENDING_APPROVAL.
    par Schválení X
        SX->>V: Approve(X)
        V->>I: Ověř přihlášení
        I-->>V: Identita správce X
        V->>R: Schval X
    and Schválení Y
        SY->>V: Approve(Y)
        V->>I: Ověř přihlášení
        I-->>V: Identita správce Y
        V->>R: Schval Y
    end

    loop Pro každý požadavek — v ukázce X, pak Y
        R->>U: load_protected(id)<br/>ochrana před načtením
        U-->>R: Rezervace a její Resource
        R->>U: confirmed_intervals(resourceId)
        U-->>R: Aktuální potvrzené intervaly
        R->>I: Smí aktér schvalovat?
        I-->>R: Ano
        R->>T: now()
        T-->>R: Aktuální serverový čas
        R->>T: validate_approval()<br/>a has_conflict()
        T-->>R: Platný čas<br/>a výsledek překryvu
        R->>R: Ověř čekající stav<br/>a _decide_confirmation()

        alt Bez kolize — X
            R->>R: Reservation.confirm()
            R->>U: save() a commit()
            U-->>R: Změna uložená
            R-->>V: X potvrzena
            V-->>SX: 200, CONFIRMED
        else Kolize s X — Y
            R->>U: rollback()<br/>bez změny stavu
            U-->>R: Y zůstává čekající
            R-->>V: Y odmítnuta kvůli kolizi
            V-->>SY: 409, konflikt
        end
    end
```

**Rozhoduje Správa rezervací.** Ukládání dat chrání její kontrolu a zápis
před jiným potvrzením. Y se načítá až po dokončení změny X, takže nesmí
rozhodovat podle starého stavu „volno“. Vítězem může být i Y; pořadí X → Y
je pouze příklad. Při více instancích aplikace musí ochrana platit také
mezi nimi.

Všechny vnitřní lifelines i jejich volání odpovídají G2. Správci jsou dvě
instance role z kontextu G1. Dotazy na dostupnost nejsou pro rozhodnutí
potřeba: předchozí AVAILABLE by potvrzení nezaručovalo.
Jde o návrh cílové spolupráce částí, nikoliv nový diagram současných view funkcí.

Načtení rezervace a načtení potvrzených intervalů jsou dvě operace stejného
chráněného kontextu. Čas se odečítá až po získání ochrany. Změnu objektu
`Reservation.confirm()` vyvolá Správa rezervací; Ukládání dat pouze uloží
výsledek. `_decide_confirmation()` je společná kontrola dostupného Resource
a kolize pro Confirm i Approve, jak požaduje ADR-01.
