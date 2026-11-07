# REQ-08 — Registrace zákazníka

**Aktér:** Nepřihlášený návštěvník.

**Vstup / událost:** Uživatelské jméno, heslo a jeho potvrzení odeslané přes `POST /registrace/`; formulář je dostupný na `GET /registrace/`.

**Podmínky:** Unikátní uživatelské jméno přijatelné podle validace účtu, shodná hesla splňující nastavenou politiku a platná CSRF ochrana.

**Úspěšný výsledek:** Vznikne právě jeden aktivní zákaznický účet. Heslo je uloženo jako hash, uživatel je automaticky přihlášen a přesměrován na úvodní stránku. Účet nemá oprávnění správce ani superuživatele.

**Hlavní scénář:** Návštěvník vyplní formulář; systém ověří vstupy, uloží účet, vytvoří přihlášenou relaci a zobrazí úvodní stránku.

**Chyby:** Obsazené nebo chybějící jméno, slabé heslo či neshodné potvrzení → formulář s chybou, žádný nový účet a žádná přihlášená relace. Chybějící CSRF token → požadavek odmítnut.

**Oprávnění:** Veřejná registrace ignoruje podstrčené příznaky `is_staff` a `is_superuser`. Již přihlášený uživatel je přesměrován na úvodní stránku; nový účet se nevytvoří a původní relace zůstane zachovaná.

**Akceptační příklady:** Platná registrace vytvoří jeden běžný účet a přihlásí jej. Opakované jméno `customer` nebo dvě různá hesla nevytvoří účet. Přidané `is_staff=true` nepřidělí oprávnění.

## Zdroj a vazby

Projektový požadavek výslovně schválený uživatelem 7. 11. 2026; nejde o tvrzení, že tuto funkci výslovně předepisuje původní zadání C02.

- [Návrh webového portálu](../design/web-portal.md)
- [Implementace a konkrétní testy REQ-08](../verification/coverage.md#req-08)
- [Ověření a vztah k zadáním](../verification/portal-requirements.md)
- [Přehled požadavků](README.md)
