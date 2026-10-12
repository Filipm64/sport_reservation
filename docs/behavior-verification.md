# L1 — Ověření chování

**Datum:** 12. 10. 2026. **Ověřený commit:** `762af3d`.
Scénář: opožděné schválení dvou žádostí o stejné sportoviště a interval,
včetně konfliktu při souběhu. Navazuje na příklady C02 a návrh H1.

Doklady odkazují na skutečně spuštěné testy:
[API](../sport_booking/reservations/tests.py),
[souběh](../sport_booking/reservations/test_concurrency.py),
[selhání ukládání](../sport_booking/reservations/test_architecture.py).

| Ověření | Výsledek | Doklad |
| :--- | :--- | :--- |
| Success path: Create → Confirm → pozdější Approve | **PASS.** Vznikne DRAFT, Confirm vytvoří PENDING_APPROVAL, která dostupnost neblokuje. Správce ji schválí do CONFIRMED; prodleva 23 hodin před deadline je povolená. | API: `test_approval_request_does_not_block_until_staff_approves`, `test_delayed_approval_succeeds_before_timeout`. |
| Alternative: během čekání vznikne potvrzená kolize | **PASS.** Approve vrátí 409 a žádost zůstane PENDING_APPROVAL. | API: `test_new_conflict_prevents_approval_and_leaves_request_pending`. |
| Concurrency: dvě současná schválení / potvrzení | **PASS.** Jedna odpověď 200, druhá 409; právě jedna CONFIRMED. Ověřeny dvojice Approve/Approve, Confirm/Confirm i Confirm/Approve. | Souběh: `test_conflicting_approvals_commit_only_one_allocation`, `test_conflicting_confirmations_commit_only_one_allocation`, `test_confirm_racing_approval_commits_only_one_allocation`. |
| Boundary: přesně deadline nebo začátek | **PASS.** Čekající žádost přejde do EXPIRED; Approve/Cancel vrátí 409. Zrušení rezervace přesně na start je odmítnuté. | API: `test_expiry_exact_deadline_on_approve_cancel_and_command`, `test_cancel_at_exact_start_is_rejected`. |
| Boundary: sousední interval a časové limity | **PASS.** Interval navazující na konec potvrzené rezervace je AVAILABLE. Přesně 30 dní dopředu / 2 hodiny přijato, překročení odmítnuto. | API: `test_availability_checks_confirmed_only_and_half_open_edges`, `test_exact_time_limits_and_exceeded_limits`. |
| Failure: chyba zápisu nebo dokončení transakce | **PASS.** Simulovaná databázová chyba se propaguje, úspěch se nevrátí a uložený stav zůstane DRAFT. | Selhání ukládání: `test_failed_save_rolls_back_and_never_reports_success`, `test_failed_commit_rolls_back`. |
| Concurrency: schválení proti expiraci v jiném procesu | **PASS.** Prošlou žádost nelze schválit; stav EXPIRED zůstane zachovaný při souběhu s expiračním commandem nad stejným SQLite souborem. | Souběh: `test_expiration_process_racing_approval_uses_shared_database`. |

## Skutečně provedený běh

```sh
PYTHONDONTWRITEBYTECODE=1 SPORT_BOOKING_TEST_DB=/tmp/sport-booking-l1-verification.sqlite3 .venv/bin/python sport_booking/manage.py test reservations.tests.ReservationApiTests reservations.test_concurrency.ReservationConcurrencyTests reservations.test_architecture.PersistenceFailureTests --noinput --verbosity 2
```

**Výsledek: 29 testů, OK, žádný přeskočený.** Spuštěno 19 API testů,
6 testů souběhu a 4 testy selhání/validace. Jde o relevantní podmnožinu
36 testů z předchozího ověření; tentokrát nebylo potřeba opakovat šest
samostatných testů databázového schématu a jednu kontrolu importů.

API příklady běží přes Django test client. Souběh používá nezávislá spojení
nad souborovou SQLite; expirační command navíc samostatný Python proces.
Časové hranice jsou fixované testem. Kód se během kroku L1 neměnil.
