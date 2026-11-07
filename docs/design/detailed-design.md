# C05 Detailed Design

Selected architecture unit: Reservation lifecycle and approval gating.

Related requirements: REQ-01, REQ-03 až REQ-06. Drivers: AD-01 až AD-05. Pravidla: BR-01 až BR-08.

## Návrhový záměr

Zákazník rezervaci odešle jedním krokem. Služba ověří interval a dostupnost, poté vytvoří `CONFIRMED` nebo `PENDING_APPROVAL` podle sportoviště. `DRAFT` neexistuje.

Potvrzené rezervace stejného sportoviště se nesmějí časově překrývat. Potvrzení jedné rezervace automaticky zamítne ostatní překrývající se čekající žádosti stejného sportoviště. Vše tvoří jednu transakci.

Samotné `PENDING_APPROVAL` neblokuje sportoviště; dostupnost závisí na příznaku sportoviště a překryvu s `CONFIRMED`. Čekající žádost platí do začátku rezervace, bez 24hodinového limitu. Terminální stavy jsou `REJECTED`, `CANCELLED` a `EXPIRED`. `CONFIRMED` lze před začátkem zrušit.

## Odpovědnosti a vlastníci

| Odpovědnost | Owner |
| --- | --- |
| Ověřit aktéra a oprávnění | IdentityAccess |
| Vyhodnotit interval, aktuální čas a překryv | TimeRules |
| Zvolit počáteční stav a rozhodnout o alokaci | ReservationService |
| Provést povolený přechod objektu | Reservation |
| Vybrat konkurenční žádosti stejného sportoviště | DataStore |
| Zamítnout konkurenty při potvrzení | ReservationService a Reservation.reject |
| Zajistit chráněné čtení a atomické uložení | DjangoDataStore |

## Kontrakt Create

`ReservationService.create(resource_id, interval, actor) -> Reservation`

Vstup: autentizovaný aktér, sportoviště a interval. Služba pod ochranou proti souběhu načte sportoviště a ověří BR-01/03/04 a kolize.

Postcondition: právě jedna nová `CONFIRMED` nebo `PENDING_APPROVAL`. Při `CONFIRMED` jsou všichni překrývající se čekající konkurenti `REJECTED`. Při neplatném vstupu nebo chybě zápisu nevznikne rezervace ani částečná zamítnutí.

## Kontrakt Approve

`ReservationService.approve(reservation_id, actor, decision) -> Reservation`

Preconditions: autentizovaný správce, existující `PENDING_APPROVAL`, rozhodnutí `approve` nebo `reject`.

- Před začátkem `reject` uloží `REJECTED`.
- Před začátkem `approve` ověří aktuální dostupnost a kolize, uloží `CONFIRMED` a zamítne konkurenty v jedné transakci.
- Při `now >= interval.start` uloží `EXPIRED`, dokončí transakci a poté vrátí chybu `expired`.
- Jiný stav → `conflict`; neznámá rezervace → `not_found`; chybějící oprávnění → `forbidden`; neplatné rozhodnutí → `invalid_input`.
- Chyba persistence nesmí být vydávána za úspěch a vrací celou neúspěšnou transakci.

## Algoritmus potvrzení

```text
protect state and resource
validate actor, interval, availability and confirmed conflicts
save winner as CONFIRMED
for id in overlapping_pending_ids(winner):
    competing = load_protected(id)
    competing.reject()
    save(competing)
commit()
```

Při chybném zápisu vítěze nebo konkurenta následuje rollback celé transakce. Při souběžném Approve druhá operace čte stav až po získání ochrany: již zamítnutý konkurent se neobnoví.

## Čas a zrušení

```text
approval_deadline = reservation.interval.start
expired = pending and now >= approval_deadline
```

`cancel` ověří vlastníka a `now < start`, pak převede `PENDING_APPROVAL` nebo `CONFIRMED` na `CANCELLED`. Expirace při začátku má přednost. Opakované zrušení ani obnovení terminálního stavu nejsou povoleny.

[Strukturální diagram](design-classes.md) · [Sekvenční diagram](approval-sequence.md) · [Stavový diagram](reservation-lifecycle.md) · [Konkrétní implementace a testy](../verification/coverage.md)

Detaily frameworku, výjimek a SQLite zůstávají v implementaci; invarianty, hranice transakce a výsledky jsou součástí kontraktu.
