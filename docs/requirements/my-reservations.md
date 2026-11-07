# REQ-10 — Zobrazení vlastních rezervací

**Aktér:** Přihlášený zákazník; stejný osobní přehled má i správce pro své vlastní rezervace.

**Vstup / událost:** `GET /` s přihlášenou relací. Identita vlastníka se bere z relace, nikoli z klientem dodaného ID.

**Výsledek:** Osobní přehled obsahuje pouze rezervace přihlášeného uživatele ve všech pěti stavech. Uvádí sportoviště, lokalitu, datum, začátek, konec a stav. Přehled je řazen sestupně podle začátku, při shodě podle ID.

**Časové pravidlo:** Čekající žádost s dosaženým začátkem se zobrazí jako `EXPIRED`, i pokud databázová expirace ještě nebyla provedena. Prohlížení samo databázi nemění. Tlačítko zrušení je dostupné jen u platné čekající nebo potvrzené rezervace před začátkem; server změnu znovu ověří podle REQ-05.

**Alternativy:** Bez vlastních rezervací → srozumitelná zpráva o prázdném přehledu. Nepřihlášený návštěvník → veřejný katalog bez osobního seznamu. Správce vidí cizí čekající žádosti výhradně v odděleném přehledu REQ-11.

**Vedlejší účinky:** Žádné; GET nevytváří rezervace ani nezapisuje stavové přechody.

**Akceptační příklady:** Zákazník A nevidí rezervace zákazníka B. Uživatel vidí své potvrzené, čekající, zamítnuté, zrušené a vypršené záznamy. Čekající žádost přesně na začátku ukazuje „Vypršelo“ bez tlačítka zrušení a bez zápisu do databáze.

## Zdroj a vazby

Projektový požadavek výslovně schválený uživatelem 7. 11. 2026; nejde o tvrzení, že tuto funkci výslovně předepisuje původní zadání C02.

- [Návrh webového portálu](../design/web-portal.md)
- [Implementace a konkrétní testy REQ-10](../verification/coverage.md#req-10)
- [Ověření a vztah k zadáním](../verification/portal-requirements.md)
- [Přehled požadavků](README.md)
