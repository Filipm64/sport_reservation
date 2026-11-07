# OP-02 — Check Availability

**Cíl / hodnota pro uživatele:** Uživatel zjistí, zda je možné zvolený
interval potvrdit.

**Spouštěcí událost:** Uživatel odešle Resource a interval ke kontrole.

**Pozorovatelný požadavek:** Systém vrátí `AVAILABLE`, pokud je Resource
dostupný a v intervalu není jeho `CONFIRMED` rezervace; jinak vrátí
`UNAVAILABLE`. Žádost čekající na schválení dostupnost nemění.

**Předpoklady:** Uživatel je přihlášen; Resource existuje; interval splňuje BR-01 a BR-03.

**Stav po úspěšném provedení:** Vrácen výsledek bez změny záznamů.

**Změna stavu:** Žádná.

**Odkaz na pravidla:** BR-01 až BR-04, BR-07.

**Hlavní úspěšný scénář:**
1. Uživatel odešle Resource a interval.
2. Systém ověří vstup a zkontroluje dostupnost a překryv s potvrzenými
   rezervacemi.
3. Systém vrátí výsledek.

**Alternativní / chybové výsledky:** Nepřihlášený uživatel → odmítnuto.
Neplatný vstup nebo neznámý Resource
→ chyba; nedostupný Resource či potvrzený překryv → `UNAVAILABLE`.

**Příklady ověření:** Potvrzená `[10:00,11:00)` dává dotazům
`[09:00,10:00)` → `AVAILABLE`, `[10:30,11:30)` → `UNAVAILABLE` a
`[11:00,12:00)` → `AVAILABLE`. Samotný překryv `PENDING_APPROVAL` →
`AVAILABLE`.

**Zdůvodnění / zdroj:** Kontrola nic nerezervuje; výsledek se může před
potvrzením změnit.

## Související podklady

- [Vazby REQ-02: pravidla, návrh, implementace a testy](../verification/coverage.md#req-02)
- [Přehled požadavků](README.md)
- [Původní specifikace baseline v0.2](../history/baseline-v0.2.md)

Provozní doba sportoviště je závazná podle [REQ-13](operating-hours.md) a BR-09; platí při vytvoření, dotazu na dostupnost i schválení.
