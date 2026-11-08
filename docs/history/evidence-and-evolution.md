# Evidence and evolution

## C08 — baseline před navrženou změnou storno politiky

Dne 8. 11. 2026 byla zachycena aplikační baseline
`cd3c4ddc8dbc47d83483441c51b8d8a7ce87281c` a specifikovány dva případy
současného BR-05 před jejich spuštěním. Oba byly následně provedené přes
API se skutečnou SQLite persistencí a nezávislým čtením committed stavu:
sekundu před začátkem zrušení uspělo, přesně při začátku bylo odmítnuté.
**2 testy prošly**. [Baseline, postup, výsledky a meze důkazu](../verification/c08-cancellation-baseline.md).

Následně zadavatel 8. 11. 2026 přijal dvouhodinovou storno lhůtu pro nové
potvrzené rezervace včetně přesné hranice, zachování rušení čekajících
žádostí před začátkem a původních podmínek existujících rezervací.
[C08 — Change Request](../requirements/C08-change-request.md) obsahuje AC,
dopady, dvě technické varianty a předávku do C09. Doporučená varianta A
ukládá verzi politiky k rezervaci; review spolužákem a konečný výběr varianty
zatím nejsou provedené. Aplikační pravidla zůstávají beze změny.

## C01 Engineering Spike

### Question
Dokáže Django ORM uložit a znovu načíst rezervaci včetně uživatele,
sportoviště, intervalu, stavu a času vytvoření?

### Co jsme udělali
- Přidali jsme modely `Sport`, `Resource` a `Reservation`; uživatel je
  standardní Django model.
- Rezervace uchovává vlastníka, Resource, interval, stav a čas vytvoření.
- Přidali jsme databázové kontroly kladné délky intervalu a povoleného stavu.
- Testy pokrývají načtení polí a vazeb, uložení změny stavu, odmítnutí
  nulového/záporného intervalu a neznámého stavu, ochranu navázaných záznamů
  před smazáním a povinného uživatele a Resource.

### Pozorovaný výsledek
Ověřeno 14. 9. 2026 na Django 6.1.1 a SQLite: všech šest testů prošlo
a Django system check nehlásil problém.

### Rozhodnutí
Používáme Django ORM, verzované migrace a testy nad databází. Uživatel se
neduplikuje vlastním modelem.

## Evidence C02: specifikace → běžící aplikace

**Revize:** 5. 10. 2026; technická kontrola podle přiloženého zadání C02.

**Přijatá baseline:** Aktuální technický návrh je
[baseline v0.2](baseline-v0.2.md), předchozí je
[baseline v0.1](baseline-v0.1.md). [Zápis týmu](baseline-approval.md)
uvádí přijetí v0.1 dne 4. 10. a v0.2 dne 5. 10. 2026 a jména členů týmu.
Schválené verze dokumentů jsou v zápisu propojené s revizemi `2c3c00c`
a `bfd2ff2`.

**Předvedené základní operace:** Create, Check Availability, Confirm,
Cancel a nová Approve prostřednictvím Django JSON API. Základní scénáře
používají Resource bez schvalování; nové scénáře Resource se schvalováním.

**Skutečně provedené příklady ověření:** Původních 16 testů při zahájení
revize prošlo. Po opravách bylo spuštěno následující ověření:

```sh
SPORT_BOOKING_TEST_DB=/tmp/sport-booking-c02-audit.sqlite3 .venv/bin/python sport_booking/manage.py test reservations --noinput
.venv/bin/python sport_booking/manage.py check
.venv/bin/python sport_booking/manage.py makemigrations --check --dry-run
```

Výsledek: **30 testů prošlo, žádný nebyl přeskočen**, Django 6.1.1,
Python 3.14.6, SQLite; system check bez problému, žádné chybějící migrace.
Testovací souborová DB je oddělená od aplikační DB. Bez proměnné
`SPORT_BOOKING_TEST_DB` používá Django sdílenou paměťovou DB a pět testů
souběhu výslovně přeskočí; takový běh nedokládá souběžné záruky.

| Operace / pravidlo | Skutečně spuštěný úspěšný příklad | Negativní / hraniční příklad |
| --- | --- | --- |
| Create | 201 a uložená DRAFT, znovu načtená z DB | nulový interval, neexistující Resource, neplatné kalendářní datum, bez přihlášení; přesná a překročená hranice 30 dní/2 hodin |
| Availability | sousední interval AVAILABLE; DRAFT/PENDING neblokují | potvrzený překryv a nedostupný Resource UNAVAILABLE; neplatný interval chyba |
| Confirm | běžný Resource → CONFIRMED; schvalovaný → PENDING_APPROVAL | kolize nebo nedostupný Resource → 409, zůstane DRAFT; cizí vlastník → 404 |
| Cancel | DRAFT, CONFIRMED a PENDING_APPROVAL → CANCELLED; potvrzený čas se uvolní a záznam zůstane | opakované zrušení a přesně na start → 409; při dosaženém deadline čekající žádosti → EXPIRED |
| Approve | zpoždění 23 hodin → CONFIRMED; zamítnutí → REJECTED | běžný uživatel → 403; nová kolize → 409 a PENDING; přesně 24 hodin / start → EXPIRED |
| Expirace | expirační příkaz skutečně spuštěn v testech | obě přesné hranice a odmítnutí rozhodnutí/zrušení po expiraci |
| Souběh | pět testů se dvěma nezávislými DB spojeními a synchronizovaným startem | Confirm/Confirm, Approve/Approve, Confirm/Approve: právě jedna alokace; Confirm/Cancel a Approve/Cancel: konečný stav CANCELLED |

Detailní vazby na názvy testů jsou v [revizi požadavků](../requirements/review.md).
API testy běží přes Django test client; souběžné testy volají stejné view
funkce ze dvou vláken s RequestFactory a samostatnými databázovými spojeními.
Není to zátěžový test ani test přes reálnou HTTP síť.

**Nalezený nesoulad a způsob vyřešení:**

- `select_for_update()` nechrání řádky v SQLite. Zápisové transakce nyní
  začínají IMMEDIATE, takže kontrola kolize a změna jsou serializované.
  Ověřeno třemi paralelními scénáři alokace; C03 musí zachovat záruku i při
  změně databáze.
- SVG nesprávně vedlo Confirmed Cancel do REJECTED a hrana Draft Cancel
  nekončila v CANCELLED. Opraveny cíle i směrové šipky.
- Text tvrdil, že Approve/Cancel vždy dovolí jen první změnu. Opraven text:
  schválení může následovat platné zrušení; ověřena obě sériová pořadí
  i souběh.
- Po 24 hodinách šlo čekající žádost zrušit před běžícím expiračním
  příkazem. Cancel nyní nejprve zkontroluje deadline a uloží EXPIRED.
  Popsáno, kdy se expirace fyzicky zapisuje; Availability zůstává čtecí.
- Neplatné kalendářní datum mohlo vyvolat výjimku místo 400. Opravena
  validace a ověřeno, že nevzniká záznam.
- Admin dovoloval měnit stav, interval a mazat rezervace mimo přijaté
  operace. Rezervační admin nyní slouží pouze k čtení; ověřeno testem.
- Doplněna autentizace Availability ve specifikaci, zdroj serverového času,
  dohledatelné REQ ID a konkrétní drivery pro C03.

**Shrnutí dopadu změny:** Schvalovaný Resource, PENDING_APPROVAL a
čas žádosti, rozhodnutí správce, REJECTED/EXPIRED, kontrola kolize při
schválení a rušení čekajících žádostí. Create, polouzavřené intervaly,
exkluzivita, limity a neblokující charakter dostupnosti zůstávají stejné.

**Zbývající předpoklad / neznámá:** Historické pořadí odsouhlasení v0.1,
analýzy dopadu a implementace v0.2 není tímto novým ověřením prokázané. Není zvolen scheduler ani jeho
maximální zpoždění; notifikace a SLA nejsou specifikovány. SQLite serializuje
zápisy celé DB; při vyčerpání timeoutu není určena uživatelská politika retry.

**Architektonické drivery přenesené do C03:**
[AD-01 až AD-05](../architecture/drivers.md): exkluzivita při souběhu,
konzistence přechodů, persistentní časový proces a scheduler, oprávnění
napříč vstupy, jednotné časové hranice. Každý má zdroj, scénář a měřitelné
kritérium; nezavádí se předčasně nová architektura.

**Commit / tag aplikace:** Výchozí revidovaný commit je
`bfd2ff2ddbc08bdd774b8a1ebf2017a72bace461` (`CV2`). Výše popsané opravy
jsou pracovní změny nad tímto commitem; pro reprodukci je zatím potřeba
celý pracovní strom. Commit ani tag oprav nebyl vytvořen. Při odevzdání tým
uloží opravy do Gitu a doplní skutečný výsledný commit/tag; výchozí hash
nesmí být vydáván za identifikátor opravené aplikace.

## Evidence C03: návrh → realizace a ověření

**Datum:** 12. 10. 2026. Výchozí stav: `acd7890` (`cv3 A - E3`).
Přijata varianta A z ADR-01, návrh G1–G4/H1–H2 a cross-view kontrola.
Historický popis pracovního stavu C02 výše patří k tehdejší revizi;
opravovaný kód C02 byl následně uložen v historii projektu.

**Realizované změny:**

- Vstupní rozhraní: `api.py` a tenké `views.py`, bez přímého ORM.
- Správa rezervací a čtecí dostupnost: `services.py`; Confirm a Approve
  sdílejí `_decide_confirmation()`. Expirace volá stejnou službu.
- Identita a oprávnění: `identity.py`; časová pravidla: `rules.py`.
- Doménové hodnoty a přechody: `domain.py`, bez závislosti na Django ORM/HTTP.
- Ukládání: port `DataStore` a adaptér `DjangoDataStore` v `persistence.py`.
  Každá operace má vlastní kontext; IMMEDIATE chrání rozhodující čtení
  a zápis. Při neúspěchu se změny vracejí zpět.
- `wiring.py` sestavuje části; databázové schéma, migrace, cesty API
  a omezení rezervačního adminu zůstaly zachované.

**Nálezy kontroly kódu:** odstraněno opakované rozhodování ve views,
import pravidel z views do commandu a přímé změny stavu z těchto vstupů.
Dále opravena validace `resource_id`: boolean, desetinné číslo a hodnota
mimo rozsah identifikátoru jsou odmítnuté jako neplatný vstup.
Chyba ukládání se nevrací jako úspěšné potvrzení.

**Skutečně provedené ověření:**

```sh
PYTHONDONTWRITEBYTECODE=1 SPORT_BOOKING_TEST_DB=/tmp/sport-booking-c03-implementation.sqlite3 .venv/bin/python sport_booking/manage.py test reservations --noinput
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python sport_booking/manage.py check
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python sport_booking/manage.py makemigrations --check --dry-run
```

**Výsledek: 36 testů prošlo, žádný nebyl přeskočen.** Django system check
bez problému; žádné změny migrací. Ověřeno celé dosavadní API chování,
pět souběhů mezi nezávislými spojeními a navíc:

- expirační management command v samostatném Python procesu závodící se
  schválením nad stejným SQLite souborem; konečný stav EXPIRED;
- rollback při simulované chybě po zápisu i před dokončením transakce;
- opakovaná expirace je bezpečná, konečné stavy nemění;
- neplatné identifikátory nevytvářejí rezervaci;
- AST kontrola povolených závislostí: žádné ORM/HTTP ve společném business
  rozhodování, žádná závislost služby na konkrétním Django adaptéru,
  expirační vstup neimportuje views/modely.

Testy simulovaných chyb ověřují rollback při zachovaném databázovém spojení;
nejde o test fyzického výpadku disku nebo ztráty spojení během commit.

**Omezení:** automatický plánovač expirace zůstává nenakonfigurovaný;
SQLite serializuje zápisy celé databáze. Týmové schválení specifikace
zůstává samostatným týmovým úkolem. Změna databáze vyžaduje nové ověření
souběžných záruk; záruky zde byly ověřené pro SQLite.

**Commit implementace:** záznam, diagramy a kód jsou součástí commitu
`Implement C03 reservation architecture and document decisions`.
Jeho hash lze získat pomocí:

```sh
git log -1 --format=%H --grep='^Implement C03 reservation architecture and document decisions$'
```

## L1 — Opakované ověření chování

Dne 12. 10. 2026 byly na commitu `762af3d` znovu spuštěny relevantní
příklady C02 pro změněné části: 19 API testů, 6 souběžných scénářů a
4 testy selhání/validace. **Všech 29 testů prošlo bez přeskočení.**
Tabulka výsledků, konkrétní testy a reprodukovatelný příkaz jsou v
[ověření chování L1](../verification/behavior.md). Aplikační kód se neměnil.

## L2 — Opakovatelná kontrola architektonického pravidla

Dne 12. 10. 2026 byla doplněna a spuštěna samostatná AST kontrola,
že HTTP vstupy a expirační command nepoužívají ORM ani nepřepisují stav
rezervace. **1 test prošel**; také odmítl sedm ukázkových porušení.
Pravidlo, reprodukovatelný příkaz a skutečný log jsou v
[ověření L2](../verification/architecture-rules.md). Aplikační chování se neměnilo.

## C03 — Architecture Evidence

**Baseline:** [v0.2](baseline-v0.2.md). Aktuální
[zápis schválení](baseline-approval.md) uvádí přijetí v0.1 dne 4. 10. 2026
a v0.2 dne 5. 10. 2026. Starší poznámky o nedoloženém schválení výše
zachycují stav při dřívější revizi.

**Part A:** Prohlídka výchozího kódu na commitu `acd7890`:
views kombinovaly HTTP, pravidla a ORM; Confirm/Approve opakovaly rozhodování;
expirační command měnil stav přímo a importoval pravidlo z views.
Nálezy jsou zachycené v [AS-IS → TO-BE delta](as-is-to-be-delta.md);
samostatný dokument Part A není v repozitáři.

**Drivers:** [AD-01 až AD-05](../architecture/drivers.md): exkluzivita při
souběhu, konzistentní přechody, trvalé čekající schvalování, oprávnění
na všech vstupech a jednotné časové hranice.

**Decision question:** Má potvrzování a schvalování rezervací řídit
společná část rezervační aplikace, nebo samostatná služba?

**Alternatives:** A — společné rozhodování uvnitř aplikace;
B — samostatná služba vlastnící rozhodování a stav.
[Struktury a porovnání](../architecture/decisions/ADR-001-reservation-coordination.md).

**Scenario walkthrough:** Dvě čekající žádosti o stejné sportoviště
a interval jsou schválené současně. První uspěje, druhá dostane konflikt
a zůstane PENDING_APPROVAL.
[Průchod oběma variantami](../architecture/decisions/ADR-001-reservation-coordination.md#průchod-scénářem--dvě-současná-schválení).

**ADR:** [ADR-01](../architecture/decisions/ADR-001-reservation-coordination.md#adr-01--má-potvrzování-a-schvalování-rezervací-řídit-společná-část-aplikace-nebo-samostatná-služba)
volí A. Samostatná služba není požadovaná a sama neřeší souběh;
přidávala by další komunikaci, ověřování identity a možnosti selhání.

**Views:**

- Domain class: [doménový model](../design/domain-model.md).
- Context: [G1](../architecture/system-context.md).
- Static architecture: [G2](../architecture/static-structure.md).
- State ownership: [G3](../design/reservation-lifecycle.md).
- Runtime/deployment: [G4](../architecture/runtime-deployment.md).
- Design sequence: [H1](../design/approval-sequence.md).
- Focused design class: [H2](../design/design-classes.md).

**Cross-view issues found/resolved:** Odděleno načtení rezervace a kolizí;
H1 výslovně ukazuje změnu doménového objektu před uložením. H2 doplňuje
společné rozhodování Confirm/Approve; G2/G4 upřesňují oddělený kontext
každého požadavku a ochranu mezi procesy. [Kontrola sedmi vazeb](../verification/cross-view-check.md).

**AS-IS → TO-BE delta:** [Tabulka J](as-is-to-be-delta.md).
Osm CHANGE provedeno, tři KEEP zachovány, obě VERIFY ověřeny testy.

**Implementation changes:** `ReservationService` vlastní přechody a
kontrolu alokace; `TimeRules` čas, `IdentityAccess` oprávnění,
`DataStore`/`DjangoDataStore` ukládání. HTTP i expirační command delegují
na společné části. Doménové entity a hodnoty jsou oddělené od ORM.
Schéma, migrace a cesty API se zachovaly; podrobná mapa souborů je v H2.

**Behaviour verification:** [L1](../verification/behavior.md): 29 relevantních
testů znovu prošlo na commitu `762af3d`. Závěrečný běh po doplnění L2:
**37 testů prošlo, žádný přeskočený**; Django check bez problému,
žádné změny migrací. [Skutečný log](../verification/evidence/c03-final-verification.log).

```sh
PYTHONDONTWRITEBYTECODE=1 SPORT_BOOKING_TEST_DB=/tmp/sport-booking-c03-final.sqlite3 .venv/bin/python sport_booking/manage.py test reservations --noinput
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python sport_booking/manage.py check
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python sport_booking/manage.py makemigrations --check --dry-run
```

**Architecture conformance rule + result:** Vstupy nesmějí přímo používat
ORM ani měnit lifecycle stav. [AST kontrola L2](../verification/architecture-rules.md)
prošla nad třemi vstupními soubory a odmítla sedm ukázkových porušení;
je součástí závěrečné sady 37 testů.

**Remaining uncertainty / risk:** Automatický plánovač expirace není
nastavený; expirační command se zatím spouští ručně. SQLite serializuje
zápisy celé databáze. Zatížení, SLA a politika retry při timeoutu nejsou
stanovené. Změna databáze vyžaduje nové ověření souběhu. Statická kontrola
L2 se vztahuje na uvedené vstupní soubory a přímé přístupy.

**Commit/tag:** Implementace a diagramy: `762af3d`.
Závěrečná evidence, L1/L2 a nový kontrolní test jsou připravené k ručnímu
commitu týmem. Výsledný hash doplnit po jeho vytvoření.

## C05 DD Verification Evidence

Tests derived from DD:

| Element DD | Test | Ověřený výsledek |
| --- | --- | --- |
| `TimeRules.is_expired` a deadline `min(requested_at + 24h, start)` | `test_expiry_exact_deadline_on_approve_cancel_and_command` | Na obou přesných hranicích vznikne `EXPIRED`; jedna minuta před hranicí zůstává žádost platná. |
| Stavový guard před rozhodnutím | `test_approve_draft_reservation_returns_conflict`; `test_expired_approval_cannot_be_approved` | Nepending žádost se nemění; expirovaná se uloží jako `EXPIRED` a vrátí 409. |
| Kontrola alokace při schválení | `test_new_conflict_prevents_approval_and_leaves_request_pending` | Nová kolize vrátí 409 a žádost zůstává `PENDING_APPROVAL`. |
| Validace před přechodem do `PENDING_APPROVAL` | `test_confirm_rejects_invalid_interval_for_approval_resource`; `test_confirm_rejects_conflict_for_approval_resource` | Neplatný interval i kolize vrátí 409 a záznam zůstane `DRAFT`. |
| Oprávnění správce | `test_staff_can_reject_but_non_staff_cannot_decide` | Běžný uživatel dostane 403; správce může zamítnout. |
| Neplatné rozhodnutí na vrstvě služby | `test_service_rejects_invalid_approval_decision` | Služba vyhodí `invalid_input`; stav zůstává `PENDING_APPROVAL`. |
| Atomicita při chybě zápisu | `test_failed_save_rolls_back_and_never_reports_success` | Neúspěšný zápis nehlásí úspěch a změna se vrátí zpět. |

Úroveň testu: deadline a stavové hranice procházejí přes API/komponentu,
protože výsledek zahrnuje uložený stav i HTTP odpověď. Rollback test je
integrační, protože ověřuje hranici služby a persistence adaptéru.

Unit/component tests executed:
- `test_new_conflict_prevents_approval_and_leaves_request_pending` – komponentní test pro konflikt při schválení.
- `test_confirm_rejects_invalid_interval_for_approval_resource` a `test_confirm_rejects_conflict_for_approval_resource` – regresní testy nálezu F1.
- `test_expired_approval_cannot_be_approved` – komponentní test pro expirovanou žádost.
- `test_staff_can_reject_but_non_staff_cannot_decide` – komponentní test pro oprávnění.
- `test_failed_save_rolls_back_and_never_reports_success` – integrace/rollback test.
- Sada Django testů `reservations` měla při hodnocené baseline 37 testů. Po opravách C06 má aktuálně 53 testů; aktuální běh je zaznamenán níže.

Design ↔ implementation mismatch:
- Nalezen rozpor v kontraktu chyby approve: text tvrdil, že `EXPIRED` se neukládá, ale pseudokód, implementace i testy stav ukládají. Opraven popis kontraktu.
- Doménové přechody ve `Reservation` odpovídají správnímu životnímu cyklu v kódu.
- `TimeRules.is_expired` odpovídá pravidlu deadlinu a chování v službě i v testech.
- `ReservationService.approve` ověřuje conflict a vybírá správný přechod stavu v jednom transakčním kroku.

Resolution:
- Implementace zůstala beze změny; popis kontraktu nyní říká, že při dosaženém deadlinu služba uloží `EXPIRED`, commitne a poté vrátí chybu.
- Rozsah DD je omezen na jednu architektonickou odpovědnost s reálnou obchodní logikou, nikoliv na celý systém.

Remaining design risk:
- SQLite serializuje zápisy celé databáze; návrhový záměr je správný pro SQLite, ale není automaticky přenosný na vícenásobné instance nebo horizontální škálování.
- Expiraci stále musí řešit serverový čas a plánovaný nebo ruční spouštěč; tento provozní detail je mimo doménový kontrakt.

Commit/tag:
- Ověření proběhlo na aktuálním pracovním stromu; nejednalo se o vytvoření nové produkční verze ani release.
- Tento designový úkol je založen na existující implementaci v repozitáři a dokumentuje návrh/ověření na aktuálním kódu, nikoli na novém release artefaktu.

## C06 — Reakce na externí hodnocení

Hodnocení posuzovalo čistý archiv `4bb9ebc` z 21. 10. 2026. Následují tři
ověřené nálezy z formuláře. Jejich opravy jsou ve změně `431b7da` a ověřeny
proti aktuálnímu kódu; hodnocený stav zůstává `4bb9ebc`.

### F1 — Confirm u Resource se schvalováním

- **Claim:** OP-03 musí před přechodem do `PENDING_APPROVAL` odmítnout neplatný interval a existující kolizi; viz [baseline v0.2](baseline-v0.2.md) (OP-03) a REQ-03 v [revizi požadavků](../requirements/review.md).
- **Expected:** neplatný interval nebo kolize vrátí chybu a rezervace zůstane `DRAFT`.
- **Observed na baseline `4bb9ebc`:** implementace obě kontroly měla, ale chyběl test Confirm pro tyto dvě větve u Resource se schvalováním. Hodnotitel doložil přežití mutací a rozdíl jejich chování dočasným testem.
- **Verify:** nález reprodukovaný hodnotitelem v čistém archivu; aktuální pokrytí je v `sport_booking/reservations/tests.py`: `test_confirm_rejects_invalid_interval_for_approval_resource` a `test_confirm_rejects_conflict_for_approval_resource`.
- **Disposition:** VERIFIED FINDING — ACCEPT. Důvod: specifikované chování nebylo regresními testy dostatečně ověřeno.
- **Action / owner:** doplnit oba testy — tým.
- **Closure evidence:** změna `431b7da`; oba testy kontrolují odmítnutí a zachování `DRAFT`. Aktuální celá sada 53 testů prošla.

### F2 — chování při expiraci v C05 DD

- **Claim:** C05 popisoval chybu při expiraci tak, že terminální stav není uložen; evidence zároveň tvrdila, že nesoulad návrhu s implementací nebyl nalezen. Viz [návrhový kontrakt](../design/detailed-design.md) a tehdejší záznam C05 výše.
- **Expected:** dokumentace má popisovat stejné chování jako přijatá specifikace, pseudokód a aplikace.
- **Observed na baseline `4bb9ebc`:** služba při expiraci uložila `EXPIRED`, commitla změnu a vrátila chybu; text kontraktu tvrdil opak.
- **Verify:** hodnotitel provedl mutaci bez uložení expirace; testy selhaly. Aktuální implementace je v `sport_booking/reservations/services.py` (`_expire_if_due`) a kontrola deadline v `rules.py` (`is_expired`).
- **Disposition:** VERIFIED FINDING — ACCEPT. Šlo o rozpor v dokumentaci, ne o chybu implementace.
- **Action / owner:** opravit kontrakt — tým.
- **Closure evidence:** změna `431b7da`; kontrakt nyní říká, že `EXPIRED` se uloží a commitne před vrácením chyby. Výsledek pokrývají `test_expired_approval_cannot_be_approved` a `test_expiry_exact_deadline_on_approve_cancel_and_command`; aktuální sada 53 testů prošla.

### F3 — kdo kontroluje deadline v H1/H2

- **Claim:** H1/H2 přisuzovaly kontrolu deadline `validate_approval()`; viz [H1](../design/approval-sequence.md) a [H2](../design/design-classes.md).
- **Expected:** návrhové diagramy mají správně ukazovat oddělenou kontrolu deadlinu a validaci časového intervalu.
- **Observed na baseline `4bb9ebc`:** deadline kontrolovalo `is_expired()` a služba `_expire_if_due`; `validate_approval()` validovalo jen interval. Změna běhu aplikace nebyla potřeba.
- **Verify:** nález porovnán hodnotitelem s runtime trace a implementací v `sport_booking/reservations/rules.py` a `services.py`. Aktuální diagramy rozlišují `is_expired()` před `validate_approval()`.
- **Disposition:** VERIFIED FINDING — ACCEPT. H1/H2 byly v této části zastaralé.
- **Action / owner:** opravit oba pohledy — tým.
- **Closure evidence:** změna `431b7da`; popis v H1/H2 odpovídá kódu. Deadline a hraniční chování kryje `test_expiry_exact_deadline_on_approve_cancel_and_command`; aktuální sada 53 testů prošla.

### Další body hodnocení a otevřené riziko

| Položka | Rozhodnutí a důvod | Akce / vlastník | Důkaz nebo stav |
| --- | --- | --- | --- |
| B1 — baseline a dohledatelnost | VERIFIED EVIDENCE GAP — ACCEPT; původní záznam nepropojoval výsledky cvičení s revizemi a rozporoval schválení v0.2. | Doplnit revize a schválení — tým. | Odkazy doplněny: hodnocená baseline `4bb9ebc`; výstupy C02 `bfd2ff2`, C03 `762af3d`, C05 `3e05867`; schválení v [zápisu baseline](baseline-approval.md). Samostatný tag nebyl vytvořen; hodnocenou baseline identifikuje commit. |
| D3 — mapování návrhu na testy | ACCEPT. Dohledatelnost v C05 byla nedostatečná. | Doplnit vazbu prvek návrhu → test a zdůvodnění úrovně — tým. | Tabulka „Tests derived from DD“ a zdůvodnění úrovně testů v části C05 výše. |
| D4 — nepokryté větve approve | ACCEPT. V hodnocené baseline nebyly všechny relevantní větve ověřeny. | Doplnit testy — tým. | Např. `test_unavailable_resource_prevents_approval`, `test_missing_approval_request_is_expired_on_approve`, `test_invalid_approval_decision_is_rejected_without_state_change`, `test_service_rejects_invalid_approval_decision`; viz `sport_booking/reservations/tests.py`. |
| Provozní expirace a jiné databáze | Otevřené riziko, nikoli uzavřený nález C06. | Automatické periodické spouštění a případná změna databáze vyžadují samostatnou práci a ověření — tým. | Testy a následné ověření níže proběhly na SQLite; automatický plánovač není nastaven. Chování na jiné DB a zátěžové chování: **NOT VERIFIED**. |

**Aktuální ověření:** 1. 11. 2026, revize `726cc62` —
`PYTHONDONTWRITEBYTECODE=1 SPORT_BOOKING_TEST_DB=/tmp/sport-booking-c06-review.sqlite3 .venv/bin/python sport_booking/manage.py test reservations --noinput`.
Výsledek: **53 testů prošlo, žádný nebyl přeskočen**; Django system check bez
problému. Jde o ověření celé sady na samostatné souborové SQLite DB, nikoli o
zátěžový test nebo ověření jiné databáze.

## Registr rizik — C07/C08

Rizika vycházejí z aktuálního projektu a jeho ověřovací evidence. C06
zjištění F1–F3 a D3–D4 jsou uzavřena změnou `431b7da`; jejich testy a
opravené dokumenty jsou podkladem pro R-04. Poskytnuté podklady neobsahují
konkrétní plán dalších implementačních úkolů ani rozdělení kapacity členů,
proto jsou termíny navázané na události a vlastníkem je tým: Jakub Petrov,
Filip Matůš a Patrik Vachník. Možná změna DB v R-01 je podmíněný scénář,
nikoli potvrzený plán. Skóre je `L × I` podle matice v zadání.

### R-01

- **Popis rizika:** Ochrana souběhu rezervací je ověřena na SQLite a používá její režim `IMMEDIATE`. Pokud se projekt převede na jinou databázi a ochrana se tam bude chovat jinak, mohou se potvrdit dvě rezervace stejného termínu a porušit BR-02.
- **Kategorie:** Technical / Quality.
- **Počáteční riziko (L/I/priorita/důvod):** L=2, I=3 → **HIGH (6)**. Jiná DB není ověřená; dvojí potvrzení by porušilo hlavní pravidlo rezervace.
- **Strategie ošetření a zdůvodnění:** MITIGATE — ponechat SQLite pro demonstraci a před přijetím jiné DB ověřit ochranu souběhu.
- **Opatření, vlastník, termín:** Před přijetím jiné DB spustit úplnou sadu včetně souběhových testů a zkontrolovat transakční ochranu. Vlastník: tým. Termín: před změnou DB.
- **Důkaz účinnosti a stav ověření:** 53 testů prošlo na SQLite v revizi `726cc62`, včetně souběhových testů. Jiná DB: **NOT VERIFIED**.
- **Očekávané reziduální riziko:** L=1, I=3 → **MEDIUM (3)**, pokud cílová DB projde souběhovými testy; jinak skóre nesnižovat.
- **Skutečné reziduální riziko / NOT VERIFIED:** **NOT VERIFIED** pro jinou DB.
- **Přijetí reziduálního rizika, vlastník, zdůvodnění:** Tým přijímá riziko při použití ověřené SQLite; případnou migraci musí tým znovu posoudit.
- **Monitoring, trigger, contingency, další review:** Trigger: změna DB nebo selhání souběhového testu. Do ověření používat SQLite. Review před změnou DB.

### R-02

- **Popis rizika:** Příkaz `expire_reservations` existuje, ale pravidelný plánovač není nastavený. Pokud ho obsluha po deadlinu nespustí, žádost může zůstat jako `PENDING_APPROVAL`, dokud ji někdo neschválí, nezruší nebo nespustí příkaz.
- **Kategorie:** Release / Operation.
- **Počáteční riziko (L/I/priorita/důvod):** L=2, I=2 → **MEDIUM (4)**. Ruční krok je doložený, automatické spuštění ne; žádosti mohou mít zastaralý stav, i když approve/cancel expiraci kontroluje.
- **Strategie ošetření a zdůvodnění:** MITIGATE — pro demonstraci přidat kontrolu expirace do ručního postupu; plánovač zavést, jen pokud bude součástí nasazení.
- **Opatření, vlastník, termín:** Před demonstrací zkontrolovat čekající žádosti a v případě potřeby spustit `.venv/bin/python sport_booking/manage.py expire_reservations`. Vlastník: tým. Termín: před každou demonstrací.
- **Důkaz účinnosti a stav ověření:** Příkaz a logiku expirace pokrývají `test_expiry_management_command_updates_old_requests` a `test_expiry_exact_deadline_on_approve_cancel_and_command`. Pravidelný plánovač ani celý postup před demonstrací nejsou ověřené.
- **Očekávané reziduální riziko:** L=1, I=2 → **LOW (2)**, pokud se kontrola provede při každé demonstraci.
- **Skutečné reziduální riziko / NOT VERIFIED:** **NOT VERIFIED**, dokud se postup nevyzkouší při demonstraci.
- **Přijetí reziduálního rizika, vlastník, zdůvodnění:** Tým přijímá ruční postup pro demonstraci; automatické plánování není potvrzeným požadavkem aktuálního rozsahu.
- **Monitoring, trigger, contingency, další review:** Trigger: žádost po deadlinu je stále čekající. Spustit příkaz ručně a zkontrolovat výsledek. Review před demonstrací nebo nasazením.

### R-03

- **Popis rizika:** Úspěšné ověření proběhlo v aktuálním pracovním prostředí. Pokud se projekt nepodaří spustit po čisté instalaci na jiném počítači, nemusí být možné jej včas předvést.
- **Kategorie:** People / Resources; Schedule / Integration.
- **Počáteční riziko (L/I/priorita/důvod):** L=2, I=3 → **HIGH (6)**. README obsahuje příkazy pro instalaci a testy, ale čisté spuštění na druhém počítači není doložené; nefunkční demo by zasáhlo hlavní výstup.
- **Strategie ošetření a zdůvodnění:** MITIGATE — nechat dalšího člena týmu zopakovat postup od čistého checkoutu.
- **Opatření, vlastník, termín:** Druhý člen provede instalaci, migrace, `manage.py check` a testy podle README. Vlastník: tým. Termín: před dalším předvedením.
- **Důkaz účinnosti a stav ověření:** README uvádí reprodukovatelné příkazy a aktuálních 53 testů prošlo lokálně. Clean checkout na druhém počítači: **NOT VERIFIED**.
- **Očekávané reziduální riziko:** L=1, I=2 → **LOW (2)**, pokud druhý člen postup úspěšně zopakuje.
- **Skutečné reziduální riziko / NOT VERIFIED:** **NOT VERIFIED**.
- **Přijetí reziduálního rizika, vlastník, zdůvodnění:** Tým přijme zbytkové riziko po úspěšném opakování postupu; do té doby připraví funkční vývojové prostředí jako zálohu.
- **Monitoring, trigger, contingency, další review:** Trigger: chybějící závislost, chyba migrace nebo selhání testů. Použít ověřené vývojové prostředí a opravit README. Review před dalším předvedením.

### R-04

- **Popis rizika:** Při další změně schvalování nebo expirace se může upravit kód, ale neodpovídající návrh či testy zůstanou zastaralé. Stalo se to před C06: F2 našlo rozpor v popisu expirace, F3 zastaralé diagramy H1/H2 a D3–D4 nedostatečnou dohledatelnost a nepokryté větve.
- **Kategorie:** Technical / Quality.
- **Počáteční riziko (L/I/priorita/důvod):** L=2, I=3 → **HIGH (6)**. C06 doložilo, že k rozchodu dokumentace, kódu a testů už došlo; přehlédnutá chyba v expiraci nebo schvalování může ovlivnit stav rezervace.
- **Strategie ošetření a zdůvodnění:** MITIGATE — při každé změně schvalování/expirace projít specifikaci, implementaci, H1/H2 a testy společně.
- **Opatření, vlastník, termín:** Do review změny doplnit kontrolu vazeb požadavek → návrh → kód → test a spustit relevantní regresní testy. Vlastník: tým. Termín: při každé změně schvalování nebo expirace.
- **Důkaz účinnosti a stav ověření:** Po C06 byly opraveny H1/H2 a kontrakt; doplněny testy pro F1 a D4 a mapa testů pro D3. Celá sada má 53 testů a prošla na SQLite v `726cc62`. Použití kontrolního postupu při budoucí změně: **NOT VERIFIED**.
- **Očekávané reziduální riziko:** L=1, I=3 → **MEDIUM (3)**, pokud se kontrola provede a relevantní testy projdou; jinak skóre nesnižovat.
- **Skutečné reziduální riziko / NOT VERIFIED:** **NOT VERIFIED** pro budoucí změny, protože žádná další změna tohoto typu nebyla tímto postupem ověřena.
- **Přijetí reziduálního rizika, vlastník, zdůvodnění:** Tým přijímá zbytkové riziko jen při zachování společné kontroly dokumentace, kódu a testů; vlastník: tým.
- **Monitoring, trigger, contingency, další review:** Trigger: změna pravidel schvalování/expirace, nesoulad při review nebo selhání regresního testu. Zastavit změnu do opravy odpovídajících artefaktů a opakovat testy. Review při každé takové změně.
