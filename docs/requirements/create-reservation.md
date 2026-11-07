# REQ-01 / OP-01 — Create Reservation

**Cíl:** Přihlášený zákazník odešle rezervaci jedním krokem.

**Vstup:** Sportoviště (`resource_id`), začátek (`starts_at`) a konec (`ends_at`) s časovým pásmem.

**Předpoklady:** Zákazník je přihlášený, sportoviště existuje a je dostupné, interval splňuje BR-01/03 a nekoliduje s potvrzenou rezervací.

**Úspěšný výsledek:** Pro sportoviště bez schvalování vznikne rovnou `CONFIRMED`. Pro sportoviště vyžadující schválení vznikne `PENDING_APPROVAL` a uloží se čas podání. API vrátí 201, ID a stav. Samostatné potvrzení uživatelem neexistuje.

**Hlavní scénář:**
1. Zákazník odešle sportoviště a interval.
2. Systém pod ochranou proti souběhu ověří interval, dostupnost sportoviště a potvrzené kolize.
3. Podle nastavení sportoviště vytvoří `CONFIRMED` nebo `PENDING_APPROVAL`.
4. Při vzniku `CONFIRMED` zamítne všechny překrývající se čekající žádosti stejného sportoviště.
5. Vše uloží v jedné transakci a vrátí výsledek.

**Chyby:** Neplatný vstup, neznámé nebo nedostupné sportoviště, nepřihlášený zákazník či potvrzená kolize → požadavek odmítnut, rezervace nevznikne. Chyba zápisu vrátí celou transakci včetně automatických zamítnutí.

**Pravidla:** BR-01 až BR-04, BR-06, BR-07, BR-08.

[Vazby na návrh, implementaci a testy](../verification/coverage.md#req-01) · [Požadavky](README.md)

## Výběr času na webu

Zákazník může zadat přesný začátek a konec nebo vybrat 1 či 2 navazující hodinové bloky podle [REQ-12](hourly-schedule.md). Oba způsoby mají stejný limit BR-03 a stejnou kontrolu kolize při uložení.

Provozní doba sportoviště je závazná podle [REQ-13](operating-hours.md) a BR-09; platí při vytvoření, dotazu na dostupnost i schválení.
