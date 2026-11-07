# Project Frame — rezervační systém sportovišť

## Účel
Zákazník si může požádat o rezervaci sportoviště na konkrétní datum a čas.
U některých sportovišť žádost před potvrzením posoudí správce.

## Aktéři
- **Zákazník:** vytvoří žádost, zkontroluje dostupnost a může rezervaci před začátkem zrušit.
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
- Approve Reservation
- Cancel Reservation

## Webové rozhraní
- Veřejný katalog zobrazuje sportoviště, lokalitu, otevírací dobu,
  dostupnost a informaci o požadovaném schválení.
- Zákazník si může vytvořit účet, přihlásit se a spravovat pouze své
  rezervace. Správce je existující Django uživatel s `is_staff`; veřejná
  registrace toto oprávnění nepřiděluje.
- Odeslání formuláře vytvoří rovnou `CONFIRMED` nebo `PENDING_APPROVAL` podle nastavení sportoviště. Web a API používají stejné služby a pravidla.
- Správa katalogu zůstává v Django administraci. Notifikace nejsou součástí
  tohoto rozhraní ani baseline v0.2.

## Stavy
Bez schvalování vzniká rovnou `CONFIRMED`, se schvalováním `PENDING_APPROVAL`.

`PENDING_APPROVAL → CONFIRMED | REJECTED | CANCELLED | EXPIRED`.

`CONFIRMED → CANCELLED` před začátkem rezervace. Konečné stavy `REJECTED`, `CANCELLED` a `EXPIRED` se neobnovují. `DRAFT` ani samostatné potvrzení zákazníkem neexistují.

## Společná pravidla
- Interval je `[start, end)` a musí mít kladnou délku.
- Resource blokuje pouze stav `CONFIRMED`; překrývající se potvrzené
  rezervace stejného Resource nejsou povolené.
- Začátek je nejvýše 30 dní dopředu a délka rezervace nejvýše 2 hodiny.
- Čekající žádost neblokuje Resource; při schválení se dostupnost ověřuje
  znovu. Potvrzení automaticky zamítne překrývající se čekající žádosti stejného sportoviště.
- Žádost o schválení vyprší při začátku rezervace. Do té doby ji může
  vlastník zrušit a správce schválit nebo zamítnout.

## Hranice a otevřené otázky
Notifikační služba byla navržena v původním rámci, ale její události,
zprávy ani doručovací pravidla nejsou dosud specifikovány a nejsou součástí
baseline v0.2. Plánovač, který bude pravidelně spouštět expiraci, a
databázové záruky pro souběžné rezervace patří do další architektonické
iterace C03.

## Požadavky webového portálu

Veřejný katalog, účty a osobní / správní přehledy vymezují [REQ-07 až REQ-11](README.md). Osobní přehled zobrazuje aktuální platnost čekající žádosti podle BR-07 bez zápisu do databáze; fronta správce nabízí jen žádosti před začátkem rezervace.

Čas rezervace lze na webu zadat ručně nebo vybrat pomocí [hodinového rozvrhu — REQ-12](hourly-schedule.md). V obou případech platí maximálně dvě hodiny.

Provozní doba sportoviště je závazná podle [REQ-13](operating-hours.md) a BR-09; platí při vytvoření, dotazu na dostupnost i schválení.
