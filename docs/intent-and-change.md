# Project Frame — rezervační systém sportovišť

## Účel
Zákazník si může požádat o rezervaci sportoviště na konkrétní datum a čas.
U některých sportovišť žádost před potvrzením posoudí správce.

## Aktéři
- **Zákazník:** vytvoří žádost, zkontroluje dostupnost, požádá o potvrzení
  a může rezervaci před začátkem zrušit.
- **Správce sportoviště:** spravuje Resource a schvaluje nebo zamítá
  čekající žádosti. V ukázce je oprávnění reprezentováno příznakem
  přihlášeného Django uživatele `is_staff`.

## Pojmy a uložená data
- **Sport:** typ sportovní aktivity.
- **Resource:** rezervovatelné sportoviště; obsahuje název, sport,
  lokalitu, otevírací dobu, příznak dostupnosti a informaci, zda vyžaduje
  schválení.
- **Reservation:** uživatel, Resource, začátek, konec, stav, čas vytvoření
  a případný čas žádosti o schválení.

## Operace
- Create Reservation
- Check Availability
- Confirm Reservation
- Approve Reservation
- Cancel Reservation

## Webové rozhraní
- Veřejný katalog zobrazuje sportoviště, lokalitu, otevírací dobu,
  dostupnost a informaci o požadovaném schválení.
- Zákazník si může vytvořit účet, přihlásit se a spravovat pouze své
  rezervace. Správce je existující Django uživatel s `is_staff`; veřejná
  registrace toto oprávnění nepřiděluje.
- Rezervační formulář kontroluje dostupnost a vytváří `DRAFT`. Potvrzení,
  schválení a zrušení volají stejné služby jako API; webové rozhraní proto
  nepřidává vlastní pravidla životního cyklu.
- Správa katalogu zůstává v Django administraci. Notifikace nejsou součástí
  tohoto rozhraní ani baseline v0.2.

## Stavy
`DRAFT → CONFIRMED` pro Resource bez schvalování.

`DRAFT → PENDING_APPROVAL → CONFIRMED | REJECTED | EXPIRED` pro Resource
vyžadující schválení.

`DRAFT`, `PENDING_APPROVAL` nebo `CONFIRMED` lze před začátkem změnit na
`CANCELLED`. Zrušené, zamítnuté ani vypršené záznamy se nemažou.

## Společná pravidla
- Interval je `[start, end)` a musí mít kladnou délku.
- Resource blokuje pouze stav `CONFIRMED`; překrývající se potvrzené
  rezervace stejného Resource nejsou povolené.
- Začátek je nejvýše 30 dní dopředu a délka rezervace nejvýše 2 hodiny.
- Čekající žádost neblokuje Resource; při schválení se dostupnost ověřuje
  znovu.
- Žádost o schválení vyprší po 24 hodinách nebo při začátku rezervace,
  podle toho, co nastane dříve.

## Hranice a otevřené otázky
Notifikační služba byla navržena v původním rámci, ale její události,
zprávy ani doručovací pravidla nejsou dosud specifikovány a nejsou součástí
baseline v0.2. Plánovač, který bude pravidelně spouštět expiraci, a
databázové záruky pro souběžné rezervace patří do další architektonické
iterace C03.
