# G1 — Kontext systému

```mermaid
flowchart LR
    customer["Zákazník"]
    system["Reservation System"]
    approver["Správce sportoviště"]

    customer -->|"Přihlášení; Create, Availability, Confirm, Cancel — sportoviště, interval nebo ID rezervace"| system
    system -->|"ID a stav rezervace; dostupnost; výsledek přihlášení nebo chyba"| customer

    approver -->|"Přihlášení; schválení či zamítnutí — ID rezervace a rozhodnutí"| system
    approver -->|"Dotaz na rezervace; správa údajů sportů a sportovišť"| system
    system -->|"Přehled a stav rezervací; výsledek rozhodnutí, správy či přihlášení; chyby"| approver
```

Zákazník a správce jsou dvě role; jeden člověk může mít obě.
Vazby zpět k aktérům jsou odpovědi na jejich požadavky, nikoliv automatické
notifikace. Diagram vychází z [projektového rámce](intent-and-change.md)
a [baseline v0.2](baseline-v0.2.md).

Přihlašování probíhá uvnitř systému. Externí poskytovatel identity ani
notifikační služba nejsou v současném rozsahu. Databáze, vnitřní části
aplikace a mechanismus expirace se v tomto pohledu nezobrazují.
