# Expirace čekajících žádostí při začátku rezervace

> Záznam dílčí změny před odstraněním DRAFT. Aktuální životní cyklus a nové ověření jsou v [navazujícím záznamu](reservation-lifecycle.md).

**Rozhodnutí:** 7. 11. 2026 uživatel schválil variantu A: čekající žádost platí do začátku rezervace, bez pevného limitu 24 hodin.

## Aktuální pravidlo

- Před začátkem může vlastník žádost zrušit a oprávněný správce schválit nebo zamítnout. Při schválení se nadále ověřuje dostupnost a kolize.
- Stáří žádosti samo o sobě nezpůsobuje expiraci.
- Při `now >= reservation.starts_at` již žádost nelze schválit, zamítnout ani zrušit. Approve/Cancel nebo expirační příkaz uloží `EXPIRED`.
- Čekající žádost nadále neblokuje sportoviště. Automatický plánovač expirace není součástí této změny; čtení samo uložený stav nemění.

[BR-07](../requirements/business-rules.md#br-07) · [Zrušení](../requirements/cancel-reservation.md) · [Schválení](../requirements/approve-reservation.md) · [Aktuální stavový diagram](../assets/diagrams/reservation-state.svg)

## Realizace a ověření

[ApprovalRequest.deadline](../../sport_booking/reservations/domain.py) odvozuje deadline pouze od začátku rezervace. Databázové schéma se nemění.

| Scénář | Očekávaný výsledek | Test |
| --- | --- | --- |
| Schválení po dvou dnech čekání, před začátkem | `CONFIRMED` | `test_delayed_approval_succeeds_after_24_hours_before_start` |
| Zrušení nebo zamítnutí po dvou dnech čekání | `CANCELLED` nebo `REJECTED` | `test_pending_request_remains_actionable_after_24_hours_until_start` |
| Expirační příkaz po dvou dnech čekání, před začátkem | Stále `PENDING_APPROVAL` | Stejný test |
| Schválení, zamítnutí, zrušení a příkaz těsně před začátkem | Požadovaná operace uspěje; příkaz ponechá žádost čekající | `test_expiry_exact_deadline_on_approve_cancel_and_command` |
| Stejné operace přesně při začátku a po něm | `EXPIRED`, uživatelské změny odmítnuty | Stejný test |
| Opakovaná expirace a expirace proti schválení v jiném procesu | `EXPIRED` se neobnoví | `test_expiration_is_idempotent_and_preserves_terminal_states`, `test_expiration_process_racing_approval_uses_shared_database` |

[Prokliky na implementaci a testy REQ-05](coverage.md#req-05) · [Prokliky REQ-06](coverage.md#req-06)

Ověřeno 7. 11. 2026 v aktuálním pracovním stromu:

```sh
PYTHONDONTWRITEBYTECODE=1 SPORT_BOOKING_TEST_DB=/tmp/sport-booking-expiration-start-20261107.sqlite3 .venv/bin/python sport_booking/manage.py test reservations --noinput --verbosity 1
```

**Výsledek: 54 testů, OK, žádný přeskočený**, včetně souběhu a expiračního příkazu v samostatném procesu. Souběžné testy používají dočasnou souborovou SQLite databázi.

## Vztah k historii

[Baseline v0.2](../history/baseline-v0.2.md) a starší záznamy ověření zachovávají původní 24hodinové pravidlo. Nejsou dokladem nového chování. Ostatní historické nejasnosti a širší revize požadavků nejsou touto změnou řešeny.
