# Dokumentace projektu

Začněte [přehledem systému](requirements/overview.md), vyberte [požadavek](requirements/README.md) a pokračujte přes [vazby na návrh, implementaci a testy](verification/coverage.md).

| Oblast | Obsah |
| --- | --- |
| [Požadavky a pravidla](requirements/README.md) | Rozsah systému, operace, pravidla a revize požadavků |
| [Architektura](architecture/README.md) | Kontext, odpovědnosti, struktura, nasazení a rozhodnutí |
| [Detailní návrh](design/README.md) | Doménový model, životní cyklus a spolupráce objektů |
| [Ověřování a vazby](verification/README.md) | Implementace a testy pro jednotlivé požadavky, evidence ověření |
| [Historie a školní etapy](history/README.md) | Baseline, schválení, audity a vývoj projektu |
| [Zadání cvičení](../assigments/README.md) | Původní podklady pro následnou kontrolu požadavků |

## Jak dokumentaci udržovat

- Popis operace upravujte v `requirements/`, společná pravidla v [business-rules.md](requirements/business-rules.md). ID požadavků a pravidel zachovávejte i při přejmenování souborů.
- Baseline v `history/` uchovávají původní specifikace. Texty operací a pravidel byly při uspořádání převzaty z v0.2 bez přeformulování; historické kopie nejsou druhým místem pro průběžné úpravy.
- Vazby udržujte pouze v [traceability.json](verification/traceability.json). U zdrojového kódu uvádějte cestu od kořene repozitáře a název symbolu, například `ReservationService.approve`.
- Po změně vazeb nebo posunu metod a testů spusťte z kořene repozitáře `python3 scripts/update_docs.py`. Přehled v obou směrech a čísla řádků se vygenerují automaticky. Ve VS Code lze otevřít soubor odkazem a symbol najít přes Go to Symbol; GitHub podporuje i generované kotvy řádků.
- Kontrolu aktuálnosti přehledu, existence symbolů a lokálních Markdown odkazů spustíte pomocí `python3 scripts/update_docs.py --check`. Skript nemá další závislosti.
- Nové diagramy vkládejte jako Mermaid přímo k vysvětlení; samostatné obrázky patří do `assets/diagrams/`. Staré exporty jsou označené v [historii](history/README.md).

Toto uspořádání ani existence vazby na test nepotvrzují platnost požadavku, aktuální úspěšnost testu nebo týmové schválení. Kontrola podle zadání cvičení následuje samostatně.

Aktuální změna BR-07: [expirace při začátku rezervace bez 24hodinového limitu](verification/approval-expiration.md).

Aktuální životní cyklus: [vytvoření jedním krokem a automatické zamítnutí konkurentů](verification/reservation-lifecycle.md).

Webový portál: [REQ-07 až REQ-11, implementace, testy a vztah k zadáním](verification/portal-requirements.md).

Výběr termínu: [hodinový rozvrh — REQ-12, implementace a ověření](verification/hourly-schedule.md). Registr vazeb může u UI souborů uvádět samotnou cestu bez Python symbolu; generátor pak odkazuje na celý HTML, CSS nebo JS soubor.

Aktuální rozvrh a pravidla: [kompaktní týdenní tabulka a vynucování provozní doby](verification/weekly-operating-hours.md).
