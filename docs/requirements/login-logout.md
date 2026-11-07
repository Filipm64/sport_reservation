# REQ-09 — Přihlášení a odhlášení

**Aktér:** Zákazník nebo správce s existujícím účtem.

**Vstup / událost:** Jméno a heslo přes `POST /prihlaseni/`; formulář je dostupný na `GET /prihlaseni/`. Odhlášení používá `POST /odhlaseni/`. Obě změny relace vyžadují CSRF ochranu.

**Úspěšné přihlášení:** Platné údaje aktivního účtu vytvoří přihlášenou relaci stejného uživatele. Role vychází z uloženého účtu. Výchozí cíl je úvodní stránka; případné návratové přesměrování smí mířit pouze na povolený místní cíl.

**Chybné přihlášení:** Neznámé jméno, chybné heslo nebo neaktivní účet → formulář s chybou, bez autentizované relace.

**Úspěšné odhlášení:** Zanikne přihlášená relace a prohlížeč je přesměrován na úvodní stránku. Další veřejné zobrazení neobsahuje soukromé přehledy.

**Alternativy:** `GET /odhlaseni/` je odmítnut a přihlášení neruší. Požadavek bez platné CSRF ochrany relaci nemění. Již přihlášený návštěvník přihlašovací stránky je přesměrován na úvodní stránku.

**Akceptační příklady:** Zákazník i správce se platnými údaji přihlásí; špatné heslo ani neaktivní účet neuspějí. Návratová adresa na cizí host se nepoužije. Odhlášení přes POST odstraní autentizaci, GET nikoli.

## Zdroj a vazby

Projektový požadavek výslovně schválený uživatelem 7. 11. 2026; nejde o tvrzení, že tuto funkci výslovně předepisuje původní zadání C02.

- [Návrh webového portálu](../design/web-portal.md)
- [Implementace a konkrétní testy REQ-09](../verification/coverage.md#req-09)
- [Ověření a vztah k zadáním](../verification/portal-requirements.md)
- [Přehled požadavků](README.md)
