# L2 — Ověření architektonického pravidla

**Architektonické pravidlo:** HTTP vstupy a expirační příkaz nesmějí
používat ORM přímo ani přepisovat stav rezervace. Změnu vyžádají u
ReservationService — Správy rezervací podle ADR-01 a G2.

**Kontrola:** Opakovatelný AST test
`ArchitectureDependencyTests.test_entry_points_do_not_access_orm_or_mutate_reservation_state`
v [test_architecture.py](../sport_booking/reservations/test_architecture.py).
Kontroluje `views.py`, `api.py` a `expire_reservations.py`: zakazuje přímé
importy ORM/ukládání, přístup přes `.objects` a přiřazení `.status`/`.state`,
včetně `setattr`. Čtení stavu pro sestavení odpovědi je povolené.

Test také ověřuje, že odmítne sedm ukázkových porušení pravidla a přijme
povolené volání služby. Ukázky se pouze analyzují; zdrojové soubory nemění.
Kontrola je statická a zaměřená na uvedené přímé přístupy; při přidání
nového vstupního souboru je potřeba zahrnout ho do seznamu kontrolovaných cest.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python sport_booking/manage.py test reservations.test_architecture.ArchitectureDependencyTests.test_entry_points_do_not_access_orm_or_mutate_reservation_state --verbosity 2
```

**Výsledek:** 12. 10. 2026 **PASS — 1 test, OK**. V žádném ze tří vstupů
není nalezené porušení. Kontrola nevyžaduje databázi a běží také v celkové
sadě `test reservations`.

**Doklad:** [Skutečný výstup běhu](evidence/l2-architecture-test.log).
