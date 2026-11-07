# REQ-13 — Nastavení a vynucování provozní doby

**Zdroj:** Požadavek uživatele 7. 11. 2026: provozní dobu nastavuje majitel / správce sportoviště, který může schvalovat rezervace; zákazník nesmí vytvořit rezervaci mimo otevřenou dobu.

**Aktér:** Současná role správce (`is_staff`) pro nastavení, zákazník pro rezervaci. V tomto rozsahu roli majitele zastupuje stávající společná role správce pro všechna sportoviště. Samostatné přidělování konkrétních vlastníků není součástí změny.

**Nastavení:** Správce v části „Nastavit provozní dobu sportovišť“ zadá čas od–do pro konkrétní sportoviště. Jedna denní doba platí každý den v týdnu v Europe/Prague. Musí být otevření před zavřením; nulová doba a provoz přes půlnoc se odmítají. Stejná validace konfigurace platí v Django administraci.

**Oprávnění:** Změna přes `POST /sportoviste/<id>/provozni-doba/` vyžaduje aktivní přihlášený účet správce a CSRF ochranu. Běžný zákazník dostane 403, host je přesměrován na přihlášení. GET změnu neprovádí a je odmítnut.

**Hlavní scénář rezervace:** Server načte aktuální provozní dobu spolu se sportovištěm. Ověří, že je celý interval uvnitř jedné denní provozní doby a délka nepřekračuje dvě hodiny. Kontrola je společná pro ruční vstup, týdenní bloky a API. Před schválením čekající žádosti se provozní doba ověří znovu pod ochranou proti souběhu.

**Výsledky:** Platná konfigurace se uloží atomicky. Neplatný interval konfiguraci nemění. Pokus o rezervaci mimo provozní dobu je odmítnut bez vytvoření rezervace. Dotaz na takový interval vrátí UNAVAILABLE. Celé uzavřené hodinové řádky se v týdenním rozvrhu nenabízejí; blok, který se nevejde celý, není volitelný. Přesný interval s necelými hodinami lze zadat ručně.

**Změna existující doby:** Platí pro nové rezervace a další schválení. Již potvrzené rezervace se automaticky neruší ani nemění. Čekající žádost, která se do nové doby nevejde, nelze schválit; správce ji může zamítnout a vlastník před začátkem zrušit.

**Příklady:** Pro dobu 08:00–22:00 jsou 08:00–09:00 a 20:00–22:00 povolené; 07:00–08:00, 21:00–23:00 a 22:00–23:00 nikoli. Pro 08:30–20:30 lze ručně rezervovat 08:30–09:30; celé bloky 08:00–09:00 a 20:00–21:00 se nenabízejí.

**Pravidla:** BR-01, BR-03, BR-04, BR-09.

[Návrh a vlastníci](../design/hourly-schedule.md) · [Implementace a testy](../verification/coverage.md#req-13) · [Evidence změny](../verification/weekly-operating-hours.md) · [Požadavky](README.md)
