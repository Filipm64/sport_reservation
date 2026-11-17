# C09 — rozsah změny, testovací plán a release záznam

Datum přípravy: **17. 11. 2026**. Podklad:
[zadání C09](../../assigments/C09_ZADANI_CZ_EN_PODROBNE.html).

**Stav: krok 2 — implementace připravená v pracovním stromu.**
Automatizované implementační ověření: **123 testů prošlo**, bez přeskočení,
včetně souborové SQLite a souběhu. Automatizace a workflow GitHub CI jsou
připravené (část 6); skutečný vzdálený běh je NOT RUN. Review diffu spolužákem, nezávislá
reprodukce, vizuální kontrola a release rozhodnutí ještě následují.
Vlastníkem navazující práce je tým projektu. Očekávání v mapě níže jsou
původní test basis; skutečné provedení rozepisuje část 5.

## 1. Převzaté rozhodnutí a identita vstupu

- Change Request: [CR-C08-01](../requirements/C08-change-request.md),
  části 2–3 obsahují přijatá pravidla a AC-01 až AC-15, část 6 review
  a vypořádání připomínky. Rozhodnutí: **ACCEPT**, upravená varianta A.
- Podle sdělení uživatele spolužák schválil návrh a připomínkoval nastavení
  lhůty provozovatelem. Uživatel přijal ukládání konkrétní lhůty k rezervaci
  při vytvoření. Záznam byl doplněn 17. 11. 2026; jméno hodnotitele a datum
  samotného review nebyly sděleny. Nejde o review implementace.
- Historická aplikační baseline C08:
  `cd3c4ddc8dbc47d83483441c51b8d8a7ce87281c`.
  [Původní dva integrační testy a jejich důkazy](c08-cancellation-baseline.md)
  zůstávají zachované.
- **Before pro implementaci C09:**
  `ae698d94a0daa9b31eea3fde9730b6cd40891d0f` (`Fix in change request`).
  Při přípravě kroku 1 nebyly vůči tomuto commitu změněné aplikační zdroje.
  Schéma reservations končí migrací `0003_remove_draft_lifecycle`.
  Závislost v repozitáři: `Django==6.1.1`.
- Schválené upřesnění v Change Requestu bylo při přípravě kroku 1
  **necommitnuté**. SHA-256 tehdejšího obsahu před doplněním stavu implementace:
  `b63f0bcefe0f7cc417c1e4fe59e10ac96612045881cf4c29c251fc8bfa9ffd85`.
  Samotný before commit neobsahuje nové upřesnění požadavku. Samostatný
  přípravný commit nebyl vytvořen; dokumentace i implementace zůstávají
  jako kontrolovatelný diff a nové soubory. Před označením RC uložit změny
  do commitu a doplnit after hash. Testovaný obsah identifikuje manifest
  SHA-256 souborů v implementačním logu (část 5).
- Lokální změny `.DS_Store` a `sport_booking/db.sqlite3` nejsou vstupem
  ověření ani součástí plánované změny. Testy připraví vlastní data.
- **After commit/tag a release artefakt:** zatím nevznikly; implementace
  je v pracovním stromu. Doplní se při identifikaci RC.

## 2. Nejmenší schválená změna

Provozovatel nastaví pro sportoviště storno lhůtu v celých nezáporných
minutách, výchozí hodnota je 120. Při vytvoření rezervace server jednou
zkopíruje aktuální hodnotu sportoviště k rezervaci. Při dalších operacích
se použije uložená hodnota, i když se nastavení sportoviště mezitím změnilo.
Stávající rezervace při migraci dostanou 0 minut. Označení v1/v2 se nezavádí.

Potvrzenou rezervaci vlastník smí zrušit, pokud současně platí:

```text
server_now < starts_at
server_now <= starts_at - uložená lhůta
```

Výpočet používá UTC a skutečně uplynulé minuty; zobrazení Europe/Prague.
U nulové lhůty první podmínka zachovává zákaz zrušení přesně při začátku.
Čekající žádost lze stáhnout kdykoliv před začátkem bez ohledu na uloženou
lhůtu; při začátku vyprší podle dosavadního BR-07. Schválení její lhůtu
nemění. API při pozdním stornu potvrzené rezervace vrátí HTTP 409 a důvod.

Provozovatele v této změně představuje stávající oprávněný správce
`is_staff`; nevzniká nový model vlastnictví sportovišť. Nejmenší rozsah
nastavení je přes existující Django admin sportoviště, s oprávněním ke
změně Resource. Samostatný veřejný endpoint ani nový webový formulář
nastavení nejsou potřebné. Uložená lhůta rezervace bude v adminu pouze
pro čtení; zákazník ji nemůže ovlivnit vstupem webu ani API.

### Dopad na konkrétní části

| Část | Plánovaná změna | Zachované chování / kontrola |
| --- | --- | --- |
| [Modely](../../sport_booking/reservations/models.py), nové migrace v `reservations/migrations/` | Pole lhůty u Resource a Reservation, validace nezáporných celých minut; starým rezervacím 0, sportovištím 120 | Zachovat ID, vztahy, intervaly, stavy a dosavadní migrace; migraci ověřit na oddělené DB |
| [Doména](../../sport_booking/reservations/domain.py) | Přenášet nastavení v Resource/ResourceListing a uloženou lhůtu v Reservation/ReservationListing | Stejné stavy a přechody; doména bez HTTP a ORM |
| [Služba](../../sport_booking/reservations/services.py), `ReservationService.create/cancel` | Při vytvoření převzít lhůtu v chráněné transakci; při rušení použít uloženou hodnotu | Vlastník, expirace, konflikt, commit a rollback zůstávají ve společné cestě |
| [Pravidla](../../sport_booking/reservations/rules.py), `TimeRules.validate_cancellation` | U CONFIRMED kontrolovat uloženou lhůtu; sdílet výpočet pro rozhodování a prezentaci | PENDING_APPROVAL bez storno omezení; vždy zákaz zrušení při začátku |
| [Persistence](../../sport_booking/reservations/persistence.py), `load_resource/load_protected/save` a listingy | Číst a ukládat lhůtu; další změny stavu ji nepřepisují z Resource | SQLite IMMEDIATE, atomické uložení a dosavadní port DataStore |
| [API](../../sport_booking/reservations/api.py) | Ověřit chybu pozdního storna a nemožnost podstrčit lhůtu při vytvoření | Stejné endpointy, úspěšné statusy, autentizace a CSRF |
| [Portál](../../sport_booking/reservations/portal.py), [web](../../sport_booking/reservations/web_views.py), [šablona](../../sport_booking/reservations/templates/reservations/home.html) | Podmínky před vytvořením, uložená lhůta a možnost zrušení v přehledu, české vysvětlení odmítnutí | Web volá stejnou službu; čtení přehledu nemění DB; stará stránka neobchází serverový čas |
| [Admin](../../sport_booking/reservations/admin.py) | Editovat nastavení Resource, ukázat neměnnou lhůtu Reservation | Zachovat zákaz přidávání a mazání rezervací; nastavení jen oprávněným účtem |
| [Požadavky](../requirements/C08-change-request.md), REQ-05/10, BR-05/06 a [návrh životního cyklu](../design/reservation-lifecycle.md) | Při implementaci aktualizovat platný popis a dotčené návrhové dokumenty | Historické baseline a staré logy nepřepisovat |
| [Registr vazeb](traceability.json), [README](../../README.md) | Po vzniku implementace a testů doplnit symboly, vygenerovat vazby a popsat aktualizaci DB | Nepřidávat neexistující symboly jako již implementované |

### Oblasti bez změny a N/A

- Dostupnost, BR-02 a automatické zamítání konkurentů BR-08 se nemění.
  Úspěšné storno termín uvolní, odmítnuté ne; zamítnuté žádosti se neobnoví.
- Registrace, přihlášení, vlastnictví rezervace, schvalovací role, provozní
  doba, limit délky 2 hodin a horizont 30 dnů zůstávají stejné.
- Expirační příkaz zůstává; nový plánovač ani proces pro storno není potřeba.
- N/A: platby, poplatky, e-maily a výjimky správce nejsou součástí CR.
- N/A: nová DB technologie, cloud, Docker a nové runtime konfigurační
  proměnné nejsou pro tuto změnu potřeba. Lhůta je uložená v databázi.
- Nové ADR není potřeba: zachováváme společnou službu, port persistence
  a transakční koordinaci z [ADR-01](../architecture/decisions/ADR-001-reservation-coordination.md).
  Ověří se soulad existujícího popisu s implementací.

## 3. Testovací mapa před implementací

Závazná očekávání vycházejí z přijatého CR, nikoliv z budoucího kódu.
N-01 až N-14 jsou scénáře v části 7 Change Requestu. Níže uvedené skupiny
byly specifikované v kroku 1; sloupec Actual byl po implementačním běhu
aktualizován podle skutečných výsledků. Konkrétní symboly jsou v části 5
a v [generovaných vazbách REQ-05](coverage.md#req-05). Historické PASS C08
nejsou převzaté: TC-C08-01/02 se spustily znovu s explicitní nulovou lhůtou.

| Skupina / basis | Scénáře a předem určené expected | Úroveň a evidence | Actual C09 |
| --- | --- | --- | --- |
| Časová hranice — AC-01–04, N-01–04 | Pro start 10:00Z a lhůtu 120: storno 07:59:59Z a 08:00:00Z → 200/CANCELLED; 08:00:01Z a 10:00:00Z → 409/CONFIRMED | Unit pravidla + HTTP API → skutečná DB, nezávislé SQL čtení | PASS — automatizovaně |
| Staré podmínky — AC-05/08, N-05/08, TC-C08-01/02 | Lhůta 0: sekundu před startem → 200/CANCELLED, při startu → 409/CONFIRMED; schválení původní žádosti zachová 0 | Zachovat `CancellationBaselineTests` v [test_c08_baseline.py](../../sport_booking/reservations/test_c08_baseline.py), explicitně připravit nulovou lhůtu; přidat schválení staré žádosti | PASS — automatizovaně |
| Čekání a expirace — AC-06/07, N-06 | Pro 0, 120 i 240 minut před startem CANCELLED; při startu odmítnutí a committed EXPIRED | API/DB a regrese `test_expiry_exact_deadline_on_approve_cancel_and_command` v [tests.py](../../sport_booking/reservations/tests.py) | PASS — automatizovaně |
| Migrace a vznik — AC-12, N-07 | Migrace všech starých stavů zachová ID, stav, vztahy a interval, přiřadí 0; Resource dostane 120; nové vytvoření převezme nastavení | Nový migrační test po vzoru [test_migrations.py](../../sport_booking/reservations/test_migrations.py), skutečná DB před/po migraci a vytvoření přes službu | PASS — automatizovaně |
| Změna nastavení — AC-13, N-11/12 | Změna 120 → 240 zachová první rezervaci 120, nová dostane 240; původní čekající žádost i po schválení zachová 120; přesná hranice každé odpovídá její hodnotě | Integrační test admin → Resource → create/approve/cancel → committed SQL | PASS — automatizovaně |
| Nulová lhůta — AC-15, N-13 | I nová rezervace vytvořená při nastavení 0 jde zrušit sekundu před startem, při startu nikoliv | Unit + API/DB; odlišit od migrace staré rezervace | PASS — automatizovaně |
| Nastavení a vstupy — AC-12/14, N-14 | Oprávněný správce změní platnou hodnotu; záporná, desetinná a nečíselná hodnota ani neoprávněný zápis nastavení nezmění; zákaznický vstup nepřepíše převzatou lhůtu | Admin/formulář, oprávnění, POST/CSRF a skutečná DB; API i webové vytvoření | PASS — automatizovaně |
| Webová shoda — AC-10/11, N-09 | Podmínky viditelné před vytvořením, přehled ukazuje uloženou lhůtu a dostupnost storna; po překročení lhůty stará stránka odešle požadavek a server odmítne bez změny DB | Django web klient + kontrola šablony; ruční vizuální kontrola později samostatně zaznamenaná | PASS — automatizovaně; vizuální kontrola NOT RUN |
| Změna času — N-10 | Jarní i podzimní změna: rozdíl v UTC odpovídá uloženým minutám; hraniční rozhodnutí i místní zobrazení správné | Unit pravidla a webové zobrazení pro Europe/Prague | PASS — automatizovaně |
| Oprávnění a stavy — AC-09 | Cizí vlastník → dosavadní 404; nepřihlášený API uživatel → dosavadní odmítnutí; opakované storno a konečný stav → 409, žádná nepovolená změna | Regrese `test_authentication_ownership_and_unknown_resource`, `test_cancel_confirmed_releases_resource_and_rejects_repeat`, `test_confirm_endpoint_removed_and_terminal_states_cannot_reopen` v [tests.py](../../sport_booking/reservations/tests.py); doplnit kladnou lhůtu | PASS — automatizovaně |
| Dostupnost a konkurenti — BR-02/08 | Úspěšné storno uvolní termín; pozdní odmítnuté storno zachová blokaci; REJECTED konkurenti se neobnoví | API + nové vytvoření stejného intervalu, čtení stavů konkurentů; rozšířit dosavadní regresi | PASS — automatizovaně |
| Souběh — BR-06 | Po storno hranici, před startem: cancel první → CANCELLED a approve odmítnuto; approve první → CONFIRMED a cancel odmítnuto; při lhůtě 0 zachovat původní výsledek | Nové případy v [test_concurrency.py](../../sport_booking/reservations/test_concurrency.py), oddělená spojení do souborové DB; zachovat `test_approve_racing_cancel_finishes_cancelled` pro nulovou lhůtu | PASS — automatizovaně |
| Nastavení souběžně s vytvořením — AC-12/13 | Při souběhu změny 120 → 240 a vytvoření převezme rezervace jednu z těchto hodnot podle pořadí transakcí; žádná pozdější změna ji nepřepíše | Skutečná souborová DB, oddělená spojení; nezávislé čtení uložené lhůty | PASS — automatizovaně |
| Transakce a architektura | Selhání save/commit nepublikuje částečnou změnu; vstupní adaptéry neobcházejí služby a ORM port | Regrese [test_architecture.py](../../sport_booking/reservations/test_architecture.py), nová data s uloženou lhůtou | PASS — automatizovaně |

Pro tvrzení o persistenci použijeme `TransactionTestCase` a čtení novým
SQLite spojením po dokončení operace, podle postupu C08. Dotaz ověří také
uloženou lhůtu, ID, vlastníka, sportoviště a interval. Skutečná integrační
hranice je HTTP adaptér → služba → ORM → committed SQLite; mockovat lze
hodiny, nikoliv persistenci. Migrační test navíc projde reálnou změnou
schématu. Test klient nepředstavuje spuštění síťového serveru/prohlížeče.

Při přípravě starých regresních testů rozlišíme, zda prokazují původní
nulovou lhůtu, nebo obecné zachované chování. Testům s novými rezervacemi
nastavíme odpovídající čas a lhůtu; očekávání nesmíme měnit jen proto,
aby odpovídala výsledku implementace. Spustí se i celý balík `reservations`,
včetně provozní doby, rozvrhu, účtů a pěti stávajících testů souběhu.

## 4. Navazující ověření a hranice tohoto kroku

Implementační ověření bylo spuštěné z kořene projektu, s vyhrazenou cestou
k testovací DB (skutečné příkazy a log viz část 5). Pro opakování použijte
novou vyhrazenou cestu:

```sh
SPORT_BOOKING_TEST_DB=/tmp/sport-booking-c09-step3.sqlite3 .venv/bin/python sport_booking/manage.py test reservations --noinput --verbosity 2
.venv/bin/python sport_booking/manage.py check
.venv/bin/python sport_booking/manage.py makemigrations --check --dry-run
python3 scripts/update_docs.py --check
```

Test runner souborovou testovací DB vytváří a odstraňuje; nepoužívat cestu
k aplikační DB. K běhu uložit commit, skutečné prostředí, příkazy, exit code
a log, ke scénářům actual a verdikt. Skutečné provedení je uvedené v části 5;
samotná kontrola dokumentace neověřuje aplikaci.

Automatizační skript a push/PR CI jsou připravené v části 6. V dalších
krocích doplníme review implementace jiným členem, čisté sestavení/test/start a smoke-check
jiným člověkem, runtime a uzamčené závislosti, identitu artefaktu,
konfiguraci a schéma, postup aktualizace a omezení obnovy.
Návrat ke starému kódu nesmí být vydáván za bezpečný rollback po vzniku
rezervací s kladnou lhůtou: starý kód by jejich podmínky nerespektoval.

**Release rozhodnutí zatím nebylo provedeno.** Tento plán nedokládá READY
ani nasazení. Výsledek READY / CONDITIONAL / HOLD, odpovědného člověka
a důvody zaznamenáme podle skutečných důkazů v kroku 7.


## 5. Provedená implementace a její ověření — krok 2

Implementované chování odpovídá části 2: Resource má nastavitelné minuty,
Reservation povinně uložené minuty bez implicitní výchozí hodnoty pro nové
ORM zápisy. `ReservationService.create` hodnotu převezme v transakci;
`DjangoDataStore.save` ji při změně stavu nepřepisuje. Migrace
`0004_cancellation_notice` použije jednorázově 0 pro existující rezervace
(`preserve_default=False`), Resource dostane 120. Admin mění pouze nastavení
sportoviště, hodnota rezervace zůstává pouze pro čtení.

Rušení a zobrazení sdílejí `TimeRules.is_cancellation_open`. Web uvádí
nastavení před vytvořením, uložené podmínky v přehledu a české odmítnutí
po lhůtě. Pro opakovanou podzimní hodinu je deadline výslovně formátovaný
s CET/CEST a UTC offsetem: standardní Django filtr u této hodiny označení
pásma vynechával, což odhalil nový test a implementace to opravila.
API zachovává tvar úspěšné odpovědi a při pozdním stornu vrací 409.

### Skutečný běh

- Datum: 17. 11. 2026, zdroj je necommitnutý pracovní strom nad before výše.
- Python 3.14.6, Django 6.1.1, SQLite 3.53.2; OS a manifest SHA-256
  testovaných zdrojů jsou v [úplném implementačním logu](evidence/c09-implementation.log).
- Nastavení: `sport_booking.settings`, `USE_TZ=True`, Europe/Prague,
  SQLite IMMEDIATE, timeout 20 s. Kontrolované hodiny testů C09 používají
  start 20. 11. 2026 10:00Z místo původního ilustračního 10. 11.; relativní
  očekávání před/na/po hranici se nemění. DST případy používají rok 2027.
- Příkaz: `SPORT_BOOKING_TEST_DB=/tmp/sport-booking-c09-implementation-pass.sqlite3 .venv/bin/python sport_booking/manage.py test reservations --noinput --verbosity 2`.
- **Actual: 123 testů, všechny prošly, 0 přeskočených; exit code 0.**
  Součástí je 7 testů souběhu, reálné migrace a nové nezávislé committed
  SQL čtení. Testovací DB byla po běhu odstraněna.
- `manage.py check`, `makemigrations --check --dry-run`, kontrola
  dokumentace a `git diff --check`: výsledky jsou v logu.

### Konkrétní nové testy

V [test_cancellation_notice.py](../../sport_booking/reservations/test_cancellation_notice.py):

| Basis | Symbol testu | Actual |
| --- | --- | --- |
| N-01–04, AC-01–04 | `CancellationNoticeTests.test_cancellation_exact_boundaries_for_multiple_notices`, `test_zero_notice_and_started_reservations` | PASS, HTTP a samostatné SQL potvrzují očekávání pro 120/240/0 minut |
| N-06 | `CancellationNoticeTests.test_pending_can_be_withdrawn_until_start_then_expires` | PASS, CANCELLED před startem / EXPIRED při startu a po něm |
| N-07 | `CancellationNoticeMigrationTests.test_existing_terms_survive_migration_and_new_creation_uses_resource_notice` v [test_migrations.py](../../sport_booking/reservations/test_migrations.py) | PASS, všech pět starých stavů a ostatní pole zachované, 0 pro staré / 120 pro nové |
| N-08/12 | `CancellationNoticeTests.test_approval_preserves_saved_notice_after_configuration_change` | PASS pro 0 i 120 minut po změně sportoviště na 240 |
| N-09 | `CancellationNoticeTests.test_stale_web_page_cannot_bypass_deadline` | PASS, server odmítne, stav CONFIRMED a lhůta zachované, web vysvětlí důvod |
| N-10 | `CancellationClockTests.test_dst_uses_elapsed_utc_minutes_and_shared_display_rule`, `CancellationNoticeTests.test_dst_deadline_is_displayed_in_correct_local_offset` | PASS pro jaro i podzim, rozhodnutí i lokální čas s pásmem |
| N-11 | `CancellationNoticeTests.test_admin_change_affects_only_future_reservations` | PASS, stará 120 / nová 240, správné hraniční rozhodnutí |
| N-13 | `CancellationNoticeTests.test_zero_notice_and_started_reservations` | PASS, i nová s nulou zachovává ostrou hranici začátku |
| N-14 | `CancellationNoticeTests.test_invalid_or_unauthorized_setting_does_not_change_resource`, `test_customer_cannot_choose_notice_via_api_or_web`, `test_saved_notice_is_read_only_in_reservation_admin` | PASS, nastavení validované, oprávnění a CSRF zachované, zákazník lhůtu nepodstrčí |
| AC-09, transakce | `CancellationNoticeTests.test_ownership_authentication_and_repeat_preserve_saved_terms`, `test_cancellation_failure_rolls_back_status_and_saved_notice` | PASS, 401/404/409 a rollback bez změny lhůty |
| AC-11 | `CancellationNoticeTests.test_web_notice_and_read_only_listing_use_saved_value` | PASS, aktuální nastavení a uložené podmínky se zobrazují odděleně; čtení nemění DB |
| BR-02/08 | `CancellationNoticeTests.test_late_cancellation_keeps_allocation_and_rejected_competitors` | PASS, odmítnutí zachová blokaci, úspěch uvolní termín, REJECTED se neobnoví |
| BR-06 | `CancellationNoticeTests.test_both_serial_orders_of_approval_and_cancellation_after_deadline` | PASS, oba předem určené výsledky pořadí |

[Testy souběhu](../../sport_booking/reservations/test_concurrency.py):
`ReservationConcurrencyTests.test_approve_racing_cancel_after_notice_deadline_has_serial_outcome`
a `test_notice_change_racing_creation_saves_one_committed_setting` prošly nad
oddělenými spojeními skutečné souborové DB. Původních pět souběhových testů
také prošlo, včetně expirace v dalším procesu. TC-C08-01/02 prošly znovu;
jejich historický log zůstal nezměněný. Regrese architektury, chyb zápisu,
portálu, účtů, rozvrhu a provozní doby je součástí uvedených 123 testů.

### Co tento výsledek ještě neuzavírá

Implementace je připravená jako diff; after commit/tag a RC artefakt ještě
nejsou vytvořené. Neproběhlo peer review tohoto diffu ani čistá reprodukce
jiným člověkem, push/PR CI nebo vizuální prohlídka v prohlížeči (**NOT RUN**).
Django klient ověřuje HTML a HTTP cesty, nikoliv síťový server a interakce
v reálném prohlížeči. Nastavení se testovalo přes admin, souběh jeho zápisu
s vytvořením přes ekvivalentní atomický DB zápis. Bezpečný rollback je
popsané omezení, nikoliv ověřená schopnost.

Aplikační `sport_booking/db.sqlite3` nebyla migrována ani použita jako
fixture. Před spuštěním nové aplikace je nutné podle README zastavit
zapisující procesy, zálohovat DB a spustit `manage.py migrate`.
Následuje krok 3: nezávislé review implementace a zhodnocení evidence;
release rozhodnutí zůstává otevřené.


## 6. Automatizace a GitHub Actions

Dne 17. 11. 2026 byl doplněn [ověřovací skript](../../scripts/check.py)
a [workflow GitHub CI](../../.github/workflows/ci.yml). Workflow má triggery
push do `main`, pull_request bez filtru cílové větve (opened, synchronize,
reopened) a workflow_dispatch. Používá Ubuntu 24.04, Python 3.14 a instalaci
z `requirements.txt`. Token má pouze `contents: read`; uložené checkout
credentials jsou vypnuté. Novější aktualizace stejného PR/větve ruší starší
rozpracovaný běh. Job má limit 15 minut.

Společný příkaz po instalaci závislostí:

```sh
.venv/bin/python scripts/check.py
```

Kontroly: pip check, Django check, makemigrations --check --dry-run,
update_docs.py --check a všechny testy reservations. Skript vytvoří
jedinečnou dočasnou souborovou SQLite DB, kterou po běhu odstraní,
a nepoužívá aplikační DB jako testovací vstup. Zaznamenává prostředí,
commit, stav pracovního stromu, instalované verze, příkazy a exit kódy.
Selhání libovolné kontroly vede k celkovému nenulovému exit kódu.
Nevytváří release artefakt a nenahrazuje nezávislé review/reprodukci.

Lokální výsledek stejného skriptu: **PASS, exit code 0, 123 testů prošlo,
0 přeskočených**, včetně 7 souběhových testů; všechny doprovodné kontroly
prošly. [Skutečný lokální log](evidence/c09-automation.log). YAML workflow
byl lokálně načten YAML parserem a zkontrolovaný proti zamýšleným triggerům.
Tento běh proběhl na macOS s existujícími závislostmi; není to doklad
čisté instalace na Ubuntu ani nezávislé reprodukce.

GitHub nahraje `.ci-output/check.log` i při neúspěšném ověření jako artefakt
`verification-<run_id>-<run_attempt>` s uchováním 30 dní. Lokální log se
při každém běhu přepisuje; lze změnit `--log`. Selhání instalace ještě
před spuštěním skriptu je viditelné v logu instalačního kroku na GitHubu.

**Skutečný běh GitHub Actions: NOT RUN.** Změny zatím nebyly commitnuté
ani pushnuté. Po prvním běhu doplnit URL runu, testovaný SHA a výsledek.
Připravené workflow není důkazem zeleného CI. Zákaz merge při selhání
není nastavovaný tímto souborem; vyžadoval by pravidlo větve na GitHubu.
