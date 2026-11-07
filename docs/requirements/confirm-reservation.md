# REQ-03 — Automatické potvrzení při vytvoření

**Cíl:** Zákazník pro sportoviště bez schvalování získá potvrzenou rezervaci už při jejím odeslání.

REQ-03 je součástí [Create Reservation](create-reservation.md). Původní samostatná operace OP-03 / Confirm je zrušená; její ID se nepřiděluje jiné operaci. `POST /api/reservations/<id>/confirm/` již neexistuje.

**Podmínky:** Přihlášený zákazník, platný interval, dostupné sportoviště bez požadavku na schválení a žádná potvrzená kolize.

**Výsledek:** Vznikne rovnou `CONFIRMED` a překrývající se čekající žádosti stejného sportoviště přejdou do `REJECTED` ve stejné transakci. Při nesplnění podmínek nevznikne rezervace ani částečné změny.

**Pravidla:** BR-01 až BR-04, BR-06, BR-08.

[Vazby na implementaci a testy](../verification/coverage.md#req-03) · [Požadavky](README.md)
