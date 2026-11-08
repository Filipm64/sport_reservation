# Požadavky a pravidla

[Přehled dokumentace](../README.md) · [Účel, aktéři a rozsah](overview.md) · [Business pravidla](business-rules.md)

[C08 — Change Request: storno politika rezervací](C08-change-request.md)
zachycuje přijatý záměr pro C09. Nová politika zatím není implementovaná;
níže uvedené požadavky nadále popisují současnou aplikaci.

| ID | Požadavek | Implementace, návrh a testy |
| --- | --- | --- |
| REQ-01 / OP-01 | [Vytvoření rezervace](create-reservation.md) | [Vazby](../verification/coverage.md#req-01) |
| REQ-02 / OP-02 | [Kontrola dostupnosti](check-availability.md) | [Vazby](../verification/coverage.md#req-02) |
| REQ-03 (součást OP-01) | [Automatické potvrzení při vytvoření](confirm-reservation.md) | [Vazby](../verification/coverage.md#req-03) |
| REQ-04 / OP-01 a OP-05 | [Zabránění dvojí rezervaci](prevent-double-booking.md) | [Vazby](../verification/coverage.md#req-04) |
| REQ-05 / OP-04 | [Zrušení rezervace](cancel-reservation.md) | [Vazby](../verification/coverage.md#req-05) |
| REQ-06 / OP-05 | [Schválení rezervace](approve-reservation.md) | [Vazby](../verification/coverage.md#req-06) |
| REQ-07 | [Veřejný katalog sportovišť](public-catalog.md) | [Vazby](../verification/coverage.md#req-07) |
| REQ-08 | [Registrace zákazníka](customer-registration.md) | [Vazby](../verification/coverage.md#req-08) |
| REQ-09 | [Přihlášení a odhlášení](login-logout.md) | [Vazby](../verification/coverage.md#req-09) |
| REQ-10 | [Zobrazení vlastních rezervací](my-reservations.md) | [Vazby](../verification/coverage.md#req-10) |
| REQ-11 | [Přehled čekajících žádostí správce](staff-approval-queue.md) | [Vazby](../verification/coverage.md#req-11) |
| REQ-12 | [Výběr rezervace z hodinového rozvrhu](hourly-schedule.md) | [Vazby](../verification/coverage.md#req-12) |
| REQ-13 | [Nastavení a vynucování provozní doby](operating-hours.md) | [Vazby](../verification/coverage.md#req-13) |

Popisy operací a pravidel vycházejí z [baseline v0.2](../history/baseline-v0.2.md). REQ-04 je převzatý z [revize požadavků](review.md), protože pokrývá více operací. Původní dokumenty, jejich stav a poznámky zůstávají zachované.

- [Revize a dohledatelnost požadavků C02](review.md)
- [Schválení baseline](../history/baseline-approval.md)
- [Zadání pro následnou kontrolu platnosti](../../assigments/README.md)

Aktuální změna BR-07: [expirace při začátku rezervace bez 24hodinového limitu](../verification/approval-expiration.md).

Aktuální změna životního cyklu: [vytvoření jedním krokem, pět stavů a zamítnutí konkurentů](../verification/reservation-lifecycle.md).

REQ-07 až REQ-11 doplňují projektový rozsah o webový portál podle rozhodnutí uživatele; [ověření podle dostupných podkladů](../verification/portal-requirements.md).
