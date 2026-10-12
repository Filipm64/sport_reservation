# J — AS-IS → TO-BE delta

**Datum:** 12. 10. 2026. AS-IS zachycuje stav před implementací,
z výchozího commitu `acd7890` (C03 A–E3). Vychází z tehdejších
[views](../sport_booking/reservations/views.py),
[modelů](../sport_booking/reservations/models.py) a
[expiračního příkazu](../sport_booking/reservations/management/commands/expire_reservations.py).
Samostatný zápis Part A v repozitáři není; používáme nálezy z prohlídky kódu
a [evidence C02](evidence-and-evolution.md).
TO-BE odpovídá přijatým diagramům [G2](static-architecture.md),
[G3](statechart-ownership.md), [G4](runtime-deployment.md),
[H1](design-sequence.md) a [H2](design-classes.md).

| Oblast | AS-IS | TO-BE | Akce |
| :--- | :--- | :--- | :--- |
| Vstupní rozhraní | View funkce parsují HTTP, vyhodnocují pravidla i zapisují přes ORM. | Vstup pouze převede požadavek, předá identitu a zavolá vlastníka operace; výsledek převede na HTTP odpověď. | `CHANGE` |
| Změna stavu rezervace | `status` přímo přepisují Confirm, Approve, Cancel, `_expire_if_due()` a expirační příkaz. | Přechod rozhodne Správa rezervací; stav objektu mění její doménové operace. Ukládání pouze uloží výsledek. | `CHANGE` |
| Potvrzení a kontrola kolize | Confirm a Approve opakují kontrolu času, dostupnosti a přechod do CONFIRMED; sdílejí jen pomocné funkce. | `ReservationService.confirm()` a `approve()` sdílejí `_decide_confirmation()`. Rozhodnutí proběhne v chráněném kontextu podle H1/H2. | `CHANGE` |
| Časová pravidla a hodnoty | `_interval_error()` a timeout jsou ve views; expirace má další podmínky v commandu. Interval a čas žádosti jsou plochá pole. | Společné `TimeRules`, `TimeInterval` a `ApprovalRequest` vyjadřují stejné hranice. Čas pro změnu stavu se odečte po získání ochrany. | `CHANGE` |
| Oprávnění | Kontroly přihlášení, `is_staff` a filtrování podle vlastníka jsou ve views. | `IdentityAccess` vlastní pravidla oprávnění; služba je použije před změnou. Stávající uživatelské účty a role lze zachovat. | `CHANGE` |
| Závislost na ukládání | Views i command volají ORM přímo a spojují business pravidla s databázovými dotazy. | `DataStore` oddělí chráněné načtení, dotaz na potvrzené intervaly a uložení. Každá operace má vlastní kontext; HTTP vstup přímo nezapisuje. | `CHANGE` |
| Dotaz na dostupnost | `check_availability()` ve views používá ORM a `_has_conflict()`; nic nezapisuje. | Logiku vlastní Dotazy na dostupnost, které používají Časová pravidla a čtecí část ukládání. Význam AVAILABLE/UNAVAILABLE zůstane stejný. | `CHANGE` |
| Vstup pro expiraci | Command importuje timeout z views a přímo provádí hromadnou změnu na EXPIRED. | Command pouze spustí `ReservationService.expire_due()`; deadline a přechody mají stejné vlastníky jako v API. | `CHANGE` |
| Uložená data a migrace | Modely obsahují vlastníka, Resource, interval, stav, čas vytvoření a čas žádosti; SQLite data zachovává po restartu. | Zachovat pole, vazby, stavové hodnoty a migrace. TimeInterval/ApprovalRequest nemusí mít vlastní tabulky. | `KEEP` |
| Vnější API a rezervační admin | Existují cesty a JSON operace z baseline; rezervační admin neumožňuje tvorbu, přepis ani smazání. | Zachovat vnější smlouvu API a omezení adminu; změnit pouze vnitřní delegování operací. | `KEEP` |
| Nasazení | Jedna Django aplikace, webový proces a ručně spouštěný expirační command nad stejným SQLite souborem. | Stejné nasazení podle ADR-01/G4; logické části nejsou samostatné služby. | `KEEP` |
| Ochrana souběhu a selhání zápisu | SQLite používá IMMEDIATE; existuje pět testů souběhu přes nezávislá spojení. Budoucí DataStore zatím není implementovaný. | Při přesunu zachovat záruku BR-02. Ověřit izolaci kontextů, rollback při chybě a souběh webu s expirací také mezi procesy. | `VERIFY` |
| Zachování chování po úpravách | Existují API, časové a souběžné testy; cílové rozdělení kódu jimi ještě ověřené není. | Po změnách spustit všechny dosavadní testy včetně souborové DB a ověřit, že kód používá pouze závislosti povolené v G2. | `VERIFY` |

## Jak tabulku použít

`CHANGE` označuje konkrétní rozdíl ve struktuře kódu. `KEEP` zachovává
stávající chování, data nebo nasazení; neznamená, že se nesmí přesunout kód.
`VERIFY` je kontrola zachovaných záruk při přesunu, nikoliv tvrzení,
že cílové třídy již existují.

Nejdříve vytvořit společná pravidla a rozhraní ukládání, potom přesunout
rozhodování do Správy rezervací a přepojit HTTP vstupy i expiraci.
Nakonec ověřit chování a povolené závislosti. Business pravidla se tímto
krokem nemění; automatický plánovač expirace zůstává nedořešený podle G4.

## Následná realizace

Všech osm položek CHANGE bylo provedeno: nové `api.py`, `services.py`,
`identity.py`, `rules.py`, `domain.py`, `persistence.py` a přepojení commandu.
`wiring.py` propojuje části při spuštění bez business rozhodování.
Položky KEEP zůstaly zachované; schéma ani migrace se nezměnily.
VERIFY bylo ověřeno 36 testy včetně pěti souběhů mezi spojeními,
expirace v samostatném procesu, simulovaného selhání zápisu/commit a kontroly
povolených importů. Podrobnosti jsou v evidenci C03.
