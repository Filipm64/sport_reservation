# C08 — výchozí stav storno politiky

## Baseline před změnou

Datum přípravy: 8. 11. 2026. Aplikační baseline:
`cd3c4ddc8dbc47d83483441c51b8d8a7ce87281c`.
Nový testovací modul a tento záznam jsou ověřovací doplněk nad tímto
commitem; aplikační kód ani platné požadavky se pro C08 nemění.
Zadání [C08_FINAL.html](../../assigments/C08_FINAL.html) je dosud nesledovaný
soubor. Lokálně změněná aplikační `sport_booking/db.sqlite3` není součástí
reprodukovatelného testovacího vstupu a při ověření se nepoužívá.

Přijatý kontrakt: [OP-04 / REQ-05](../requirements/cancel-reservation.md)
a [BR-05](../requirements/business-rules.md#br-05) v uvedeném commitu.
Vlastník smí zrušit CONFIRMED před začátkem, nikoliv při začátku nebo později;
záznam zůstává. Kontext: BR-01, BR-02, BR-06 a BR-07 ve stejném dokumentu.
Vlastníkem rozhodnutí je `ReservationService.cancel`, čas kontroluje
`TimeRules.validate_cancellation`, transakci ukládá `DjangoDataStore`.
Architektonická opora: [ADR-01](../architecture/decisions/ADR-001-reservation-coordination.md).

Prostředí: Python 3.14.6, Django 6.1.1 (`requirements.txt`), SQLite 3.53.2.
Konfigurace: `sport_booking.settings`, `USE_TZ=True`, `Europe/Prague`,
SQLite `IMMEDIATE`, timeout 20 s. Schéma reservations:
`0003_remove_draft_lifecycle` včetně předchozích migrací. Django test runner
vytvoří oddělenou databázi, aplikuje migrace a po běhu ji odstraní.
Účty, sport, sportoviště a rezervace vznikají automaticky v každém testu;
nejsou potřeba existující data ani hesla.

## Společná příprava a metoda

Oba případy byly specifikovány **před prvním spuštěním**, nikoliv podle
pozorovaného výsledku. Původní stav NOT RUN byl po provedení nahrazen
níže uvedeným pozorováním. Běh 8. 11. 2026: **2 testy prošly**.
Kompletní [výstup včetně SQL čtení](evidence/c08-cancellation-baseline.log).
Spustitelný postup: [test_c08_baseline.py](../../sport_booking/reservations/test_c08_baseline.py).

- Uživatelský účet `c08-owner`, běžná role, přihlášení Django test klientem.
- Sport `C08 Tennis`, Resource `C08 Court`, Ostrava, 08:00–22:00
  Europe/Prague, dostupný, bez schvalování.
- Vytvoření při `2026-11-09T09:00:00+00:00` (10:00 Praha).
- Rezervace `[2026-11-10T10:00:00+00:00, 2026-11-10T11:00:00+00:00)`
  (11:00–12:00 Praha), vlastník `c08-owner`.
- Hodiny business pravidel jsou řízené přes `TimeRules.now`; API, služba,
  oprávnění, ORM, transakce a SQLite jsou skutečné.
- `TransactionTestCase` neobaluje případ vnější testovací transakcí.
  Po dokončení požadavku se uložený stav čte přes nové nezávislé SQLite
  spojení dotazem `SELECT id, user_id, resource_id, starts_at, ends_at,
  status FROM reservations_reservation WHERE id = ?`.
  Kontrolují se i identita, sportoviště a zachování intervalu.
- Test runner po každém případu vyčistí data; opakovaný běh sestaví stejný
  vstup znovu. Číselná ID generuje DB a log je zaznamená.

## TC-C08-01 — zrušení sekundu před začátkem

Test basis: BR-05 / OP-04 v baseline výše. Riziko: změna storno politiky
může nechtěně změnit kontrakt, souvisí s [R-04](../history/evidence-and-evolution.md#r-04).

| # | Akce / vstup | Expected před provedením | Actual / evidence |
| --- | --- | --- | --- |
| 1 | Připravit účet a Resource, POST `/api/reservations/` s uvedeným intervalem | HTTP 201, CONFIRMED | HTTP 201, id=1, CONFIRMED |
| 2 | Nezávislé SQL čtení uloženého záznamu | Jeden CONFIRMED správného vlastníka, Resource a intervalu | SQL: id=1, user=1, resource=1, interval souhlasí, CONFIRMED |
| 3 | V čase `2026-11-10T09:59:59+00:00` POST `/api/reservations/<id>/cancel/` jako vlastník | HTTP 200, CANCELLED | HTTP 200, CANCELLED |
| 4 | Novým SQLite spojením načíst committed stav | Tentýž záznam CANCELLED, ostatní kontrolovaná data zachována | SQL: id=1, CANCELLED, vlastník, Resource a interval zachovány |

Konečná podmínka: rezervace nebyla smazána, uložené zrušení už neblokuje
Resource podle BR-02. Tento případ ověřuje uložený status; nové vytvoření
stejného termínu není jeho součástí. Verdikt: **PASS**, kroky 1–4 doložené
v [logu TC-C08-01](evidence/c08-cancellation-baseline.log).

## TC-C08-02 — odmítnutí zrušení přesně při začátku

Test basis: BR-05 / OP-04 ve stejné baseline; stejné riziko R-04.
Používá nově připravenou DB a stejná vstupní data, nikoliv výsledek TC-01.

| # | Akce / vstup | Expected před provedením | Actual / evidence |
| --- | --- | --- | --- |
| 1 | Připravit účet a Resource, POST `/api/reservations/` | HTTP 201, CONFIRMED | HTTP 201, id=2, CONFIRMED |
| 2 | Nezávislé SQL čtení uloženého záznamu | Jeden CONFIRMED správného vlastníka, Resource a intervalu | SQL: id=2, user=2, resource=2, interval souhlasí, CONFIRMED |
| 3 | V čase `2026-11-10T10:00:00+00:00` POST `/api/reservations/<id>/cancel/` jako vlastník | HTTP 409, odmítnutí zrušení | HTTP 409, „Reservation has already started.“ |
| 4 | Novým SQLite spojením načíst stav po odmítnutí | Tentýž záznam stále CONFIRMED, ostatní kontrolovaná data zachována | SQL: id=2, CONFIRMED, vlastník, Resource a interval zachovány |

Konečná podmínka: neúspěšné zrušení nezměnilo uloženou rezervaci.
Verdikt: **PASS**, kroky 1–4 doložené v
[logu TC-C08-02](evidence/c08-cancellation-baseline.log).

## Reprodukce a meze důkazu

Z kořene repozitáře, s novou vyhrazenou cestou k testovací DB:

```sh
SPORT_BOOKING_TEST_DB=/tmp/sport-booking-c08-baseline.sqlite3 .venv/bin/python sport_booking/manage.py test reservations.test_c08_baseline --noinput --verbosity 2
```

Test runner tuto testovací DB vytváří a odstraňuje; nepoužívat cestu
k aplikační DB. Skutečný běh použil jedinečnou cestu uvedenou v logu.

Jde o integrační test přes Django HTTP test klienta a skutečnou persistenci,
bez síťového serveru/prohlížeče. Přihlášení používá `force_login`; CSRF
ochrana není v tomto klientovi vynucená. Neověřuje UI, přihlášení heslem,
souběh, čekající žádosti ani celý systém. Při přípravě tohoto ověření nebyl
nový limit odsouhlasený. Následný souhlas s požadavkem je zaznamenán v
[C08 Change Request](../requirements/C08-change-request.md); implementace
nenásledovala a tyto případy dokazují jen původní kontrakt.
