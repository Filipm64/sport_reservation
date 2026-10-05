# Kontrola zadání C02 — 5. 10. 2026

Technické a dokumentační nedostatky byly opraveny. Doklady týmového
rozhodnutí a historické pořadí práce nelze vytvořit automatickou revizí.

| Bod zadání | Stav po revizi / místo |
| --- | --- |
| Čtyři úplné textové operace | Hotovo v baseline v0.1 i v0.2, jednotná struktura |
| Kontrola přijetí každého požadavku | Technická revize hotová: `requirements-review.md`; skutečné přijetí týmem čeká |
| Jednou definovaná společná pravidla | BR v každé verzi baseline; operace na ně odkazují, Project Frame je stručný přehled |
| Aktéři a cíle celého systému | Use-case pohled v0.1; use-case SVG v0.2, bez interních komponent |
| Celý stavový životní cyklus | Mermaid v0.1 a opravené SVG v0.2 |
| Aktivity jednotlivých funkcionalit | Aktivity v obou baseline; v0.2 úplné větve v Mermaid včetně expirace při Cancel |
| Konzistence textu, požadavků a diagramů | Opraveno rušení, konečné stavy, souběh, přihlášení a čas; pravidla odkazují na testy |
| Explicitní týmové schválení v0.1 | **Nedoloženo**; doplnit pravdivý záznam, ne zpětně vymyšlené datum |
| Spustitelná aplikace vytvořená s AI | Existující Django aplikace, opravená a ověřená; README obsahuje spuštění |
| Úspěšný a negativní příklad každé operace | Skutečně spuštěno v nynější v0.2; tabulka v evidenci. Historický běh v0.1 není doložen |
| Analýza dopadu před přepsáním | Analýza existuje v baseline v0.2; **historické pořadí není doloženo** |
| Dotčené i nedotčené části | Výslovně uvedeno v dopadu změny baseline v0.2 |
| Úplná nová operace Approve | OP-05 v baseline v0.2, včetně zamítnutí, expirace a oprávnění |
| Aktualizované use-case a state diagramy | Hotovo; opraveny chybné hrany stavového SVG |
| Aplikace odpovídá schválené v0.2 | Technicky ověřeno proti návrhu v0.2; **týmové schválení chybí** |
| Evidence specifikace a aplikace | Aktualizovaný `evidence-and-evolution.md`, 30 skutečně spuštěných testů |
| Konkrétní driver pro C03 | Hotovo: pět driverů AD-01 až AD-05 ve `architecture-drivers.md` |
| Commit / tag ověřených oprav | Výchozí commit zaznamenán; **výsledný commit oprav je třeba uložit a doplnit** |

## Co doplní tým před odevzdáním

1. Opravdu projít a přijmout obě baseline, zejména 30 dní, 2 hodiny,
   24 hodin, neblokování čekající žádosti, rušení a oprávnění správce.
   Zapsat skutečné datum, členy a schválenou revizi. Pokud existuje starší
   doložitelný záznam, odkázat na něj; jinak uvést skutečný současný stav.
2. Doložit z dostupné historie, zda byla v0.1 odsouhlasena a spuštěna
   před analýzou změny. Původní v0.1 aplikaci případně vyhledat v historii
   a předvést podle její baseline. Zpětné současné testy toto pořadí nedokazují.
3. Commitnout ověřené opravy a v evidenci nahradit pracovní stav skutečným
   hashem; následně opakovat příkazy z README na dané revizi.

## Platné a historické dokumenty

Pro v0.2 jsou závazné text a diagramy přímo v `baseline-v0.2.md`, pro v0.1
`baseline-v0.1.md`. Volné exporty `docs/stateDiagram.svg`, `docs/useCase.svg`
a `docs/activityDiagram.svg` a duplikát `evidence-and-evolution 2.md`
jsou historické pracovní artefakty. Nepoužívat je jako současnou baseline.
`docs/images/reservation-activity-v0.2.svg` je starší zjednodušený pohled;
úplný revidovaný diagram aktivit je vložen v baseline v0.2.
