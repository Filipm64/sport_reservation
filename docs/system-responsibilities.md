# Odpovědnosti systému — C03

Slice pokrývá Create, Check Availability, Confirm, Cancel, Approve a
expiraci čekajících žádostí podle [baseline v0.2](baseline-v0.2.md).
Vychází z [doménového modelu](domain-model.md) a
[driverů AD-01 až AD-05](architecture-drivers.md).

„Jeden jasný vlastník“ znamená jednoznačnou autoritu nad daným rozhodnutím
nebo stavem. Neznamená jednu instanci aplikace ani předem vybranou komponentu.

## Významné odpovědnosti

| Zdroj | Odpovědnost | Co musí rozhodovat / vlastnit | Potřebuje jednoho jasného vlastníka? | Důvod |
| :--- | :--- | :--- | :--- | :--- |
| **ODP-01:** OP-01 až OP-05; vstupy API z C02 | Přijmout požadavek a vyjádřit jeho výsledek | Význam vstupních údajů, rozlišení chybného vstupu a business odmítnutí, převod výsledku do odpovědi. | Ne pro celý systém; ano pro smlouvu každého vstupu. | Rozhraní se může lišit, ale nesmí měnit význam operace ani samo povolit doménový přechod. |
| **ODP-02:** REQ-01, REQ-03, REQ-05, REQ-06; AD-04 | Vyhodnotit oprávnění k operaci | Přihlášení, vlastnictví rezervace a schvalovací oprávnění; rozhodnutí, zda aktér smí požadovanou operaci vyvolat. | Ano pro pravidla oprávnění. | API ani jiný vstup nesmějí umožnit jinou pravomoc nad stejnou rezervací. |
| **ODP-03:** BR-01, BR-03, BR-05, BR-07; AD-05 | Vyhodnotit časová pravidla | Význam intervalu a překryvu, platnost požadovaného času, hranici rušení a deadline schválení vzhledem k rozhodnému času. | Ano pro význam pravidel a zdroje rozhodného času. | Různé operace nesmějí na stejné časové hranici rozhodovat podle odlišných pravidel. |
| **ODP-04:** OP-01, OP-03 až OP-05; stavový diagram; BR-05/06; AD-02 | Spravovat životní cyklus rezervace | Vznik DRAFT, aktuální stav a povolené přechody do CONFIRMED, PENDING_APPROVAL, CANCELLED, REJECTED a EXPIRED. | Ano pro změny stavu. | Stejná rezervace nesmí mít více nezávislých autorit, které schválí vzájemně nepřípustné přechody. |
| **ODP-05:** BR-02, BR-04, BR-06; REQ-03/04/06; AD-01 | Autoritativně rozhodnout o alokaci sportoviště | Aktuální dostupnost Resource, konflikt s CONFIRMED rezervacemi a zachování exkluzivity při Confirm i Approve. | Ano v rozsahu jednoho Resource. | Kontrola konfliktu a vznik potvrzené alokace musí tvořit konzistentní rozhodnutí i při souběhu různých rezervací. |
| **ODP-06:** OP-02, REQ-02; BR-01 až BR-04 | Poskytnout informaci o dostupnosti | Čtecí výsledek AVAILABLE/UNAVAILABLE pro existující Resource a platný interval, bez změny rezervací nebo příslibu alokace. | Ne jako výhradní autorita nad stavem; ano pro jednotný význam výsledku. | Dotaz může mít více vstupů, ale vždy musí používat stejná pravidla blokujících stavů a překryvu. |
| **ODP-07:** změna C02, BR-07, REQ-06; AD-03 | Udržet a dokončit čekající schvalovací proces | Čas podání a existence ApprovalRequest, rozpoznání vypršení, přijetí pozdějšího rozhodnutí správce a vyvolání příslušného přechodu rezervace. | Ano pro vlastnictví čekající žádosti a dokončení procesu. | Proces trvá přes více požadavků a restartů; pozdní rozhodnutí nesmí obnovit ukončenou žádost. Samotný stav Reservation mění ODP-04. |
| **ODP-08:** postpodmínky OP-01 a OP-03 až OP-05; BR-02/06/07; AD-01 až AD-03 | Trvale uchovat a obnovit rozhodnutý stav | Vlastníka, Resource, interval, stav a časy rezervace; úplné uložení změny a obnovu po restartu bez smazání ukončených záznamů. | Ano pro autoritativní uložený stav. | Úspěšná odpověď musí odpovídat uložené změně; nesmí přetrvat pouze část rozhodnutí nebo se ztratit čekající proces. |

## Požadované seskupení a oddělení

Seskupení zde znamená společná pravidla nebo konzistentní hranici práce se
sdíleným stavem. Neurčuje počet tříd, umístění souborů ani názvy komponent.

| Odpovědnost | S čím musí být seskupena a proč | Od čeho má být oddělena a proč |
| :--- | :--- | :--- |
| **ODP-01 — Požadavek a odpověď** | Interpretace vstupu a převod výsledku pro dané rozhraní patří k sobě: používají stejnou smlouvu. Musí předat ověřenou identitu a doménové údaje dalším odpovědnostem. | Od pravidel oprávnění, času, přechodů a alokace (ODP-02 až ODP-05): formát či transport se mění z jiného důvodu a vstupní data jsou nedůvěryhodná. |
| **ODP-02 — Oprávnění** | Rozhodnutí o vlastnictví a pravomoci musí pracovat s identitou aktéra a dotčenou rezervací; u změn je závaznou podmínkou ODP-04/05/07. Všechny vstupy sdílejí tutéž autoritu oprávnění. | Od způsobu přihlašování a získání identity i od formátu odpovědi: důvěryhodnost identity a business pravomoc jsou odlišné otázky. |
| **ODP-03 — Časová pravidla** | Význam intervalu, překryvu a časových hranic musí být společný pro ODP-04 až ODP-07. Při změně stavu se vyhodnotí s rozhodným časem a aktuálními údaji téže operace. | Od parsování vstupních řetězců, technického získání času a spouštění časových úloh: změna formátu nebo technologie nesmí změnit business hranice. |
| **ODP-04 — Životní cyklus** | Se stavem Reservation, výsledky ODP-02/03 a uložením ODP-08; při přechodu do CONFIRMED také s autoritativním rozhodnutím ODP-05. ODP-07 používá stejné přechody. | Od vstupního rozhraní a techniky ukládání či spouštění expirace: tyto mechanismy nesmějí definovat vlastní povolené přechody. |
| **ODP-05 — Alokace a invariant** | Kontrola dostupnosti Resource, aktuálních CONFIRMED intervalů, přechod ODP-04 a uložení ODP-08 musí tvořit jednu konzistentní hranici rozhodnutí. Jinak mezi kontrolou a alokací může vzniknout kolize. | Od informativního dotazu ODP-06 a technických mechanismů souběhu: dřívější AVAILABLE není oprávnění alokovat; mechanismus lze změnit při zachování invariantu. |
| **ODP-06 — Dostupnost** | Se společnou definicí překryvu ODP-03 a blokujících stavů ODP-05; čte dostupnost Resource a relevantní potvrzené rezervace. | Od změn životního cyklu a alokace ODP-04/05: čtení nesmí vytvořit rezervaci, zapsat expiraci ani slíbit budoucí potvrzení. |
| **ODP-07 — Čekající schvalování** | ApprovalRequest, čas podání a příslušná Reservation musí mít konzistentní životní cyklus s ODP-04/08. Rozhodnutí používá ODP-02/03 a při schválení znovu ODP-05. | Od technického způsobu spuštění pozdějšího rozhodnutí či expirace: opakované spuštění nebo výpadek nesmí změnit deadline ani obnovit konečný stav. |
| **ODP-08 — Trvalý stav** | Uložení stavu, času žádosti a výsledné alokace musí být konzistentní s ODP-04/05/07. Úspěch operace lze oznámit až po úspěšném uložení jejího výsledku. | Od business rozhodování a formátu vstupu/výstupu: změna technologie ukládání ani její selhání nesmějí vytvořit alternativní pravidla nebo být vydávána za business zamítnutí. |

