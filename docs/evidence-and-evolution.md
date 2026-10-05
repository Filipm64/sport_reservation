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

**Přijatá baseline:** `docs/baseline-v0.2.md`; schválena zadavatelem
5. 10. 2026 a ověřena automatickými testy. Samostatný týmový zápis
schválení zatím v repozitáři není.

**Předvedené základní operace:** Create Reservation, Check Availability,
Confirm Reservation, Cancel Reservation a nová Approve Reservation.
Jde o Django JSON API; ukázka běží v `sport_booking/`.

**Skutečně provedené příklady ověření:** `python manage.py test reservations`
— 16 testů prošlo na Django 6.1.1 a SQLite. Testy skutečně volají API přes
Django test client:
- Create: vytvoří `DRAFT`; shodný začátek a konec vrátí chybu.
- Check Availability: sousední interval je dostupný; potvrzený překryv
  nedostupný; `DRAFT` a `PENDING_APPROVAL` čas neblokují.
- Confirm: bez schvalování přejde do `CONFIRMED`; kolidující potvrzení je
  odmítnuto.
- Approve: správce může po nasimulované prodlevě žádost potvrdit nebo
  zamítnout; běžný uživatel nemůže rozhodovat; žádost starší 24 hodin
  vyprší; nová kolize schválení odmítne.
- Cancel: čekající žádost se změní na `CANCELLED` a záznam zůstane;
  zrušení po začátku je odmítnuto.
- `expire_reservations` byl spuštěn v testu a převedl starou žádost do
  `EXPIRED`.

Dále prošly `python manage.py check` a
`python manage.py makemigrations --check --dry-run`.

**Nalezený nesoulad a způsob vyřešení:** První běh testu dostupnosti
vrátil `UNAVAILABLE`, protože test zkoušel čas na sportovišti, které už
mělo překrývající se potvrzenou rezervaci. Implementace odpovídala pravidlu;
test pro izolované `DRAFT` ověření byl přesunut na jiné sportoviště.
Opakovaný běh všech 16 testů prošel.

**Shrnutí dopadu změny:** Resource může vyžadovat schválení. Čekající žádost
Resource neblokuje; při schválení se znovu ověřuje konflikt. Přibyly stavy
`PENDING_APPROVAL`, `REJECTED` a `EXPIRED`, oprávnění `is_staff` pro
schvalování, uložení času žádosti a příkaz pro expiraci po 24 hodinách
(nebo při začátku rezervace, je-li dříve).

**Zbývající předpoklad / neznámá:** Příkaz `expire_reservations` je nutné
plánovaně spouštět; plánovač není součástí ukázky. Notifikace nejsou
specifikovány. Souběh byl pokryt transakcemi, ale zátěžový test paralelních
požadavků ani produkční databáze nebyly součástí ověření.

**Architektonické drivery přenesené do C03:** Plánované spouštění expirace,
spolehlivé transakční zamykání nad stejným Resource, oprávnění správců
a rozhodnutí, zda a kdy se mají odesílat notifikace.

**Commit / tag aplikace:** Nebyl vytvořen; změny zůstávají pouze lokálně
a nic nebylo odesláno na GitHub.
