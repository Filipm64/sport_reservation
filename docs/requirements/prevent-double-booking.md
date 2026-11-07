# REQ-04 — Zabránění dvojí rezervaci

REQ-04 vyžaduje nejvýše jednu potvrzenou rezervaci stejného sportoviště pro překrývající se interval. Aktuální vazby jsou v generovaném přehledu; původní revize C02 je historický podklad.

Současné Create/Create, Approve/Approve a Create/Approve se vyhodnocují pod jednou ochranou proti souběhu. Při potvrzení se konkurenční čekající žádosti automaticky zamítnou. Dostupnost je pouze informativní.

## Související podklady

- [Vazby REQ-04: pravidla, návrh, implementace a testy](../verification/coverage.md#req-04)
- [Přehled požadavků](README.md)
- [Původní revize](review.md)
