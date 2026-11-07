# REQ-07 — Veřejný katalog sportovišť

**Aktér:** Návštěvník, přihlášený zákazník i správce.

**Vstup / událost:** Otevření úvodní stránky (`GET /`). Přihlášení není nutné.

**Výsledek:** Zobrazí se všechna sportoviště v katalogu, včetně provozně nedostupných. U každého je název, sport, lokalita, otevírací doba, provozní dostupnost a příznak požadovaného schválení. Provozní dostupnost neznamená volný konkrétní termín; ten ověřuje REQ-02.

**Hlavní scénář:** Návštěvník otevře stránku; systém načte katalog a vykreslí jeho položky bez změny dat a bez vytvoření rezervace.

**Alternativy:** Prázdný katalog → srozumitelná zpráva bez chyby. Nedostupné sportoviště → zůstává viditelné a je označené jako nedostupné.

**Oprávnění a vedlejší účinky:** Veřejný katalog nezpřístupňuje cizí rezervace ani seznam čekajících žádostí. Otevírací doba vymezuje povolené rezervace podle [REQ-13](operating-hours.md) a BR-09.

**Akceptační příklady:** Nepřihlášený návštěvník vidí Kurt A s lokalitou Ostrava a dobou 08:00–22:00. Neaktivní Kurt A zůstává v katalogu označený jako nedostupný. Katalog bez položek vrátí úspěšnou stránku s informací o prázdném seznamu.

## Zdroj a vazby

Projektový požadavek výslovně schválený uživatelem 7. 11. 2026; nejde o tvrzení, že tuto funkci výslovně předepisuje původní zadání C02.

- [Návrh webového portálu](../design/web-portal.md)
- [Implementace a konkrétní testy REQ-07](../verification/coverage.md#req-07)
- [Ověření a vztah k zadáním](../verification/portal-requirements.md)
- [Přehled požadavků](README.md)
