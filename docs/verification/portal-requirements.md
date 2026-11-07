# Ověření REQ-07 až REQ-11 a vztah k zadáním

**Rozsah schválený uživatelem:** veřejný katalog, registrace zákazníka, přihlášení a odhlášení, vlastní rezervace a přehled čekajících žádostí správce. Požadavky byly doplněny 7. 11. 2026 jako explicitní projektový rozsah. Nejde o tvrzení, že všechny tyto funkce předepisuje původní zadání C02.

## Jednotný stav dokumentace, kódu a testů

Tento záznam zachycuje ověření REQ-07 až REQ-11 dne 7. 11. 2026. Výsledky platí pro tehdejší pracovní verzi dokumentace, kódu a testů. Navazující ověření týdenního rozvrhu a provozní doby je v [aktuálním záznamu](weekly-operating-hours.md).

[Úplný výstup běhu](evidence/portal-requirements.log) zachycuje konkrétní spuštěné testy a výsledek.

## Požadavek → očekávání → ověření

| Požadavek | Úspěšný příklad / oracle | Negativní nebo hraniční příklad / oracle | Prokliky |
| --- | --- | --- | --- |
| REQ-07 Katalog | Host vidí název, sport, lokalitu, otevírací dobu, dostupnost a schvalování | Prázdný katalog se zobrazí bez chyby; nedostupná položka zůstává označená v seznamu; soukromé přehledy se nezpřístupní | [Implementace a testy](coverage.md#req-07) |
| REQ-08 Registrace | Vznikne jeden aktivní běžný účet s heslem uloženým jako hash a přihlášenou relací | Duplicitní jméno, slabé heslo či neshoda nevytvoří účet; podstrčené role nedávají staff/superuser; přihlášený uživatel nevytvoří další účet | [Implementace a testy](coverage.md#req-08) |
| REQ-09 Relace | Aktivní zákazník i správce se přihlásí; POST logout odstraní autentizaci | Špatné heslo a neaktivní účet selžou; GET logout vrátí 405; neplatné CSRF vrátí 403; cizí návratový host se nepoužije | [Implementace a testy](coverage.md#req-09) |
| REQ-10 Vlastní rezervace | Osobní seznam obsahuje vlastní záznamy ve všech pěti stavech, s údaji a sestupným řazením | Cizí záznamy nejsou v osobním seznamu ani správci; prázdný seznam má zprávu; přesně na začátku se čekající žádost zobrazí jako vypršelá bez změny databáze | [Implementace a testy](coverage.md#req-10) |
| REQ-11 Fronta správce | Staff vidí platné čekající žádosti ostatních zákazníků, konec intervalu a ovládání | Host a zákazník frontu nedostanou; vyloučeny jsou ostatní stavy i žádosti přesně na začátku a po něm; stáří přes 24 hodin nevadí; GET nezapisuje stav | [Implementace a testy](coverage.md#req-11) |

Testy používají HTTP rozhraní přes Django test client a skutečnou testovací databázi. Očekávané výsledky vycházejí z požadavků a [návrhových kontraktů](../design/web-portal.md). U kontroly CSRF se navíc používá `Client(enforce_csrf_checks=True)`; jsou ověřeny odmítnuté požadavky i funkční registrace, přihlášení a odhlášení s platnými tokeny.

## Co bylo realizováno

Existující katalog, registrace a autentizace byly výslovně specifikovány a ověřeny. Osobní seznam a fronta nyní mají oddělené datové dotazy. Časový snapshot je společný pro zobrazení seznamů a ovládání; význam zobrazené expirace vlastní TimeRules. Prošlé žádosti se nenabízejí správci k rozhodnutí a vlastníkovi se zobrazují jako vypršelé. Zobrazení nepřepisuje rezervace v databázi. Fronta správce doplňuje konec časového intervalu.

## Vazba na dostupná zadání

| Podklad | Použité kritérium | Konkrétní doklad |
| --- | --- | --- |
| [C06 Assessment — R1 až R5](../../assigments/SWI_C06_Assessment_Form_CZ_v4.md#c02--engineering-specification) | Vstup, předpoklady, výsledek, konzistence pravidel, shoda implementace a evidence | Samostatné stránky REQ-07 až REQ-11, tabulka výše a spuštěné testy |
| [C06 Assessment — A1 až A3](../../assigments/SWI_C06_Assessment_Form_CZ_v4.md#c03--architecture) | Odpovědnosti, skuteční vlastníci a cesta volání | Návrh portálu, aktualizovaný kontext systému, prokliky na konkrétní symboly; architektonické testy běží v celé sadě |
| [C03 Part A — A2, A3 a A9](../../assigments/SWI_C03_PartA_Tuesday_students_bilingual_v8.html) | Dohledat hlavní a alternativní průchod a uvádět ověřená tvrzení | Tabulka kontraktů a sekvence portálu, pozitivní i negativní testy a log běhu |
| [C05 Detailed Design — kroky 3 až 6](../../assigments/SWI_C05_Detailed_Design_students_toggle_v4.html) | Explicitní kontrakty, časové a stavové hranice, odvození testů a shoda návrhu s kódem | Návrh portálu vymezuje read-only dotazy a oddělení rolí; testy ověřují odpovídající chování na HTTP/integration úrovni |
| [C07/C08](../../assigments/SWI_C07_C08_Assignment_CZ_EN_FINAL.html) | Rozlišit Specified / Designed / Implemented / Verified a nepoužívat jen plán jako důkaz ověření | Konkrétní požadavky, návrh, symboly implementace, identifikovaný pracovní strom a skutečný testovací log |

Dostupné podklady neobsahují původní zadání C01/C02 ani samostatné C04. Jejich úplný soulad tímto nelze potvrdit. Nové požadavky jsou přijaté rozhodnutím uživatele; výše jsou použita dostupná relevantní kritéria kvality, bez doplňování domnělých povinností do původního zadání. Kompletní odevzdání C03/C05, nezávislé hodnocení C06 a projektové výstupy C07/C08 mají širší rozsah než tento krok.

## Reprodukovatelné ověření

```sh
PYTHONDONTWRITEBYTECODE=1 SPORT_BOOKING_TEST_DB=/tmp/sport-booking-portal-requirements-20261107.sqlite3 .venv/bin/python sport_booking/manage.py test reservations --noinput --verbosity 2
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python sport_booking/manage.py makemigrations --check --dry-run
python3 scripts/update_docs.py --check
```

**Výsledek:** 18 nových testů portálu; celkem 67 testů, všechny prošly a žádný nebyl přeskočený. Zahrnuty jsou i dosavadní testy životního cyklu, rollbacku, migrace a souběhu nad dočasnou souborovou SQLite databází. Nová změna nevyžaduje migraci. Ověřeny jsou také symboly a lokální odkazy v dokumentaci.
