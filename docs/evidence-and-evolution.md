# Evidence and evolution

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
[baseline v0.1](baseline-v0.1.md). Formální přijetí týmem není doloženo
pro žádnou verzi. Původní tvrzení o schválení zadavatelem nelze z dostupných
podkladů ověřit, proto už není prezentováno jako doložený fakt.

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

Detailní vazby na názvy testů jsou v [revizi požadavků](requirements-review.md).
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

**Zbývající předpoklad / neznámá:** Tým musí doložit přijetí politik a
baseline. Historické pořadí odsouhlasení v0.1, analýzy dopadu a implementace
v0.2 není tímto novým ověřením prokázané. Není zvolen scheduler ani jeho
maximální zpoždění; notifikace a SLA nejsou specifikovány. SQLite serializuje
zápisy celé DB; při vyčerpání timeoutu není určena uživatelská politika retry.

**Architektonické drivery přenesené do C03:**
[AD-01 až AD-05](architecture-drivers.md): exkluzivita při souběhu,
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
[ověření chování L1](behavior-verification.md). Aplikační kód se neměnil.

## L2 — Opakovatelná kontrola architektonického pravidla

Dne 12. 10. 2026 byla doplněna a spuštěna samostatná AST kontrola,
že HTTP vstupy a expirační command nepoužívají ORM ani nepřepisují stav
rezervace. **1 test prošel**; také odmítl sedm ukázkových porušení.
Pravidlo, reprodukovatelný příkaz a skutečný log jsou v
[ověření L2](architecture-rule-verification.md). Aplikační chování se neměnilo.

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

**Drivers:** [AD-01 až AD-05](architecture-drivers.md): exkluzivita při
souběhu, konzistentní přechody, trvalé čekající schvalování, oprávnění
na všech vstupech a jednotné časové hranice.

**Decision question:** Má potvrzování a schvalování rezervací řídit
společná část rezervační aplikace, nebo samostatná služba?

**Alternatives:** A — společné rozhodování uvnitř aplikace;
B — samostatná služba vlastnící rozhodování a stav.
[Struktury a porovnání](architecture-decision.md).

**Scenario walkthrough:** Dvě čekající žádosti o stejné sportoviště
a interval jsou schválené současně. První uspěje, druhá dostane konflikt
a zůstane PENDING_APPROVAL.
[Průchod oběma variantami](architecture-decision.md#průchod-scénářem--dvě-současná-schválení).

**ADR:** [ADR-01](architecture-decision.md#adr-01--má-potvrzování-a-schvalování-rezervací-řídit-společná-část-aplikace-nebo-samostatná-služba)
volí A. Samostatná služba není požadovaná a sama neřeší souběh;
přidávala by další komunikaci, ověřování identity a možnosti selhání.

**Views:**

- Domain class: [doménový model](domain-model.md).
- Context: [G1](system-context.md).
- Static architecture: [G2](static-architecture.md).
- State ownership: [G3](statechart-ownership.md).
- Runtime/deployment: [G4](runtime-deployment.md).
- Design sequence: [H1](design-sequence.md).
- Focused design class: [H2](design-classes.md).

**Cross-view issues found/resolved:** Odděleno načtení rezervace a kolizí;
H1 výslovně ukazuje změnu doménového objektu před uložením. H2 doplňuje
společné rozhodování Confirm/Approve; G2/G4 upřesňují oddělený kontext
každého požadavku a ochranu mezi procesy. [Kontrola sedmi vazeb](cross-view-check.md).

**AS-IS → TO-BE delta:** [Tabulka J](as-is-to-be-delta.md).
Osm CHANGE provedeno, tři KEEP zachovány, obě VERIFY ověřeny testy.

**Implementation changes:** `ReservationService` vlastní přechody a
kontrolu alokace; `TimeRules` čas, `IdentityAccess` oprávnění,
`DataStore`/`DjangoDataStore` ukládání. HTTP i expirační command delegují
na společné části. Doménové entity a hodnoty jsou oddělené od ORM.
Schéma, migrace a cesty API se zachovaly; podrobná mapa souborů je v H2.

**Behaviour verification:** [L1](behavior-verification.md): 29 relevantních
testů znovu prošlo na commitu `762af3d`. Závěrečný běh po doplnění L2:
**37 testů prošlo, žádný přeskočený**; Django check bez problému,
žádné změny migrací. [Skutečný log](evidence/c03-final-verification.log).

```sh
PYTHONDONTWRITEBYTECODE=1 SPORT_BOOKING_TEST_DB=/tmp/sport-booking-c03-final.sqlite3 .venv/bin/python sport_booking/manage.py test reservations --noinput
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python sport_booking/manage.py check
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python sport_booking/manage.py makemigrations --check --dry-run
```

**Architecture conformance rule + result:** Vstupy nesmějí přímo používat
ORM ani měnit lifecycle stav. [AST kontrola L2](architecture-rule-verification.md)
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
