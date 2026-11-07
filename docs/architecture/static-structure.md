# G2 — TO-BE statická architektura

Návrh rozděluje [odpovědnosti](responsibilities.md) do sedmi logických
částí. Podle [ADR-01](decisions/ADR-001-reservation-coordination.md) jsou všechny součástí jedné
rezervační aplikace; nevzniká samostatná rezervační služba.

```mermaid
flowchart TB
    subgraph system["Reservation System"]
        subgraph app["Rezervační aplikace — varianta A z ADR-01"]
            entry["Vstupní rozhraní<br/>API a webové rozhraní<br/>role: přijmout požadavek, vrátit výsledek"]
            auth["Identita a oprávnění<br/>role: přihlášení a povolení operace<br/>owns: identity a schvalovací oprávnění"]
            reservations["Správa rezervací<br/>role: vytvoření, potvrzení, schválení, zrušení, expirace<br/>owns: životní cyklus Reservation, ApprovalRequest a invariant BR-02"]
            facilities["Správa sportovišť — ResourceService<br/>role: konfigurace provozní doby"]
            availability["Čtecí dotazy<br/>AvailabilityQueries, PortalQueries<br/>role: dostupnost, katalog a přehledy bez zápisu"]
            time["Časová pravidla<br/>role: intervaly, překryv a časové hranice<br/>owns: společný význam času a intervalů"]
            storage["Ukládání dat<br/>role: načtení a spolehlivé uložení<br/>owns: trvalé záznamy a ochrana souběžného zápisu"]

            entry -->|"přihlášení / ověření identity"| auth
            entry -->|"Create, Approve, Cancel; systémový vstup pro expiraci"| reservations
            entry -->|"Check Availability; veřejný katalog; vlastní rezervace; fronta správce"| availability
            entry -->|"nastavit provozní dobu"| facilities
            facilities -->|"ověřit oprávnění správce"| auth
            facilities -->|"ověřit platnost doby"| time
            facilities -->|"chráněné načtení a atomický zápis doby"| storage
            reservations -->|"ověřit vlastníka / pravomoc správce"| auth
            reservations -->|"ověřit interval, překryv, začátek a deadline"| time
            availability -->|"ověřit interval, překryv a zobrazenou platnost"| time
            reservations -->|"chráněné načtení stavu a kolizí / uložení změny"| storage
            availability -->|"pouze číst katalog, rezervace a potvrzené intervaly"| storage
            auth -->|"načíst identitu / uložit přihlašovací údaje a oprávnění"| storage
        end
    end
```

Šipky označují povolená volání; výsledek se vrací volajícímu.
Externí systémy nyní nepoužíváme. Lidské aktéry zachycuje
[kontext G1](system-context.md).

## Hlavní vlastník každé odpovědnosti

| Odpovědnost | Jediný hlavní vlastník |
| --- | --- |
| ODP-01 — přijetí požadavku a odpověď | Vstupní rozhraní |
| ODP-02 — oprávnění k operaci | Identita a oprávnění |
| ODP-03 — časová pravidla | Časová pravidla |
| ODP-04 — životní cyklus rezervace | Správa rezervací |
| ODP-05 — rozhodnutí o alokaci a exkluzivita | Správa rezervací |
| ODP-06 — informace o dostupnosti | Čtecí dotazy |
| ODP-07 — čekající schvalování | Správa rezervací |
| ODP-08 — trvalé uložení a obnova | Ukládání dat |

## Důležité hranice

- **Správa rezervací rozhoduje.** Create i Approve používají stejnou
  kontrolu kolize a přechod na CONFIRMED. Cancel i expirace mění tentýž
  životní cyklus; nikdo jiný rezervaci přímo nepřepisuje.
- **Ukládání dat zajišťuje ochranu rozhodnutí.** Správa rezervací načte
  aktuální stav, vyhodnotí pravidla a uloží změnu v jedné chráněné operaci.
  Jiný požadavek nesmí mezi kontrolou a uložením potvrdit kolidující interval.
  Business pravidla vlastní Správa rezervací, technické uložení Ukládání dat.
  Každý požadavek má vlastní kontext ukládání; ochrana proti kolizím je
  společná i mezi procesy. Čas pro rozhodnutí se odečte až po získání ochrany.
- **Dostupnost je pouze dotaz.** Výsledek AVAILABLE není souhlas s pozdějším
  potvrzením. Dotaz sdílí časová pravidla, ale nic nezapisuje; Správa rezervací
  při potvrzení kontroluje aktuální kolize znovu.
- **Vstupy pravidla neobcházejí.** Ověřují přihlášení; Správa rezervací
  navíc žádá o kontrolu vlastnictví nebo schvalovacího oprávnění. Expirace
  používá důvěryhodný systémový vstup a stejné přechody jako ostatní operace.

Plánované spouštění expirace pouze vyvolá tento systémový vstup; neurčuje
pravidla vypršení. Správa katalogu Sport/Resource není v tomto rezervačním
slice rozkreslená. Logické rozdělení je nyní realizované v kódu; mapování tříd na soubory
je v H2. Automatické spouštění expirace zůstává provozním úkolem.

Webový vstup v `reservations/web_views.py` navíc skládá read-only přehled
pro zákazníka a správce prostřednictvím `PortalQueries`. Čtení katalogu a
rezervací vede přes `DataStore`; změny životního cyklu nadále provádí pouze
`ReservationService`. Registrace vytváří běžného Django uživatele a
nepřiděluje `is_staff`.

## Rozšíření webového portálu — REQ-07 až REQ-11

Čtecí dotazy zahrnují `AvailabilityQueries` pro dostupnost a `PortalQueries` pro katalog, vlastní rezervace a frontu správce. Ověření rolí a identity provádí vstupní webové rozhraní podle Django session. `TimeRules.display_status` určuje platnost zobrazené čekající žádosti bez změny uloženého stavu. Datový adaptér pouze vybírá a načítá údaje.

Registraci a relace realizuje část Identita a oprávnění prostřednictvím Django UserCreationForm, LoginView a LogoutView; konkrétní vstupní třídy jsou v `web_views.py`. Přímý ORM přístup z webových vstupů zůstává zakázaný.

[Kontrakty a sekvence portálu](../design/web-portal.md) · [Prokliky REQ-07 až REQ-11](../verification/coverage.md#req-07)

## Provozní doba — REQ-13

`ResourceService` vlastní změnu konfigurace sportoviště. `ReservationService` vlastní rozhodnutí o rezervaci a před alokací ověřuje aktuální provozní dobu přes TimeRules. Obě služby používají stejné porty a transakční ochranu. [Kontrakty a implementační vazby](../requirements/operating-hours.md).
