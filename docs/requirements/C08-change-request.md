# C08 — Change Request: storno politika rezervací

**Číslo změny:** CR-C08-01 · **Datum:** 8. 11. 2026

Pravidla změny jsou odsouhlasená. Tento dokument popisuje, co chceme
změnit, proč, kterých částí aplikace se to dotkne a jak výsledek ověříme.
Nové chování zatím není naprogramované. Záznam současného stavu a výsledky
jeho testů jsou v [ověření C08](../verification/c08-cancellation-baseline.md).

## 1. Proč změnu chceme a jak aplikace funguje dnes

Dnes může vlastník zrušit potvrzenou rezervaci kdykoliv před jejím
začátkem, třeba i sekundu předem. Provozovatel tak nemusí mít čas nabídnout
uvolněný termín někomu jinému. Proto jsme se rozhodli zavést dvouhodinový
předstih pro rušení nových potvrzených rezervací.

Návrh přijal zadavatel projektu 8. 11. 2026. Konkrétní funkci jsme si
zvolili pro náš projekt; zadání C08 požaduje postup posouzení změny.

Výchozí verze aplikace je commit
`cd3c4ddc8dbc47d83483441c51b8d8a7ce87281c`. Její současná pravidla popisují
[REQ-05 — Zrušení rezervace](cancel-reservation.md),
[BR-05 — Zrušení](business-rules.md#br-05) a
[REQ-10 — Vlastní rezervace](my-reservations.md).
Rozhodování zajišťuje společná služba `ReservationService`, jak popisuje
[ADR-01](../architecture/decisions/ADR-001-reservation-coordination.md).

Současné chování jsme ověřili dvěma integračními testy:

- Sekundu před začátkem zrušení uspělo a do databáze se uložilo CANCELLED.
- Přesně při začátku se zrušení odmítlo a v databázi zůstalo CONFIRMED.

**Oba testy prošly.** Stav jsme po požadavku přečetli také samostatným
spojením do databáze. [Postup, prostředí a příprava dat](../verification/c08-cancellation-baseline.md)
a [úplný výstup testů](../verification/evidence/c08-cancellation-baseline.log)
jsou uložené zvlášť. Tyto výsledky dokazují dnešní chování; nové pravidlo
se bude testovat až po implementaci.

## 2. Co se má změnit

Dohodli jsme se na těchto pravidlech:

1. **Novou potvrzenou rezervaci lze zrušit nejpozději 2 hodiny před začátkem.**
   Přesně 2 hodiny předem je zrušení ještě povolené.
2. **Čekající žádost lze dál stáhnout kdykoliv před začátkem.**
   Její vypršení při začátku rezervace zůstává stejné.
3. **Dříve vytvořené rezervace si ponechají původní podmínky.**
   To platí i pro starou čekající žádost, kterou správce schválí až po
   zavedení změny. Rozhoduje vytvoření rezervace, ne datum jejího schválení.

Například novou potvrzenou rezervaci na 11:00 lze zrušit do 9:00 včetně.
V 9:00:01 už zrušení neprojde. Pokud jde o rezervaci vytvořenou před
zavedením změny, dál půjde zrušit kdykoliv před 11:00.

Rozhoduje čas na serveru při zpracování žádosti o zrušení. Dvě hodiny
znamenají 120 skutečných minut, a to i při změně letního času. Výpočet
použije UTC; uživatel uvidí místní čas Europe/Prague. Samotné otevření
stránky před lhůtou nezaručuje, že pozdější zrušení ještě projde.

Důležitý důsledek: rezervace může být vytvořená nebo schválená méně než
2 hodiny před začátkem. Pokud už podléhá novým pravidlům a je potvrzená,
vlastník ji pak zrušit nemůže. Dokud žádost čeká na schválení, stáhnout ji
může. Aplikace proto musí podmínky vysvětlit před vytvořením rezervace
a v přehledu ukázat, zda ji ještě lze zrušit.

V této změně neřešíme poplatky, platby, e-maily, výjimky správce ani různé
lhůty pro jednotlivá sportoviště. Neměníme ani pravidlo, že zrušení
potvrzené rezervace neobnoví žádosti, které kvůli ní byly zamítnuté.

## 3. Podle čeho poznáme, že změna funguje

Čísla AC slouží jako odkazy na konkrétní podmínky přijetí. V tabulce
„nová rezervace“ znamená vytvořená po zavedení nových pravidel.
Zrušení smí dál provést pouze vlastník a pouze v povoleném stavu.
HTTP 200 znamená úspěch; HTTP 409 odmítnutí kvůli pravidlům rezervace.

| ID | Situace | Očekávaný výsledek |
| --- | --- | --- |
| AC-01 | Nová potvrzená rezervace, více než 2 h do začátku | Zrušení uspěje: HTTP 200, v databázi CANCELLED |
| AC-02 | Nová potvrzená rezervace, přesně 2 h do začátku | Zrušení ještě uspěje, stejně jako AC-01 |
| AC-03 | Nová potvrzená rezervace, méně než 2 h do začátku | HTTP 409 s vysvětlením lhůty; v databázi zůstane CONFIRMED |
| AC-04 | Potvrzená rezervace právě začala nebo už začátek minul | HTTP 409; potvrzený stav se nezmění, u starých i nových rezervací |
| AC-05 | Původní potvrzená rezervace před začátkem | Zrušení dál uspěje i sekundu před začátkem |
| AC-06 | Čekající žádost před začátkem | Vlastník ji může stáhnout bez dvouhodinového omezení; uloží se CANCELLED |
| AC-07 | Čekající žádost při začátku nebo později | Zrušení se odmítne, HTTP 409; podle BR-07 se uloží EXPIRED |
| AC-08 | Stará žádost schválená po zavedení změny | Ponechá si původní podmínky a chová se podle AC-05 |
| AC-09 | Cizí či nepřihlášený uživatel, opakované zrušení nebo konečný stav | Zachovají se dosavadní oprávnění a odmítnutí; uložený stav se nezmění |
| AC-10 | Zrušení přes web i API | Obě cesty použijí stejná pravidla; server při odeslání znovu zkontroluje čas |
| AC-11 | Vytváření rezervace a osobní přehled | Uživatel se dozví podmínky před vytvořením a potom uvidí lhůtu nebo důvod, proč už zrušení není možné; staré podmínky budou rozlišitelné |
| AC-12 | Převod databáze a následné vytváření rezervací | Staré záznamy si zachovají původní podmínky, nové dostanou nové; uživatel si pravidla nemůže zvolit v API požadavku |

Úspěšné zrušení uvolní termín podle BR-02; odmítnuté zrušení ho neuvolní.
Zamítnuté žádosti se neobnovují, jak stanoví BR-08.

## 4. Kterých částí projektu se změna dotkne — Impact Matrix

Prošli jsme pravidla, místo rozhodování v kódu, ukládání do databáze,
web i API, testy a nasazení. Tabulka rozlišuje:

- **CHANGE — upravit:** tato část potřebuje změnu.
- **CHECK — ověřit:** má zůstat zachovaná, ale musíme ji zkontrolovat.
- **NO IMPACT — bez dopadu:** pro tuto změnu není potřeba zásah.

Úpravy a ověření zajistí tým projektu. Tabulka je plán práce, nikoliv
seznam již provedených úprav.

| Oblast a odkaz | Co a proč | Co udělat | Jak ověřit výsledek |
| --- | --- | --- | --- |
| [REQ-05](cancel-reservation.md), [BR-05 a BR-06](business-rules.md#br-05), [REQ-10](my-reservations.md) | CHANGE: jiné podmínky pro staré a nové rezervace; změní se i některé souběhy schválení a zrušení | Popsat nové lhůty, původní podmínky a pořadí současných operací | Porovnat pravidla s AC-01 až AC-12 a testy souběhu |
| [Životní cyklus](../design/reservation-lifecycle.md) | CHANGE: přechod z CONFIRMED do CANCELLED dostane nové časové podmínky; stavy se nemění | Upravit podmínky přechodu a odlišit čekající žádost | Testy stavových přechodů a přesných časových hranic |
| [services.py](../../sport_booking/reservations/services.py), `ReservationService.cancel`; [ADR-01](../architecture/decisions/ADR-001-reservation-coordination.md) | CHECK: obě vstupní cesty mají dál používat společnou službu | Zachovat načtení, ověření vlastníka, vypršení, kontrolu storna a bezpečné uložení | Integrační testy a kontrola závislostí |
| [rules.py](../../sport_booking/reservations/rules.py), `TimeRules.validate_cancellation` | CHANGE: dnes kontroluje jen začátek rezervace | Doplnit pravidlo podle stavu, verze politiky a serverového času | Testy před lhůtou, přesně na ní a po ní; změna letního času |
| [domain.py](../../sport_booking/reservations/domain.py), `Reservation`, `ReservationListing` | CHANGE: služba i osobní přehled musí znát podmínky konkrétní rezervace | Přenášet verzi politiky a určit poslední čas pro zrušení | Testy přenosu údajů a shody webu s rozhodnutím služby |
| [models.py](../../sport_booking/reservations/models.py), [dosavadní migrace](../../sport_booking/reservations/migrations/0003_remove_draft_lifecycle.py) | CHANGE u varianty A: rozlišit staré a nové záznamy v databázi | Přidat pole a migraci; starým řádkům přiřadit původní pravidla | Test převodu existující DB a vytvoření nové rezervace |
| [persistence.py](../../sport_booking/reservations/persistence.py), `load_protected`, `save`, `list_reservations` | CHANGE: načíst a uložit politiku bez změny při schválení nebo stornu | Rozšířit převod mezi databází a objekty aplikace | Načtení po uložení, AC-08/12 a samostatný SQL dotaz |
| [api.py](../../sport_booking/reservations/api.py), `ReservationApi.cancel` | CHECK: HTTP 409 už existuje, přibude důvod pozdního storna | Ověřit odpověď a zabránit volbě politiky klientem | Úspěšné i odmítnuté požadavky a oprávnění |
| [web_views.py](../../sport_booking/reservations/web_views.py), `reservation_action`, `_error_message`; [home.html](../../sport_booking/reservations/templates/reservations/home.html) | CHANGE: tlačítko dnes kontroluje jen začátek | Doplnit české vysvětlení, podmínky před vytvořením a správnou možnost zrušení | Webové testy včetně odeslání ze stránky otevřené před lhůtou |
| [portal.py](../../sport_booking/reservations/portal.py) | CHECK: předává údaje pro osobní přehled | Podle potřeby doplnit údaje o možnosti zrušení | Přehled používá správné podmínky a při čtení nemění DB |
| [admin.py](../../sport_booking/reservations/admin.py) | CHECK: admin nesmí obcházet společnou službu | Zachovat zákaz přidávání a mazání rezervací; nové pole nesmí umožnit přepsat politiku | Kontrola oprávnění a polí pouze pro čtení |
| Expirace, dostupnost, BR-02/07/08 a souběh BR-06 | CHECK: zachovat vypršení, zákaz kolizí a zamítání konkurentů; u nových rezervací zohlednit storno lhůtu | Spustit související testy pro obě politiky | Výsledky regresních a souběhových testů |
| Import a samostatný proces pro storno | NO IMPACT: takové vstupy v projektu nejsou | Nic nového nevytvářet | Kontrola skutečných cest zápisu; expirační příkaz zůstává zahrnutý výše |
| Přímé SQL nebo zápisy mimo službu | CHECK: databáze sama časové storno pravidlo nehlídá | Zkontrolovat aplikační zápisy a popsat omezení přímého SQL | Kontrola adminu, migrace a míst, kde se stav mění |
| [settings.py](../../sport_booking/sport_booking/settings.py), [README](../../README.md), nasazení | CHANGE postup aktualizace; CHECK časové a DB nastavení | Popsat migraci při zastavených zápisech, bez nového plánovače | Zkušební aktualizace a spuštění aplikace |
| [traceability.json](../verification/traceability.json), [testy](../../sport_booking/reservations/tests.py), [testy C08](../../sport_booking/reservations/test_c08_baseline.py) | CHANGE: část dosavadních očekávání bude platit jen pro staré rezervace | Doplnit nové testy a odkazy; původní výsledky uchovat | Výstup testů a kontrola dokumentace |

## 5. Jaké máme možnosti — Options Matrix

Obě varianty mají splnit stejná pravidla: 2 hodiny u nových potvrzených
rezervací, zachování starých podmínek a volné stažení čekající žádosti.
Liší se tím, jak poznáme, která pravidla konkrétní rezervaci patří.

| Varianta | Splní požadavky? | Výhody | Náklady a rizika | Jak ji ověřit |
| --- | --- | --- | --- | --- |
| **A — uložit verzi politiky ke každé rezervaci** | Ano, pokud se správně převedou původní data a údaje se přenesou všemi částmi aplikace | Z řádku v DB poznáme platná pravidla; schválení, restart ani další aktualizace je nezmění | Nové pole, migrace a úprava načítání; chybná výchozí hodnota by mohla změnit práva starých rezervací; návrat ke staré verzi nesmí údaj ztratit | Převod starých dat, nové vytvoření, načtení po uložení, pozdější schválení staré žádosti a časové hranice |
| **B — porovnávat datum vytvoření s pevným datem zavedení změny** | Ano, pokud se okamžik přepnutí jednoznačně nastaví a uchová | Využije existující `created_at`, bez nového pole | Správné chování závisí na trvalém nastavení data přepnutí; chyba při obnově nastavení může změnit podmínky existujících rezervací | Vytvoření před přepnutím, při něm a po něm; restart, obnova DB a nastavení, pozdější schválení staré žádosti |

**Doporučujeme variantu A.** Vyžaduje pole navíc a migraci, ale podmínky
rezervace zůstanou uložené přímo u ní. U varianty B bychom museli při každém
nasazení a obnově zachovat správné datum přepnutí.

Pokud neuděláme nic, aplikace zůstane funkční, ale pozdní storna budou dál
možná. Upozornění uživatelů, aby rušili včas, může dočasně pomoci;
požadovaný zákaz tím však nezajistíme.

## 6. Na čem jsme se dohodli

Zadavatel projektu **8. 11. 2026 schválil změnu pravidel** popsanou
v části 2. Výsledek rozhodnutí je **ACCEPT — změnu chceme zavést**.
Důvodem je čas, který provozovatel potřebuje k nabídnutí uvolněného termínu,
a současně zachování slíbených podmínek již vytvořených rezervací.

Pro provedení doporučujeme variantu A. Implementaci a ověření zajistí tým
projektu; konkrétní úkoly si rozdělí před zahájením práce. Tento dokument
zatím neznamená, že je změna naprogramovaná nebo otestovaná.


## 7. Co bude následovat při implementaci

Zadání C08 požaduje připravit předání do C09. Samostatné zadání C09 zatím
nemáme; následující body jsou náš plán, který podle něj případně upravíme.

1. Aktualizovat REQ-05, BR-05, BR-06, REQ-10 a popis stavových přechodů.
   Dosavadní texty zatím popisují běžící aplikaci.
2. Přidat k rezervaci verzi politiky: `v1` pro původní pravidla a `v2` pro
   nová. Při migraci přiřadit všem existujícím řádkům v1; novým rezervacím
   při vytváření v2. Pozdější schválení verzi nesmí změnit.
3. Doplnit načítání a ukládání verze. Pro potvrzenou v2 povolit zrušení
   do `starts_at - 2 hodiny` včetně. Zachovat ověření vlastníka, povolených
   stavů, vypršení žádosti a bezpečné uložení celé operace.
4. Upravit vysvětlení a tlačítko na webu podle stejných pravidel. API musí
   při pozdním stornu vrátit HTTP 409 s jasným důvodem.
5. Doplnit nové testy a ověřit, že ostatní funkce dál fungují. Použít
   oddělenou souborovou testovací DB, spustit také `manage.py check`,
   `makemigrations --check --dry-run` a `python3 scripts/update_docs.py --check`.
6. Uložit výstup testů, označit výsledný commit a migraci, vyzkoušet
   spuštění z čistého stažení projektu a rozhodnout o nasazení.

### Připravené testy nového chování

Tyto scénáře se zatím **nespouštěly**. Pro příklady používáme začátek
rezervace `2026-11-10T10:00:00Z`; `Z` označuje UTC. V Praze je tehdy 11:00.
Po požadavku vždy ověříme i skutečně uložená data.

| Případ | Vstup | Očekávaný výsledek |
| --- | --- | --- |
| N-01 | Nová potvrzená rezervace, zrušení v `07:59:59Z` | HTTP 200, v DB CANCELLED |
| N-02 | Totéž v `08:00:00Z` | HTTP 200, v DB CANCELLED |
| N-03 | Totéž v `08:00:01Z` | HTTP 409, v DB CONFIRMED |
| N-04 | Totéž v `10:00:00Z` | HTTP 409, v DB CONFIRMED |
| N-05 | Původní potvrzená rezervace, zrušení v `09:59:59Z` | HTTP 200, v DB CANCELLED |
| N-06 | Čekající žádost obou verzí, zrušení v `09:59:59Z`, potom samostatný případ v `10:00:00Z` | Před začátkem CANCELLED; při začátku odmítnutí a EXPIRED |
| N-07 | Migrace DB se starými rezervacemi všech stavů a následné vytvoření nové | Staré mají v1, nezměněné ID, stav a interval; nová má v2 |
| N-08 | Schválení staré čekající žádosti a zrušení sekundu před začátkem | Zůstala v1, zrušení uspěje |
| N-09 | Stránka otevřená před lhůtou, požadavek na zrušení dorazí po ní | Server odmítne, web vysvětlí důvod, DB beze změny |
| N-10 | Storno lhůta přes změnu zimního a letního času | Odstup 120 skutečných minut a správně zobrazený místní čas |

Dále ověříme oprávnění, opakované zrušení, konečné stavy, uvolnění termínu
po úspěchu, zachování blokace po odmítnutí, neobnovení zamítnutých žádostí
a vypršení čekajících žádostí.

Zvlášť otestujeme současné schválení a zrušení nové žádosti méně než
2 hodiny před začátkem. Pokud se nejdřív provede zrušení, schválení už
neprojde. Pokud se nejdřív provede schválení, žádost se potvrdí a zrušení
už neprojde kvůli lhůtě. Stará v1 zachová dosavadní chování podle BR-06.

Původní TC-C08-01/02 ponecháme jako testy starých podmínek v1. Po změně
schématu jim výslovně připravíme původní politiku. Historický výstup testů
nebudeme přepisovat podle nového chování.

### Jak změnu nasadit a co při potížích

Před aktualizací zastavíme server a ostatní procesy zapisující do DB,
vytvoříme zálohu a provedeme migraci. Ověříme, že staré záznamy mají v1
a nové vytváření používá v2. Potom obnovíme provoz. Stará a nová verze
aplikace nesmějí současně vytvářet rezervace.

Návrat ke starému kódu po vzniku v2 rezervací by znovu dovolil jejich pozdní
storno. Při opravě proto zachováme uložené verze politiky a použijeme kód,
který obě pravidla respektuje. Pouhá obnova staré zálohy by navíc ztratila
novější rezervace a změny; není automatickým řešením.

Největší rizika jsou chybné přiřazení politiky starým datům, odlišná pravidla
webu a API nebo přepsání politiky při schválení. Navazují na R-04
(nesoulad dokumentace a kódu), R-01 (databáze a souběh) a R-03
(opakovatelné spuštění) v [registru rizik](../history/evidence-and-evolution.md).
Zatím nemáme důkaz, že navržené úpravy tato rizika ošetřily. To ověříme
během implementace a testování. Posouzení znovu otevřeme při změně lhůty,
databáze nebo při rozdílném chování webu a API.

## 8. Co máme hotové

- Popsaný výchozí stav a dva provedené testy: hotovo, oba prošly.
- Návrh změny a souhlas s pravidly: hotovo.
- Analýza dopadů, dvě varianty a doporučení: připravené.
- Plán implementace a ověření pro navazující cvičení: připravený.
- Implementace a testy nových pravidel: zatím neprovedené, následují později.

[Přehled požadavků](README.md) · [Ověřování](../verification/README.md)
