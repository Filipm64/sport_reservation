# REQ-11 — Přehled čekajících žádostí správce

**Aktér:** Přihlášený správce (`is_staff`). Role platí pro všechna sportoviště.

**Vstup / událost:** `GET /` s přihlášenou relací správce.

**Výsledek:** Oddělený přehled obsahuje všechny žádosti ve stavu `PENDING_APPROVAL` se začátkem v budoucnosti. Uvádí žadatele, sportoviště, lokalitu, datum, začátek a konec. Nabízí schválení a zamítnutí přes REQ-06. Záznamy jsou řazené sestupně podle začátku, při shodě podle ID.

**Podmínky výběru:** Stáří žádosti není omezeno 24 hodinami. Při `now >= starts_at` se žádost již nenabízí k rozhodnutí. Potvrzené, zamítnuté, zrušené a vypršené záznamy do tohoto seznamu nepatří.

**Oprávnění:** Host ani běžný zákazník nedostanou údaje fronty ani ovládání pro správce. Případné přímé volání schválení či zamítnutí znovu ověřuje roli serverem podle REQ-06.

**Alternativy:** Bez platných čekajících žádostí → srozumitelný prázdný stav. Změní-li se žádost po zobrazení přehledu, následná akce respektuje aktuální stav; zobrazení není příslibem úspěšného schválení.

**Vedlejší účinky:** Žádné. Seznam neposouvá databázové stavy; pro expiraci existuje společná rezervační služba a příkaz.

**Akceptační příklady:** Správce vidí budoucí čekající žádost jiného zákazníka, i když čeká dva dny. Žádost přesně na začátku už v seznamu není. Tentýž seznam se zákazníkovi ani hostu nezobrazí.

## Zdroj a vazby

Projektový požadavek výslovně schválený uživatelem 7. 11. 2026; nejde o tvrzení, že tuto funkci výslovně předepisuje původní zadání C02.

- [Návrh webového portálu](../design/web-portal.md)
- [Implementace a konkrétní testy REQ-11](../verification/coverage.md#req-11)
- [Ověření a vztah k zadáním](../verification/portal-requirements.md)
- [Přehled požadavků](README.md)
