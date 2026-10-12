# I — Cross-view kontrola

**Datum:** 12. 10. 2026. Kontrolován návrh pro dvě současná schválení
stejného sportoviště. C2 zde znamená dokument odpovědností systému.

| Kontrola | Výsledek a konkrétní vazba |
| --- | --- |
| C02 ↔ G2 | **Shoda.** Správa rezervací řídí Create, Confirm, Approve, Cancel a expiraci. Časová pravidla zajišťují BR-01/03/05/07; Správa rezervací spolu s chráněným ukládáním zachovává BR-02/06. Dostupnost je pouze čtecí a čekající žádosti neblokují. |
| C2 ↔ G2 | **Shoda.** ODP-01 až ODP-08 jsou každá právě jednou přiřazené v tabulce G2. Životní cyklus, alokace a čekající schvalování patří Správě rezervací; ukládání nerozhoduje o business výsledku. |
| G2 ↔ H1 | **Shoda.** H1 používá jen Vstupní rozhraní → Identita a oprávnění / Správa rezervací a Správa rezervací → Identita a oprávnění / Časová pravidla / Ukládání dat. Vlastní volání uvnitř Správy rezervací nepřidává novou závislost. Správci jsou aktéři z G1. |
| H1 ↔ H2 | **Zpřesněno.** Načtení je nyní rozdělené na `load_protected()` a `confirmed_intervals()`. Čas má vlastníka `TimeRules`; rozhodnutí `ReservationService._decide_confirmation()`. Stav mění `Reservation.confirm()`, uložení dokončí `save()` a `commit()`; konflikt končí `rollback()`. |
| Statechart ↔ G3/H1 | **Zpřesněno.** Přechod PENDING_APPROVAL → CONFIRMED vyvolává Správa rezervací, nikoliv Ukládání dat. Při kolizi Y zůstává PENDING_APPROVAL; žádný nový přechod nevzniká. G3 přiřazuje všechny změny stejnému ownerovi. |
| G2 ↔ G4 | **Shoda po zpřesnění.** Všech šest částí je mapováno do webového procesu; expirace používá systémový vstup, Správu rezervací, Časová pravidla a Ukládání dat ve krátkodobém procesu stejné aplikace. Oba používají jeden SQLite soubor. Kontext každé operace je oddělený, ochrana platí mezi procesy. |
| ADR ↔ G2/G4 | **Shoda po zpřesnění.** Varianta A je vidět jako jedna aplikace bez rezervační služby. Confirm a Approve mají v H2 společné `_decide_confirmation()` uvnitř Správy rezervací. Expirační příkaz je další vstup stejného nasazení, nikoliv nezávislý vlastník stavu. |

## Opravy artefaktů před změnou kódu

- **H1:** oddělené načtení rezervace a kolizí, explicitní odečet času po
  získání ochrany, změna doménového objektu a dokončení zápisu. Původní
  „ulož CONFIRMED“ mohlo mylně přisoudit rozhodnutí ukládací části.
- **H2:** doplněné společné `_decide_confirmation()` pro Confirm/Approve
  a smlouva odděleného kontextu ukládání pro každý požadavek.
- **G2/G4:** zpřesněna ochrana mezi požadavky i procesy; nejde o jeden
  sdílený rozpracovaný databázový kontext pro všechny požadavky.

**Závěr:** V kontrolovaném slice nezůstává rozpor mezi návrhovými pohledy.
H1/H2 jsou záměrně zaměřené na schválení a konflikt; nemusí zobrazovat
každou operaci celé baseline. Kontrola nezměnila business pravidla ani kód.
Po opravách prošla kontrola syntaxe a skutečné vykreslení diagramů G2, G4,
H1 a H2. Upravené H1 a H2 byly také vizuálně zkontrolovány.

Následné sjednocení kódu podle G2/H2 je zaznamenané v evidenci C03.
Automatické spouštění expirace zůstává nedořešené. Kontrola pohledů není
náhradou týmového schválení baseline.
