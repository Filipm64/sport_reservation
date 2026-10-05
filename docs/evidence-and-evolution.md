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
