# Vytvoření rezervace jedním krokem a automatické zamítnutí konkurentů

**Rozhodnutí uživatele:** 7. 11. 2026. Aktuální pracovní strom nahrazuje dvoukrokové vytvoření a Confirm jedním odesláním rezervace.

## Chování

- Create ověří autentizaci, interval, dostupnost sportoviště a potvrzené kolize. Neplatný požadavek nevytvoří rezervaci.
- Bez požadavku na schválení vzniká rovnou `CONFIRMED`; jinak `PENDING_APPROVAL` s časem podání.
- Při vzniku `CONFIRMED` služba ve stejné transakci změní všechny překrývající se čekající žádosti stejného sportoviště na `REJECTED` (BR-08).
- Sousední intervaly a jiná sportoviště se nezamítají. Zrušení vítěze zamítnuté žádosti neobnovuje.
- Zůstává pět stavů: `PENDING_APPROVAL`, `CONFIRMED`, `REJECTED`, `CANCELLED`, `EXPIRED`.
- Samostatný Confirm a jeho API endpoint jsou odstraněné. Web po odeslání rovnou zobrazuje potvrzení nebo čekání na správce.
- Vlastník může čekající i potvrzenou rezervaci zrušit před začátkem. Čekající žádost vyprší při začátku; pevný limit 24 hodin neplatí.

[Stavový diagram](../design/reservation-lifecycle.md) · [Sekvence](../design/approval-sequence.md) · [Pravidla](../requirements/business-rules.md)

## Migrace

[Migrace 0003](../../sport_booking/reservations/migrations/0003_remove_draft_lifecycle.py) před změnou databázového omezení převádí staré `DRAFT` na `CANCELLED`. Zachovává záznamy, vlastníky a intervaly. Nevytváří z neodeslaných záznamů potvrzené rezervace ani čekající žádosti. Ostatní stavy nemění.

Po aktualizaci spusťte:

```sh
.venv/bin/python sport_booking/manage.py migrate
```

Migrace byla ověřena na dočasné testovací databázi; během této úpravy nebyla spuštěna nad aplikační databází. Zpětná migrace schématu neobnovuje původní `DRAFT`.

## Ověření

```sh
PYTHONDONTWRITEBYTECODE=1 SPORT_BOOKING_TEST_DB=/tmp/sport-booking-lifecycle-20261107.sqlite3 .venv/bin/python sport_booking/manage.py test reservations --noinput --verbosity 1
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python sport_booking/manage.py makemigrations --check --dry-run
python3 scripts/update_docs.py --check
```

[Úplný výstup běhu](evidence/reservation-lifecycle.log).

**Výsledek:** 49 testů, OK, žádný přeskočený. Žádné chybějící migrace. Ověřeno na SQLite v aktuálním pracovním stromu 7. 11. 2026.

| Oblast | Doklad |
| --- | --- |
| Create rovnou potvrzuje nebo čeká; kolize nic nevytvoří | [REQ-01](coverage.md#req-01), [REQ-03](coverage.md#req-03) |
| Zamítnutí překryvů a zachování sousedních intervalů / jiných sportovišť | [REQ-06](coverage.md#req-06) |
| Create/Create, Approve/Approve a Create/Approve při souběhu | [REQ-04](coverage.md#req-04) |
| Rollback vítěze i zamítnutých konkurentů při chybě ukládání | [REQ-04](coverage.md#req-04) |
| Rušení, expirace a časové hranice | [REQ-05](coverage.md#req-05), [REQ-06](coverage.md#req-06) |
| Web v jednom kroku a zamítnutí konkurenční žádosti přes web | [PortalTests](../../sport_booking/reservations/test_portal.py) |
| Převod historických DRAFT bez ztráty záznamů | [ReservationLifecycleMigrationTests](../../sport_booking/reservations/test_migrations.py) |

Starší baseline, logy a revize zůstávají historickými doklady tehdejšího chování. Jejich výsledky se nevydávají za ověření současné změny.
