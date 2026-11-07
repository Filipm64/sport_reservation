# OP-05 — Approve Reservation

**Cíl / hodnota pro uživatele:** Oprávněný správce rozhodne, zda čekající
žádost smí alokovat Resource.

**Spouštěcí událost:** Přihlášený správce odešle schválení nebo zamítnutí.

**Pozorovatelný požadavek:** Pouze uživatel s oprávněním správce může
rozhodnout o `PENDING_APPROVAL`. Schválení znovu ověří čas, dostupnost
a kolize; zamítnutí změní stav na `REJECTED`. Po limitu žádost přejde
do `EXPIRED` a nelze ji schválit.

**Předpoklady:** Rezervace existuje a je ve stavu `PENDING_APPROVAL`;
aktér je přihlášený správce.

**Stav po úspěšném provedení:** Schválení → `CONFIRMED`; zamítnutí →
`REJECTED`; vypršelá žádost → `EXPIRED`.

**Změna stavu:** `PENDING_APPROVAL → CONFIRMED | REJECTED | EXPIRED`.

**Odkaz na pravidla:** BR-01 až BR-04, BR-06, BR-07, BR-08.

**Hlavní úspěšný scénář:**
1. Správce otevře čekající žádost a odešle rozhodnutí.
2. Systém ověří oprávnění a stav žádosti.
3. Při zamítnutí nastaví `REJECTED`; při schválení znovu ověří platnost
   intervalu, dostupnost a kolize.
4. Je-li kontrola úspěšná, systém nastaví `CONFIRMED` a všechny překrývající se čekající žádosti stejného sportoviště změní na `REJECTED`. Vše uloží v jedné transakci.

**Alternativní / chybové výsledky:** Běžný uživatel → zakázáno.
Žádost nečeká na rozhodnutí → odmítnuto. Při dosažení začátku
rezervace (`now >= starts_at`) → `EXPIRED`. Nedostupný Resource, neplatný čas či nová kolize
→ schválení odmítnuto. Běžné potvrzení konkurenta již žádost automaticky převede na `REJECTED`; další pokus o její schválení je nepovolený přechod. Kontrola kolize zůstává i jako ochrana proti nekonzistentním datům.

**Příklady ověření:** Správce schválí platnou čekající žádost →
`CONFIRMED`; správce ji zamítne → `REJECTED`; běžný uživatel rozhodnout
nemůže; žádost starší 24 hodin před začátkem zůstává platná;
při dosažení začátku rezervace → `EXPIRED`; kolize vzniklá během čekání
znemožní schválení.

**Zdůvodnění / zdroj:** C02 přidává lidské rozhodnutí před alokací.
Znovu se kontroluje dostupnost, protože `PENDING_APPROVAL` Resource
neblokuje.

## Související podklady

- [Vazby REQ-06: pravidla, návrh, implementace a testy](../verification/coverage.md#req-06)
- [Přehled požadavků](README.md)
- [Původní specifikace baseline v0.2](../history/baseline-v0.2.md)

Provozní doba sportoviště je závazná podle [REQ-13](operating-hours.md) a BR-09; platí při vytvoření, dotazu na dostupnost i schválení.
