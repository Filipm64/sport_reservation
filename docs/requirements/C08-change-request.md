# C08 — Change Request: storno politika rezervací

**ID:** CR-C08-01 · **Cvičení:** C08 — Controlled Change

**Stav:** ACCEPT pro business pravidla (souhlas zadavatele v tomto chatu
8. 11. 2026); technická varianta A je doporučená k review.
Implementace: **PLANNED**, nové chování: **NOT VERIFIED**.
Peer review spolužákem: **NOT DONE**. C08 zatím není celé dokončené.

## 1. Zdroj, potřeba a výchozí stav

Zdroj: návrh omezení pozdního storna, který zadavatel projektu přijal
8. 11. 2026. Business potřeba: provozovatel potřebuje čas znovu nabídnout
uvolněný termín; dnešní zrušení těsně před začátkem tuto možnost omezuje.
Jde o projektový požadavek, nikoliv povinnou funkci předepsanou C08.

Aplikační baseline: `cd3c4ddc8dbc47d83483441c51b8d8a7ce87281c`.
Platný kontrakt této verze je [REQ-05 / OP-04](cancel-reservation.md),
[BR-05](business-rules.md#br-05), navazující BR-02, BR-06, BR-07, BR-08
a [REQ-10](my-reservations.md). Vlastník smí před začátkem zrušit
PENDING_APPROVAL i CONFIRMED; záznam se nemaže.

Architektura: [ADR-01](../architecture/decisions/ADR-001-reservation-coordination.md),
společná `ReservationService`, transakční `DjangoDataStore`.
Runtime, konfigurace, schéma `0003_remove_draft_lifecycle`, přesná data,
dva krokované případy a jejich skutečné provedení jsou v
[baseline C08](../verification/c08-cancellation-baseline.md).
**TC-C08-01 i TC-C08-02: PASS**, včetně nezávislého čtení committed dat.
[Úplný log](../verification/evidence/c08-cancellation-baseline.log).
Tato evidence platí pro původní kontrakt, nikoliv pro navržené chování.

## 2. Odsouhlasená změna a rozsah

1. U nově vytvořených rezervací lze CONFIRMED zrušit nejpozději
   **2 hodiny před začátkem**. Přesně na hranici je zrušení povolené.
2. PENDING_APPROVAL může vlastník nadále stáhnout kdykoliv před začátkem.
   Expirace při začátku podle BR-07 se nemění.
3. Rezervace vytvořené před zavedením nové politiky zachovají původní
   podmínky, i když budou schválené až po zavedení změny.

Čas rozhoduje server při vyhodnocení operace. Dvě hodiny znamenají
120 minut skutečného času; výpočet se provádí nad UTC okamžiky,
zobrazení zůstává v Europe/Prague. Dřívější otevření stránky ani odeslání
požadavku nepředstavuje příslib úspěchu po dosažení hranice.

Mimo rozsah: storno poplatky a platby, oznámení e-mailem, administrátorská
výjimka, rozdílné limity sportovišť, nová role, změna DB technologie,
worker, změna dostupnosti a obnovení automaticky zamítnutých konkurentů.

**Důsledek k výslovnému posouzení při review:** Create ani Approve tímto
návrhem neomezujeme. Nová rezervace potvrzená méně než 2 hodiny před
začátkem už nepůjde zrušit vlastníkem; čekající žádost v témže čase ještě
stáhnout lze. UI musí podmínku sdělit před vytvořením žádosti/rezervace
a po schválení zobrazit aktuální možnost storna. Návrh nezavádí ochrannou
lhůtu po vytvoření ani schválení.

## 3. Podmínky přijetí — plán pro C09

Společně platí ověření identity, vlastníka a povoleného stavu. „Nová“
znamená vytvořená podle nové politiky, nikoliv nově schválená.

| ID | Vstup / situace | Požadované pozorovatelné chování |
| --- | --- | --- |
| AC-01 | Nová CONFIRMED, `now < starts_at - 2 h` | Vlastník zruší; HTTP 200, tentýž záznam CANCELLED |
| AC-02 | Nová CONFIRMED, `now == starts_at - 2 h` | Stejný úspěch jako AC-01 |
| AC-03 | Nová CONFIRMED, `starts_at - 2 h < now < starts_at` | HTTP 409, srozumitelný důvod storno lhůty; uložený záznam zůstane CONFIRMED |
| AC-04 | Nová nebo původní CONFIRMED, `now >= starts_at` | HTTP 409, bez změny potvrzeného stavu |
| AC-05 | Původní CONFIRMED, `now < starts_at`, i sekundu před začátkem | Původní právo vlastníka zrušit zůstane zachované |
| AC-06 | Nová nebo původní PENDING_APPROVAL, `now < starts_at` | Vlastník stáhne žádost bez dvouhodinového omezení; CANCELLED |
| AC-07 | PENDING_APPROVAL, `now >= starts_at` | Stávající BR-07: HTTP 409, uložené EXPIRED |
| AC-08 | Původní čekající žádost schválená po zavedení změny | Ponechá si původní storno politiku; AC-05 |
| AC-09 | Cizí/nepřihlášený uživatel nebo konečný stav | Zachovat existující oprávnění a kontrakt odmítnutí; opakované storno stav nemění |
| AC-10 | Úspěšné/odmítnuté storno přes API nebo web | Stejné rozhodnutí služby; web ukazuje možnost a deadline podle politiky a při POST znovu kontroluje čas |
| AC-11 | Zobrazení podmínek před vytvořením; následný přehled | Uživatel zná omezení potvrzené rezervace; staré rezervace mají rozlišitelné původní podmínky |
| AC-12 | Migrace a Create po nasazení | Všechny původní řádky zachovají původní politiku; nové dostanou novou; politika se neposílá jako volitelný klientský vstup |

Zrušení uvolní termín podle BR-02. Odmítnuté storno ho neuvolní.
Zrušení vítěze neobnovuje REJECTED žádosti podle BR-08.

## 4. Impact Matrix

Metoda: od AC k autoritativnímu rozhodnutí, načtení a uložení rezervace;
potom obě vstupní cesty, čtecí model portálu, schéma, testy a release.
Byly prohlédnuty níže uvedené aktuální artefakty. CHANGE znamená nutnou
budoucí změnu, CHECK regresní ověření; neoznačuje hotovou implementaci.
Vlastník realizace a ověření: tým projektu; konkrétní rozdělení pro C09
určí tým před implementací.

| Oblast / přesný artefakt | Dopad a důvod | Akce pro C09 | Důkaz dokončení |
| --- | --- | --- | --- |
| [REQ-05](cancel-reservation.md), [BR-05](business-rules.md#br-05), [BR-06](business-rules.md#br-06), [REQ-10](my-reservations.md) | CHANGE: dvě politiky, nové hranice a u v2 odlišný výsledek Approve před Cancel | Popsat kontrakt a výjimku původních rezervací; nynější platný text zatím zachovat | Review proti AC-01 až AC-12 a souběhové regresi |
| [Životní cyklus](../design/reservation-lifecycle.md) | CHANGE: guard CONFIRMED → CANCELLED závisí na politice; stavy stejné | Upravit guard, rozlišit PENDING a CONFIRMED | Přechodové a hraniční testy |
| [ADR-01](../architecture/decisions/ADR-001-reservation-coordination.md), [services.py](../../sport_booking/reservations/services.py), `ReservationService.cancel` | CHECK: rozhodování zůstane ve společné službě | Zachovat protected load → owner → expiry → cancellation → commit | Review volání, architektonické a integrační testy |
| [rules.py](../../sport_booking/reservations/rules.py), `TimeRules.validate_cancellation` | CHANGE: dnes ověřuje pouze začátek | Rozhodovat podle stavu, politiky a serverového času | Testy před/na/po hranici; UTC a změna letního času |
| [domain.py](../../sport_booking/reservations/domain.py), `Reservation`, `ReservationListing` | CHANGE: služba i UI musí znát politiku | Přenášet politiku a odvodit deadline/možnost storna | Komponentové testy a shoda čtení se zápisem |
| [models.py](../../sport_booking/reservations/models.py), [migrace](../../sport_booking/reservations/migrations/0003_remove_draft_lifecycle.py) | CHANGE u varianty A: trvalé rozlišení původních a nových záznamů | Nová migrace, backfill, bezpečný default a povolené hodnoty | Migrace existujících dat + nové Create |
| [persistence.py](../../sport_booking/reservations/persistence.py), `load_protected`, `save`, `list_reservations` | CHANGE: uložit a načítat politiku bez jejího přepisování při Approve/Cancel | Rozšířit mapování domény, modelu a seznamů | Round-trip a AC-08/12, committed SQL čtení |
| [api.py](../../sport_booking/reservations/api.py), `ReservationApi.cancel` | CHECK: 409 už podporuje; nový důvod odmítnutí | Zachovat endpoint, ověřit response a neovlivnitelnost politiky klientem | API pozitivní/negativní a autorizační testy |
| [web_views.py](../../sport_booking/reservations/web_views.py), `reservation_action`, `_error_message`; [home.html](../../sport_booking/reservations/templates/reservations/home.html) | CHANGE: dnešní tlačítko kontroluje jen začátek | České vysvětlení lhůty, podmínky před Create a správný deadline/tlačítko | Webové integrační testy včetně zastaralé stránky |
| [portal.py](../../sport_booking/reservations/portal.py) | CHECK: ověřit předání dat do přehledu | Podle čtecího modelu doplnit politiku nebo odvozené údaje | Test osobního přehledu a GET bez zápisu |
| [admin.py](../../sport_booking/reservations/admin.py) | CHECK: rezervace se nesmějí upravovat mimo službu | Nové pole nesmí zpřístupnit editaci politiky; Create/Delete jsou zakázané | Kontrola readonly polí a oprávnění adminu |
| Expirační command, dostupnost, BR-02/06/07/08 | CHECK: bez změny kontraktu; sdílejí stav rezervace | Zachovat expiraci, exkluzivitu, souběh a zamítnutí konkurentů | Relevantní regrese včetně souběhu |
| Import / samostatný worker pro storno | NO IMPACT: v projektu tyto vstupy neexistují | Nevytvářet nové komponenty | Review skutečných writer cest; expirační command řešen výše |
| Přímý SQL / ORM mimo službu | CHECK: DB neumí sama garantovat časové storno pravidlo | Neprezentovat API kontrolu jako ochranu libovolného SQL; chránit aplikační writer cesty | Popsat omezení a ověřit admin a migraci |
| [settings.py](../../sport_booking/sport_booking/settings.py), [README](../../README.md), nasazení | CHANGE postup nasazení; CHECK časová a DB konfigurace | Bez nového scheduleru; migrace při zastavených writerech | Reprodukce upgradu a spuštění |
| [traceability.json](../verification/traceability.json), [testy](../../sport_booking/reservations/tests.py), [baseline testy](../../sport_booking/reservations/test_c08_baseline.py) | CHANGE: část starých očekávání platí jen pro původní politiku | Zachovat historickou evidenci, doplnit nové scénáře a aktualizovat vazby | Test report, SQL evidence, `update_docs.py --check` |

## 5. Options Matrix

Obě varianty zachovávají 2 h pro nové CONFIRMED, původní podmínky starých
rezervací a výjimku pro PENDING. Délka lhůty je společná business podmínka;
varianty porovnávají způsob bezpečného rozlišení politik.

| Varianta | Splnění AC | Přínos | Náklady, selhání a obnova | Jak ověřit |
| --- | --- | --- | --- | --- |
| **A — uložená verze politiky u každé rezervace** | Ano při správném backfillu a přenosu všemi cestami | Politika zůstává stabilní přes schválení, restart i další release; původ podmínek je čitelný z řádku | Nové pole, migrace a mapování domény/portálu; špatný default může změnit původní práva; rollback musí metadata zachovat | Migrace starých řádků, nové Create, round-trip, schválení staré žádosti, hranice a rollback postup |
| **B — rozlišení přes `created_at` a pevný UTC okamžik zavedení v konfiguraci** | Ano při jednoznačném okamžiku přepnutí a zachovaných časech vytvoření | Využije existující timestamp bez nového pole v DB | Politika závisí na trvalé konfiguraci každého prostředí; chybný cutoff při obnově nebo změně konfigurace zpětně přepíše interpretaci dat; nutné zastavit všechny writery při přepnutí | Před/na/po cutoff, obnovení konfigurace a DB, restart, stará žádost schválená později |

**Doporučení: A.** Jedno pole a migrace jsou pro současnou Django aplikaci
přiměřené; stabilita podmínek již vytvořené rezervace je zásadní.
Varianta B je proveditelná, ale dlouhodobě váže práva uživatele na správně
obnovený globální čas přepnutí. Samostatná služba tuto potřebu neřeší lépe.

Nečinnost zachová ověřenou baseline, ale neřeší rušení na poslední chvíli.
Ruční upozornění na včasné storno může být dočasná kompenzace, nikoliv
splnění přijatého zákazu; není doporučené jako konečné řešení.

## 6. Rozhodnutí a review

- **Zadavatel a vlastník požadavku:** uživatel projektu v tomto chatu.
- **Datum business rozhodnutí:** 8. 11. 2026.
- **Rozhodnutí:** ACCEPT podmínek v oddílu 2 a jejich rozpracování do C09.
- **Technické doporučení:** A; čeká na kritické posouzení spolužákem.
- **Vlastník realizace/releasu:** tým projektu; tento dokument není release approval.
- **Peer reviewer:** dosud neurčen, review **NOT DONE**; AI příprava dokumentu
  není review spolužákem požadované zadáním.

Reviewer má především posoudit: zákaz storna krátce po potvrzení při
blízkém termínu; zachování staré politiky u později schválené žádosti;
hranici přesně 2 h; důvěryhodnost migrace a obnovy. Sem doplní jméno,
datum, konkrétní námitku, reakci týmu a konečný výběr varianty.
Před C09 uzavřít tyto body; nevykazovat peer-reviewed rozhodnutí předem.

## 7. Předávka do C09 — nejmenší delta varianty A

1. Po review aktualizovat REQ-05, BR-05, REQ-10 a guard ve stavovém návrhu.
   Aktuální dokumenty popisují dosud běžící aplikaci a nyní se nepřepisují.
2. Přidat neměnnou verzi storno politiky k rezervaci: původní `v1`, nová
   `v2`. Backfill všech existujících stavů na v1, nové Create na v2;
   schválení nemění verzi. Neodvozovat ji ze současného statusu.
3. Přenést verzi přes doménu, persistenci a čtecí přehled. Ve společných
   pravidlech určit deadline pro CONFIRMED v2 jako `starts_at - 2 h`;
   ostatní oprávněná storna zůstanou před začátkem. Zachovat vlastnictví,
   konečné stavy, expiraci a atomickou změnu stavu.
4. Upravit webové vysvětlení a tlačítko podle stejné politiky; POST musí
   znovu rozhodnout na serveru. API vrátí srozumitelný důvod s HTTP 409.
5. Doplnit níže uvedené testy a vazby; spustit integrační a regresní sadu
   s oddělenou souborovou SQLite DB, `manage.py check`,
   `makemigrations --check --dry-run`, `python3 scripts/update_docs.py --check`.
6. Zaznamenat výsledný commit, novou migraci, skutečný test report a
   clean-checkout ověření; teprve potom rozhodnout o releasu.

### Nové test oracle — zatím NOT RUN

Pro novou potvrzenou rezervaci se začátkem `2026-11-10T10:00:00Z`:

| Případ | Rozhodný čas / vstup | Očekávání |
| --- | --- | --- |
| N-01 | `07:59:59Z` | HTTP 200, committed CANCELLED |
| N-02 | `08:00:00Z` | HTTP 200, committed CANCELLED |
| N-03 | `08:00:01Z` | HTTP 409, committed CONFIRMED |
| N-04 | `10:00:00Z` | HTTP 409, committed CONFIRMED |
| N-05 | Původní CONFIRMED v `09:59:59Z` | HTTP 200, committed CANCELLED |
| N-06 | PENDING obou politik v `09:59:59Z`, resp. `10:00:00Z` | CANCELLED, resp. odmítnutí + committed EXPIRED |
| N-07 | Migrace DB s existujícími rezervacemi všech stavů; pak nové Create | Staré v1 beze změny ID, stavu a intervalu; nové v2 |
| N-08 | Schválení původní čekající žádosti, potom storno sekundu před začátkem | Zůstává v1, storno uspěje |
| N-09 | Web otevřen před hranicí, POST dorazí po ní | Služba odmítne; UI vysvětlí lhůtu; DB beze změny |
| N-10 | Přechod zimního/letního času | Dvě hodiny skutečného času v UTC, správně zobrazený místní deadline |

Regrese: vlastnictví, nepřihlášený přístup, opakované storno, konečné stavy,
uvolnění termínu po úspěchu a blokování po odmítnutí, neobnovení REJECTED,
expirace i souběh Approve/Cancel. U nové v2 žádosti schvalované méně než
2 h před začátkem odpovídá souběh sériovému pořadí: Cancel první → CANCELLED
a Approve odmítnuto; Approve první → CONFIRMED a Cancel odmítnuto.
Původní v1 zachová dosavadní souběhový kontrakt BR-06. Toto rozlišení
musí být při implementaci výslovně doplněno také do specifikace BR-06.
Baseline TC-C08-01/02 zůstanou regresí **v1**; v novém schématu budou
potřebovat vědomou přípravu původní politiky, ne přepsání starého logu.

### Nasazení, obnova a rizika

Pro jednoznačné přepnutí zastavit server a ostatní writery, zálohovat DB,
aplikovat migraci s backfillem v1, nasadit Create s v2 a ověřit data před
obnovením provozu. Neprovozovat smíšené staré a nové writery. Migrace nesmí
jedním novým defaultem označit existující řádky jako v2.

Rollback starého kódu by v2 rezervacím znovu dovolil pozdní storno a smazání
pole by ztratilo informaci o politice. Po vzniku v2 proto nelze slíbit
bezpečný prostý downgrade: zachovat metadata, zastavit zápisy a použít
opravenou verzi respektující obě politiky. Obnova celé předchozí zálohy
by ztratila novější operace; není automatická náhrada tohoto postupu.

Nová rizika: chybný backfill, rozpor UI/API, přepsání politiky při schválení
a změna výsledku souběhu u v2. Vazba na dosavadní R-04 (nesoulad artefaktů),
R-01 (DB/souběh), R-03 (reprodukce prostředí) v
[registru rizik](../history/evidence-and-evolution.md).
Účinnost navržených opatření a skutečné reziduální riziko nové politiky:
**NOT VERIFIED**. Přehodnotit po migraci, integračních testech a review;
další trigger je změna lhůty, databáze nebo nález odlišného UI/API chování.

## 8. Kontrola dokončení C08

- Baseline a přijaté původní chování: hotovo, odkazy výše.
- Dva krokované případy a skutečné integrační provedení: hotovo, 2 PASS.
- Věrohodný CR, AC, Impact Matrix a dvě proveditelné varianty: připraveno.
- Souhlas zadavatele s business změnou: zaznamenán.
- Review spolužákem, konečný výběr varianty a rozdělení odpovědností: zbývá.
- Rozsah a nové/regresní oracle pro C09: připraveno k review.

[Přehled požadavků](README.md) · [Ověřování](../verification/README.md)
