# Hodinový rozvrh — návrh REQ-12

## Rozdělení odpovědností

| Owner | Odpovědnost |
| --- | --- |
| ScheduleFilterForm | Sportoviště a den; rozsah dnešek až +30 dní |
| PortalQueries.weekly_schedule | Načtení sportoviště a potvrzených intervalů přes DataStore; bez zápisů |
| TimeRules.weekly_blocks / hourly_blocks | Týdenní tabulka, bloky lokálních dnů, provozní doba, překryvy a časový horizont |
| HourBlock | Read-only DTO: klíč, přesný začátek, konec, popisek, dostupnost a důvod nedostupnosti |
| BookingForm.clean | Přepínač ruční / blokový vstup; přesně 1 nebo 2 unikátní navazující dostupné bloky; odvození začátku a konce na serveru |
| schedule.js | Okamžitá zpětná vazba, výběr nejvýše dvou sousedních bloků a přepínání vstupů |
| ReservationService.create | Autoritativní kontrola aktuálního intervalu a kolize, volba počátečního stavu a atomické uložení |

## Kontrakty

`PortalQueries.weekly_schedule(resource_id, day, now) -> dict` načte katalogový příznak a potvrzené intervaly sportoviště a zavolá společná časová pravidla. Nevrací jména ani identitu rezervujících zákazníků. Potvrzené intervaly se načítají jednou pro celý rozvrh, nikoli samostatně pro každý blok.

`TimeRules.hourly_blocks` převádí místní půlnoc a následující místní půlnoc do UTC a iteruje po 60 skutečných minutách. Proto zachová délku bloku i při změně letního času. Popisky jsou v Europe/Prague a v přechodových dnech obsahují UTC offset. Dostupnost používá BR-01/02/03/04/09; intervaly mají polouzavřené hranice.

`BookingForm.clean` v blokovém režimu ověřuje odeslané klíče proti znovu sestavenému rozvrhu pro odeslané sportoviště a den. Duplicitní klíč není druhá hodina. Při dvou blocích musí konec prvního být začátkem druhého. Z vybraných DTO se odvodí skutečný interval; interval zaslaný klientem v tomto režimu není zdroj pravdy.

V ručním režimu jsou začátek a konec povinné. Pro oba režimy společná služba volá TimeRules.validate_interval; dvouhodinová délka se měří mezi skutečnými okamžiky v UTC, nikoli rozdílem místních hodin při přechodu letního času.

## Tok

```mermaid
sequenceDiagram
    actor Customer as Zákazník
    participant Web as home / formuláře
    participant Portal as PortalQueries
    participant Rules as TimeRules
    participant Store as DataStore
    participant Service as ReservationService
    Customer->>Web: GET sportoviště a den
    Web->>Portal: weekly_schedule(resource, day, now)
    Portal->>Store: load_resource, confirmed_intervals
    Store-->>Portal: příznak dostupnosti a intervaly
    Portal->>Rules: weekly_blocks(day, now, resource, confirmed)
    Rules-->>Portal: hodinové bloky
    Portal-->>Web: rozvrh
    Web-->>Customer: volné / nedostupné bloky
    Customer->>Web: POST jeden nebo dva klíče bloků
    Web->>Portal: znovu načíst aktuální rozvrh
    Portal-->>Web: aktuální bloky
    Web->>Web: BookingForm.clean: počet, unikátnost, návaznost, dostupnost
    Web->>Service: create(resource_id, odvozený interval, actor)
    Service->>Store: chráněné čtení a zápis podle REQ-01
    Service-->>Web: rezervace nebo chyba
    Web-->>Customer: výsledek; při úspěchu zachovat den a sportoviště
```

Dostupnost v rozvrhu je informativní. Formulářová kontrola ani JavaScript nenahrazují transakční kontrolu služby. Odeslání z rozvrhu používá stávající POST úvodní stránky a stejnou službu jako API. Databázové schéma se nemění.

[Požadavek](../requirements/hourly-schedule.md) · [Generované prokliky](../verification/coverage.md#req-12) · [Testy a UI ověření](../verification/hourly-schedule.md)

## Týdenní tabulka a provozní doba — REQ-13

`weekly_blocks` začíná pondělím týdne vybraného dne, sestaví sedm lokálních dnů a spojí je do řádků podle hodiny a DST fold. Řádky uzavřené ve všech dnech vynechá. Opakovaná hodina má oddělený řádek; při neexistující hodině je buňka prázdná. Identifikátor bloku obsahuje lokální datum i pořadí hodiny, takže výběr nezávisí na klientském odhadu dne. Server a JS povolují pouze dva sousední bloky jednoho dne. Všechny ostatní časové limity zůstávají ve společných pravidlech.

| Owner | Dodatečná odpovědnost |
| --- | --- |
| TimeRules.validate_operating_hours | Ověřit konfiguraci otevření před zavřením |
| TimeRules.is_within_operating_hours | Vyhodnotit celý interval proti dennímu oknu v Europe/Prague |
| ResourceService.update_operating_hours | Ověřit roli správce a atomicky uložit konfiguraci |
| DataStore.set_operating_hours | Zapsat oba časy v chráněné transakci |
| OperatingHoursForm / update_operating_hours | Vstupní validace, CSRF, odpověď uživateli; bez přímého ORM |

Resource DTO obsahuje oba skutečné časy provozu. Create a Approve po načtení aktuálního sportoviště volají `validate_resource_hours` ve stejné transakci jako alokaci. Availability při platném intervalu mimo provoz vrací False. Změna konfigurace používá stejnou ochranu SQLite IMMEDIATE, aby se nesouběžila s rozpracovaným rozhodnutím o rezervaci.

Existující pole opens_at / closes_at se využívají bez změny schématu. Již potvrzené rezervace se po zúžení doby automaticky nemažou ani neruší. Běžný správce může dobu upravit přímo v portálu; nemusí mít obecné Django oprávnění change_resource.

[REQ-13 a pravidlo BR-09](../requirements/operating-hours.md) · [Aktuální ověření](../verification/weekly-operating-hours.md)
