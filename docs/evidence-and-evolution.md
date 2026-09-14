# C01 Engineering Spike

## Question / unknown:
Dokáže Django ORM uložit rezervaci včetně uživatele, sportoviště, časového intervalu,
stavu a data vytvoření do databáze a následně přes `Reservation.objects.get()`
načíst stejná data? Potřebujeme ověřit persistenci, nikoliv pouze existenci objektu v paměti.

## What we did:
- Do existujícího Django projektu jsme přidali aplikaci `reservations`, modely
  `Sport`, `Resource`, `Reservation`. Uživatel je standardní
  Django model.
- Rezervace obsahuje vazby na uživatele a sportoviště, začátek, konec, stav
  (`DRAFT`, `CONFIRMED`, `CANCELLED`) a automatické datum vytvoření.
  DB constraints vynucují kladnou délku intervalu a platný stav.
- Přidali jsme šest automatických testů: načtení polí a vazeb, persistenci změn
  stavu, odmítnutí nulového/záporného intervalu, neznámého stavu,


## Observed result:
Ověřeno 14. 9. 2026 s Django 6.1.1 a SQLite:
- Test runner vytvořil izolovanou in-memory SQLite databázi
  a úspěšně aplikoval migrace včetně `reservations.0001_initial`.
- `test reservations`: všech 6 testů prošlo 
- `check`: žádné problémy

## Decision / what changes because of the result:
Pro další iteraci používáme Django ORM a verzované migrace. Uložení a načtení
rezervace ověřujeme standardním `TestCase`. Rezervace se vytváří ve stavu DRAFT podle
projektového rámce; uživatele neduplikujeme vlastním modelem. Nové změny schématu
budou mít migrace a testy nad DB. 
