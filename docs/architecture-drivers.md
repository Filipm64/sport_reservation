# Architektonické drivery pro C03

Driver je požadavek nebo omezení, které významně ovlivní strukturu systému.
Není to databázový ovladač ani seznam vybraných technologií. Tyto drivery
vycházejí z baseline v0.2; nepřidávají platby ani notifikace do C02.

| ID / priorita | Zdroj a důvod | Konkrétní scénář a požadovaný výsledek | Evidence C02 / rozhodnutí pro C03 |
| --- | --- | --- | --- |
| AD-01 / vysoká | BR-02, BR-06; REQ-04. Exkluzivní sportoviště nesmí být přiděleno dvakrát. | Dva uživatelé současně potvrzují překrývající se žádosti stejného Resource; také dva správci současně schvalují. Nejvýše jedna alokace uspěje, druhá dostane konflikt a zůstane DRAFT/PENDING_APPROVAL. | Tři testy alokace v `ReservationConcurrencyTests` (Confirm/Confirm, Approve/Approve, Confirm/Approve). SQLite IMMEDIATE nyní serializuje zápisy celé databáze. C03 musí zvolit hranici transakce a záruky pro cílovou databázi; zachovat i kombinaci Confirm/Approve při změně příznaku Resource. Měřítko úspěchu: žádné dvě kolidující CONFIRMED po dokončení požadavků. |
| AD-02 / vysoká | BR-06; REQ-05, REQ-06. Rozhodnutí a stažení žádosti musí být konzistentní. | Approve/Confirm se potká s Cancel stejné rezervace před začátkem a expirací. Cancel první → pozdější schválení odmítnuto; schválení první → následné Cancel povoleno. Výsledek CANCELLED, záznam zachován. | Dva souběžné a jeden sekvenční API test. C03 udrží společné pravidlo přechodů a pořadí zámků; prověří závody s expirací. Kritérium není „uspěje vždy pouze první operace“. |
| AD-03 / vysoká | BR-07; REQ-06. Čekání přesahuje jeden HTTP požadavek a musí přežít restart. | Žádost zůstane bez rozhodnutí; server se restartuje; při `now >= min(requested_at + 24 h, starts_at)` už Approve/Cancel nesmí žádost přijmout. Opakovaný běh expirace nemění již konečné stavy. | Čas a stav jsou v DB; API ověřuje deadline a existuje příkaz `expire_reservations`. C03 vybere spouštění, obnovu po výpadku a dohled nad selháním úloh. Maximální zpoždění zápisu EXPIRED je TBD k odsouhlasení, nikoliv vymyšlené SLA. |
| AD-04 / vysoká | OP-01 až OP-05; REQ-01, REQ-03, REQ-05, REQ-06. Ochrana cizích žádostí a pravomoci správce. | Nepřihlášený uživatel je odmítnut; jiný zákazník nemůže potvrdit/zrušit cizí rezervaci; zákazník nemůže schvalovat. Admin nesmí ručně vytvořit kolidující CONFIRMED ani smazat historii. | API test oprávnění, staff test a test omezení adminu. C03 sjednotí pravidla na všech vstupních rozhraních. Model `is_staff` je stávající volba; rozsah správce na konkrétní sportoviště je otevřená otázka, nikoliv přijatý požadavek. |
| AD-05 / střední | BR-01, BR-03, BR-05, BR-07. Časové hranice musí zůstat stejné ve všech operacích. | Časy s pásmem se porovnají jako skutečné okamžiky. Sousední intervaly nekolidují; přesně na deadline nelze rozhodnout; přesně na start nelze zrušit. | API testy hranic a fixovaného času. C03 posoudí společný zdroj hodin a umístění pravidel; scheduler a API nesmějí používat odlišnou definici expirace. |

## Omezení a nezodpovězené otázky

- C02 má jednoduchou spustitelnou lokální Django/SQLite aplikaci. Nepotřebuje
  frontu, externí službu ani předčasné vrstvení kódu.
- Celodatabázový zámek chrání korektnost, ale omezuje paralelní zápisy.
  Očekávaný počet uživatelů, zatížení a cílová latence nejsou zadány (TBD).
  Timeout SQLite 20 sekund je technická hodnota ukázky, nikoliv business SLA.
- Notifikace nejsou specifikované; externí notifikační služba zatím není
  přijatý driver. Pokud ji tým přijme, nejprve určí události a požadované
  doručení a až poté řeší technickou integraci.
- Technické driver scénáře lze ověřit testy. Politiky 24 hodin, 30 dní,
  2 hodiny a pravomoci správce musí tým skutečně přijmout a zdůvodnit.
