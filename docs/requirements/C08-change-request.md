# C08 — Change Request: storno politika rezervací

**Číslo změny:** CR-C08-01 · **Datum:** 8. 11. 2026

Pravidla změny jsou odsouhlasená. Tento dokument popisuje, co chceme
změnit, proč, kterých částí aplikace se to dotkne a jak výsledek ověříme.
Implementace podle tohoto rozhodnutí je připravená v pracovním stromu;
[stav a ověření C09](../verification/c09-release-record.md) rozlišují
provedené kontroly od zbývajícího review a release kroků. Historický stav
a jeho testy jsou v [ověření C08](../verification/c08-cancellation-baseline.md).

## 1. Proč změnu chceme a jak aplikace funguje dnes

Dnes může vlastník zrušit potvrzenou rezervaci kdykoliv před jejím
začátkem, třeba i sekundu předem. Provozovatel tak nemusí mít čas nabídnout
uvolněný termín někomu jinému. Proto jsme se rozhodli zavést dvouhodinový
předstih pro rušení nových potvrzených rezervací. Po připomínce z review
jsme 17. 11. 2026 návrh rozšířili: lhůtu nastavuje provozovatel pro každé
sportoviště a konkrétní hodnota se uloží při vytvoření rezervace.
Dvě hodiny budou výchozí nastavení sportoviště.

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

1. **Provozovatel nastavuje storno lhůtu pro každé sportoviště v celých
   nezáporných minutách; výchozí hodnota je 120 minut.** Při vytvoření
   rezervace server zkopíruje aktuální nastavení sportoviště k rezervaci.
   Potvrzenou rezervaci lze zrušit nejpozději o tuto uloženou lhůtu před
   začátkem; přesně na hranici je zrušení ještě povolené, vždy však pouze
   před začátkem. Hodnota 0 znamená možnost zrušení kdykoliv před začátkem.
2. **Čekající žádost lze dál stáhnout kdykoliv před začátkem.**
   Její vypršení při začátku rezervace zůstává stejné.
3. **Dříve vytvořené rezervace si ponechají původní podmínky.**
   To platí i pro starou čekající žádost, kterou správce schválí až po
   zavedení změny. Při migraci dostanou uloženou lhůtu 0 minut.
4. **Změna nastavení sportoviště ovlivní pouze budoucí rezervace.**
   Uložená lhůta se při schválení, zrušení ani změně nastavení nepřepisuje.
   Rozhoduje nastavení při vytvoření, ne datum schválení. Zákazník nesmí
   vlastní lhůtu zadat ani změnit přes web či API.

Například novou potvrzenou rezervaci na 11:00 s uloženou lhůtou 120 minut
lze zrušit do 9:00 včetně.
V 9:00:01 už zrušení neprojde. Pokud jde o rezervaci vytvořenou před
zavedením změny, dál půjde zrušit kdykoliv před 11:00.

Rozhoduje čas na serveru při zpracování žádosti o zrušení. Uložená lhůta
znamená skutečně uplynulé minuty, a to i při změně letního času. Výpočet
použije UTC; uživatel uvidí místní čas Europe/Prague. Samotné otevření
stránky před lhůtou nezaručuje, že pozdější zrušení ještě projde.

Důležitý důsledek: rezervace může být vytvořená nebo schválená až po
uplynutí své storno lhůty. Pokud už je potvrzená,
vlastník ji pak zrušit nemůže. Dokud žádost čeká na schválení, stáhnout ji
může. Aplikace proto musí podmínky vysvětlit před vytvořením rezervace
a v přehledu ukázat, zda ji ještě lze zrušit.

V této změně neřešíme poplatky, platby, e-maily ani výjimky správce.
Neměníme ani pravidlo, že zrušení
potvrzené rezervace neobnoví žádosti, které kvůli ní byly zamítnuté.

## 3. Podle čeho poznáme, že změna funguje

Čísla AC slouží jako odkazy na konkrétní podmínky přijetí. V tabulce
„nová rezervace“ znamená vytvořená po zavedení nových pravidel.
AC-01 až AC-03 používají uloženou lhůtu 120 minut; stejné hranice
se ověří také pro jinou nastavenou lhůtu.
Zrušení smí dál provést pouze vlastník a pouze v povoleném stavu.
HTTP 200 znamená úspěch; HTTP 409 odmítnutí kvůli pravidlům rezervace.

| ID | Situace | Očekávaný výsledek |
| --- | --- | --- |
| AC-01 | Nová potvrzená rezervace, více než 2 h do začátku | Zrušení uspěje: HTTP 200, v databázi CANCELLED |
| AC-02 | Nová potvrzená rezervace, přesně 2 h do začátku | Zrušení ještě uspěje, stejně jako AC-01 |
| AC-03 | Nová potvrzená rezervace, méně než 2 h do začátku | HTTP 409 s vysvětlením lhůty; v databázi zůstane CONFIRMED |
| AC-04 | Potvrzená rezervace právě začala nebo už začátek minul | HTTP 409; potvrzený stav se nezmění, u starých i nových rezervací |
| AC-05 | Původní potvrzená rezervace před začátkem | Zrušení dál uspěje i sekundu před začátkem |
| AC-06 | Čekající žádost před začátkem | Vlastník ji může stáhnout bez omezení uloženou lhůtou; uloží se CANCELLED |
| AC-07 | Čekající žádost při začátku nebo později | Zrušení se odmítne, HTTP 409; podle BR-07 se uloží EXPIRED |
| AC-08 | Stará žádost schválená po zavedení změny | Ponechá si původní podmínky a chová se podle AC-05 |
| AC-09 | Cizí či nepřihlášený uživatel, opakované zrušení nebo konečný stav | Zachovají se dosavadní oprávnění a odmítnutí; uložený stav se nezmění |
| AC-10 | Zrušení přes web i API | Obě cesty použijí stejná pravidla; server při odeslání znovu zkontroluje čas |
| AC-11 | Vytváření rezervace a osobní přehled | Uživatel se dozví podmínky před vytvořením a potom uvidí lhůtu nebo důvod, proč už zrušení není možné; staré podmínky budou rozlišitelné |
| AC-12 | Převod databáze a následné vytváření rezervací | Staré záznamy dostanou 0 minut, sportoviště výchozích 120 minut; nové rezervace převezmou aktuální lhůtu sportoviště ze serveru, nikoliv od zákazníka |
| AC-13 | Oprávněný provozovatel změní lhůtu sportoviště ze 120 na 240 minut | Existující rezervace si ponechají 120 minut, nová převezme 240 minut; schválení uloženou hodnotu nemění |
| AC-14 | Nastavení lhůty sportoviště | Oprávněný provozovatel může nastavit celé nezáporné minuty; neplatný vstup nebo neoprávněná změna se odmítne bez změny nastavení |
| AC-15 | Potvrzená rezervace s uloženou lhůtou 0 minut | Sekundu před začátkem zrušení uspěje, přesně při začátku a později se odmítne |

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
| [REQ-05](cancel-reservation.md), [BR-05 a BR-06](business-rules.md#br-05), [REQ-10](my-reservations.md) | CHANGE: jiné podmínky pro staré a nové rezervace; změní se i některé souběhy schválení a zrušení | Popsat nové lhůty, původní podmínky a pořadí současných operací | Porovnat pravidla s AC-01 až AC-15 a testy souběhu |
| [Životní cyklus](../design/reservation-lifecycle.md) | CHANGE: přechod z CONFIRMED do CANCELLED dostane nové časové podmínky; stavy se nemění | Upravit podmínky přechodu a odlišit čekající žádost | Testy stavových přechodů a přesných časových hranic |
| [services.py](../../sport_booking/reservations/services.py), `ReservationService.cancel`; [ADR-01](../architecture/decisions/ADR-001-reservation-coordination.md) | CHECK: obě vstupní cesty mají dál používat společnou službu | Zachovat načtení, ověření vlastníka, vypršení, kontrolu storna a bezpečné uložení | Integrační testy a kontrola závislostí |
| [rules.py](../../sport_booking/reservations/rules.py), `TimeRules.validate_cancellation` | CHANGE: dnes kontroluje jen začátek rezervace | Doplnit pravidlo podle stavu, uložené lhůty a serverového času | Testy před lhůtou, přesně na ní a po ní; změna letního času |
| [domain.py](../../sport_booking/reservations/domain.py), `Reservation`, `ReservationListing` | CHANGE: služba i osobní přehled musí znát podmínky konkrétní rezervace | Přenášet uloženou lhůtu a určit poslední čas pro zrušení | Testy přenosu údajů a shody webu s rozhodnutím služby |
| [models.py](../../sport_booking/reservations/models.py), [dosavadní migrace](../../sport_booking/reservations/migrations/0003_remove_draft_lifecycle.py) | CHANGE u upravené varianty A: uložit lhůtu u sportoviště i rezervace | Přidat pole a migraci; starým rezervacím přiřadit 0 minut, sportovištím 120 minut | Test převodu existující DB a vytvoření nové rezervace |
| [persistence.py](../../sport_booking/reservations/persistence.py), `load_protected`, `save`, `list_reservations` | CHANGE: při vytvoření zkopírovat aktuální lhůtu sportoviště a zachovat ji při dalších operacích | Rozšířit převod mezi databází a objekty aplikace | Načtení po uložení, AC-08/12 a samostatný SQL dotaz |
| [api.py](../../sport_booking/reservations/api.py), `ReservationEndpoint.cancel` | CHECK: HTTP 409 už existuje, přibude důvod pozdního storna | Ověřit odpověď a zabránit volbě lhůty zákazníkem | Úspěšné i odmítnuté požadavky a oprávnění |
| [web_views.py](../../sport_booking/reservations/web_views.py), `reservation_action`, `_error_message`; [home.html](../../sport_booking/reservations/templates/reservations/home.html) | CHANGE: tlačítko dnes kontroluje jen začátek | Doplnit české vysvětlení, podmínky před vytvořením a správnou možnost zrušení | Webové testy včetně odeslání ze stránky otevřené před lhůtou |
| [portal.py](../../sport_booking/reservations/portal.py) | CHECK: předává údaje pro osobní přehled | Podle potřeby doplnit údaje o možnosti zrušení | Přehled používá správné podmínky a při čtení nemění DB |
| [admin.py](../../sport_booking/reservations/admin.py) | CHECK: admin nesmí obcházet společnou službu | Zachovat zákaz přidávání a mazání rezervací; pole lhůty rezervace musí být pouze pro čtení | Kontrola oprávnění a polí pouze pro čtení |
| Nastavení sportoviště — [admin.py](../../sport_booking/reservations/admin.py), případné webové nastavení | CHANGE: provozovatel nastavuje lhůtu konkrétního sportoviště | Zpřístupnit nastavení oprávněnému správci (`is_staff` podle současného modelu rolí); validovat celé nezáporné minuty; zákazník nastavení nemění | AC-13/14; změna nezasáhne existující rezervace |
| Expirace, dostupnost, BR-02/07/08 a souběh BR-06 | CHECK: zachovat vypršení, zákaz kolizí a zamítání konkurentů; u nových rezervací zohlednit storno lhůtu | Spustit související testy pro nulovou i kladnou lhůtu | Výsledky regresních a souběhových testů |
| Import a samostatný proces pro storno | NO IMPACT: takové vstupy v projektu nejsou | Nic nového nevytvářet | Kontrola skutečných cest zápisu; expirační příkaz zůstává zahrnutý výše |
| Přímé SQL nebo zápisy mimo službu | CHECK: databáze sama časové storno pravidlo nehlídá | Zkontrolovat aplikační zápisy a popsat omezení přímého SQL | Kontrola adminu, migrace a míst, kde se stav mění |
| [settings.py](../../sport_booking/sport_booking/settings.py), [README](../../README.md), nasazení | CHANGE postup aktualizace; CHECK časové a DB nastavení | Popsat migraci při zastavených zápisech, bez nového plánovače | Zkušební aktualizace a spuštění aplikace |
| [traceability.json](../verification/traceability.json), [testy](../../sport_booking/reservations/tests.py), [testy C08](../../sport_booking/reservations/test_c08_baseline.py) | CHANGE: část dosavadních očekávání bude platit jen pro staré rezervace | Doplnit nové testy a odkazy; původní výsledky uchovat | Výstup testů a kontrola dokumentace |

## 5. Jaké máme možnosti — Options Matrix

Původní posouzení porovnávalo následující dvě varianty pro pevnou
dvouhodinovou lhůtu. Po review je varianta A upravena na uložení konkrétní
lhůty v minutách místo označení v1/v2. Tabulka zachovává původní alternativy;
varianta B s jediným datem přepnutí nepokrývá opakované změny nastavení
jednotlivých sportovišť bez další historie nastavení.

| Varianta | Splní požadavky? | Výhody | Náklady a rizika | Jak ji ověřit |
| --- | --- | --- | --- | --- |
| **A — uložit verzi politiky ke každé rezervaci** | Ano, pokud se správně převedou původní data a údaje se přenesou všemi částmi aplikace | Z řádku v DB poznáme platná pravidla; schválení, restart ani další aktualizace je nezmění | Nové pole, migrace a úprava načítání; chybná výchozí hodnota by mohla změnit práva starých rezervací; návrat ke staré verzi nesmí údaj ztratit | Převod starých dat, nové vytvoření, načtení po uložení, pozdější schválení staré žádosti a časové hranice |
| **B — porovnávat datum vytvoření s pevným datem zavedení změny** | Ano, pokud se okamžik přepnutí jednoznačně nastaví a uchová | Využije existující `created_at`, bez nového pole | Správné chování závisí na trvalém nastavení data přepnutí; chyba při obnově nastavení může změnit podmínky existujících rezervací | Vytvoření před přepnutím, při něm a po něm; restart, obnova DB a nastavení, pozdější schválení staré žádosti |

**Volíme upravenou variantu A: konkrétní lhůtu uloženou u rezervace.**
Sportoviště má měnitelné nastavení, rezervace jeho hodnotu převezme pouze
při vytvoření. Při rušení se použije uložená hodnota bez dohledávání historie
nastavení. Vyžaduje to pole u sportoviště i rezervace, migraci a oprávněné
nastavení provozovatelem; testy musí pokrýt také pozdější změnu nastavení.

Pokud neuděláme nic, aplikace zůstane funkční, ale pozdní storna budou dál
možná. Upozornění uživatelů, aby rušili včas, může dočasně pomoci;
požadovaný zákaz tím však nezajistíme.

## 6. Na čem jsme se dohodli

Zadavatel projektu **8. 11. 2026 schválil původní změnu pravidel**
s pevnou dvouhodinovou lhůtou. Dne **17. 11. 2026 přijal upřesnění po review**
popsané v aktuální části 2. Výsledek rozhodnutí je **ACCEPT — změnu chceme zavést**.
Důvodem je čas, který provozovatel potřebuje k nabídnutí uvolněného termínu,
a současně zachování slíbených podmínek již vytvořených rezervací.

Pro provedení je zvolena **upravená varianta A — uložit konkrétní storno
lhůtu v minutách ke každé rezervaci**. Uživatel dne 17. 11. 2026 potvrdil,
že spolužák návrh schválil, a předal připomínku k review:

- **Připomínka:** lhůtu má určovat provozovatel sportoviště.
- **Vypořádání — ACCEPT:** provozovatel nastaví lhůtu sportoviště a server
  ji při vytvoření zkopíruje k rezervaci. Pozdější změna nastavení ani
  schválení žádosti uloženou hodnotu nezmění. Není potřeba rozlišovat v1/v2.
- **Dopad:** doplněno nastavení sportoviště, upraveno ukládání rezervace,
  AC-12 až AC-15 a testy změny nastavení; staré rezervace mají 0 minut.

Záznam vychází ze sdělení uživatele; jméno hodnotitele a datum samotného
review nebyly uvedeny. Uživatel toto řešení přijal 17. 11. 2026.
Review implementace proběhne až nad konkrétním diffem v C09.

Implementaci a ověření zajistí tým projektu; konkrétní úkoly si rozdělí
před zahájením práce. Samotné přijetí návrhu neprokazuje implementaci; její aktuální stav
a výsledky jsou v [záznamu C09](../verification/c09-release-record.md).


## 7. Co bude následovat při implementaci

Navazujeme podle [zadání C09](../../assigments/C09_ZADANI_CZ_EN_PODROBNE.html).
Následující body tvoří implementační část; C09 dále vyžaduje review diffu,
automatizované ověření a log, nezávislou čistou reprodukci jiným členem,
identitu artefaktu a rozhodnutí o release candidate.

1. Aktualizovat REQ-05, BR-05, BR-06, REQ-10 a popis stavových přechodů.
   Dosavadní texty zatím popisují běžící aplikaci.
2. Přidat nastavení lhůty sportoviště v minutách (výchozí 120) a uloženou
   lhůtu rezervace. Existujícím rezervacím při migraci přiřadit 0 minut.
   Při vytvoření server převezme aktuální nastavení sportoviště; pozdější
   schválení ani změna nastavení hodnotu rezervace nesmí změnit.
3. Doplnit načítání a ukládání lhůty a její nastavení oprávněným
   provozovatelem. Pro potvrzenou rezervaci povolit zrušení do
   `starts_at - uložená lhůta` včetně, vždy však pouze před začátkem.
   Zachovat ověření vlastníka, povolených stavů, vypršení žádosti
   a bezpečné uložení celé operace.
4. Upravit vysvětlení a tlačítko na webu podle stejných pravidel. API musí
   při pozdním stornu vrátit HTTP 409 s jasným důvodem.
5. Doplnit nové testy a ověřit, že ostatní funkce dál fungují. Použít
   oddělenou souborovou testovací DB, spustit také `manage.py check`,
   `makemigrations --check --dry-run` a `python3 scripts/update_docs.py --check`.
6. Uložit výstup testů, označit výsledný commit a migraci, vyzkoušet
   spuštění z čistého stažení projektu a rozhodnout o nasazení.

### Připravené testy nového chování

Scénáře byly připravené před implementací. Aktuální provedení a konkrétní
testovací symboly zachycuje [záznam C09](../verification/c09-release-record.md);
tato tabulka uchovává jejich původní očekávání. Pro příklady používáme začátek
rezervace `2026-11-10T10:00:00Z`; `Z` označuje UTC. V Praze je tehdy 11:00.
Po požadavku vždy ověříme i skutečně uložená data. N-01 až N-04
používají rezervaci s uloženou lhůtou 120 minut.

| Případ | Vstup | Očekávaný výsledek |
| --- | --- | --- |
| N-01 | Nová potvrzená rezervace, zrušení v `07:59:59Z` | HTTP 200, v DB CANCELLED |
| N-02 | Totéž v `08:00:00Z` | HTTP 200, v DB CANCELLED |
| N-03 | Totéž v `08:00:01Z` | HTTP 409, v DB CONFIRMED |
| N-04 | Totéž v `10:00:00Z` | HTTP 409, v DB CONFIRMED |
| N-05 | Původní potvrzená rezervace, zrušení v `09:59:59Z` | HTTP 200, v DB CANCELLED |
| N-06 | Čekající žádost s nulovou i kladnou lhůtou, zrušení v `09:59:59Z`, potom samostatný případ v `10:00:00Z` | Před začátkem CANCELLED; při začátku odmítnutí a EXPIRED |
| N-07 | Migrace DB se starými rezervacemi všech stavů a následné vytvoření nové | Staré mají 0 minut, nezměněné ID, stav a interval; sportoviště má výchozích 120 minut a nová rezervace převezme aktuální nastavení |
| N-08 | Schválení staré čekající žádosti a zrušení sekundu před začátkem | Zůstala jí lhůta 0 minut, zrušení uspěje |
| N-09 | Stránka otevřená před lhůtou, požadavek na zrušení dorazí po ní | Server odmítne, web vysvětlí důvod, DB beze změny |
| N-10 | Storno lhůta přes změnu zimního a letního času | Odstup odpovídá uloženým skutečným minutám a správně zobrazenému místnímu času |
| N-11 | Vytvořit rezervaci při nastavení 120 minut, změnit nastavení na 240 a vytvořit další na jiný termín | První má stále 120, druhá 240 minut; hranice obou se vyhodnotí podle uložené hodnoty |
| N-12 | Vytvořit čekající žádost při nastavení 120 minut, změnit nastavení na 240 a schválit ji | Žádost si po schválení zachová 120 minut |
| N-13 | Nastavení 0 minut; zrušení nové potvrzené rezervace sekundu před začátkem a v samostatném případě při začátku | Před začátkem HTTP 200 / CANCELLED; při začátku HTTP 409 / CONFIRMED |
| N-14 | Neoprávněný uživatel nebo neplatná hodnota nastavení; zákazník podstrčí vlastní lhůtu při vytvoření | Nastavení se neoprávněně ani neplatně nezmění; rezervace nemůže převzít lhůtu od zákazníka |

Dále ověříme oprávnění, opakované zrušení, konečné stavy, uvolnění termínu
po úspěchu, zachování blokace po odmítnutí, neobnovení zamítnutých žádostí
a vypršení čekajících žádostí.

Zvlášť otestujeme současné schválení a zrušení žádosti po posledním čase
pro storno podle uložené kladné lhůty, ale ještě před začátkem rezervace.
Pokud se nejdřív provede zrušení, schválení už
neprojde. Pokud se nejdřív provede schválení, žádost se potvrdí a zrušení
už neprojde kvůli lhůtě. Rezervace s nulovou lhůtou zachová dosavadní
chování podle BR-06. Při souběhu změny nastavení a vytvoření ověříme,
že rezervace převezme jednu platnou hodnotu při vytvoření a dál ji uchová.

Původní TC-C08-01/02 ponecháme jako testy starých podmínek. Po změně
schématu jim výslovně připravíme uloženou lhůtu 0 minut. Historický výstup testů
nebudeme přepisovat podle nového chování.

### Jak změnu nasadit a co při potížích

Před aktualizací zastavíme server a ostatní procesy zapisující do DB,
vytvoříme zálohu a provedeme migraci. Ověříme, že staré rezervace mají
0 minut, sportoviště výchozích 120 minut a nové vytváření přebírá aktuální
nastavení sportoviště. Potom obnovíme provoz. Stará a nová verze
aplikace nesmějí současně vytvářet rezervace.

Návrat ke starému kódu po vzniku rezervací s kladnou lhůtou by znovu dovolil
jejich pozdní storno. Při opravě proto zachováme uložené lhůty a použijeme
kód, který je respektuje. Pouhá obnova staré zálohy by navíc ztratila
novější rezervace a změny; není automatickým řešením.

Největší rizika jsou chybné přiřazení lhůty starým datům, odlišná pravidla
webu a API nebo přepsání lhůty rezervace při schválení či změně nastavení.
Navazují na R-04
(nesoulad dokumentace a kódu), R-01 (databáze a souběh) a R-03
(opakovatelné spuštění) v [registru rizik](../history/evidence-and-evolution.md).
Automatizované kontroly a zbývající omezení jsou doložené v záznamu C09;
nezávislé review a čistá reprodukce jiným členem ještě následují. Posouzení znovu otevřeme při změně lhůty,
databáze nebo při rozdílném chování webu a API.

## 8. Co máme hotové

- Popsaný výchozí stav a dva provedené testy: hotovo, oba prošly.
- Návrh změny a souhlas s pravidly: hotovo.
- Analýza dopadů a dvě původní varianty: připravené; upravená varianta A
  zvolena. Schválení návrhu a připomínka spolužáka jsou zaznamenané podle
  sdělení uživatele 17. 11. 2026; nastavitelná a při vytvoření uložená lhůta
  je přijatá pro implementaci.
- Plán implementace a ověření pro navazující cvičení: připravený.
- Implementace nových pravidel a automatizované testy: připravené,
  výsledky a zbývající kroky jsou v [záznamu C09](../verification/c09-release-record.md).

[Přehled požadavků](README.md) · [Ověřování](../verification/README.md)
