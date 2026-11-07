# REQ-12 — Výběr rezervace z hodinového rozvrhu

**Zdroj:** Požadavek uživatele 7. 11. 2026: vedle ručního zadání času umožnit výběr jednoho nebo dvou hodinových bloků v rozvrhu a zachovat maximální délku rezervace 2 hodiny.

**Aktér:** Přihlášený zákazník, případně správce rezervující jako zákazník.

**Vstup:** Sportoviště, den v Europe/Prague určující zobrazený týden a jeden nebo dva navazující hodinové bloky stejného dne. Alternativně přesný ručně zadaný začátek a konec. Oba způsoby používají stejný proces REQ-01, stejné stavy a společná pravidla.

**Hlavní scénář:**
1. Zákazník vybere sportoviště a den od dneška nejvýše 30 dní dopředu. Zobrazí se kompaktní týdenní tabulka: pondělí až neděle ve sloupcích a hodiny v řádcích. Lze přecházet mezi týdny v povoleném horizontu.
2. Potvrzené kolize, minulé bloky, bloky za povoleným horizontem nebo nedostupné sportoviště jsou nezvolitelné. Čekající žádosti samy neblokují čas. Nezobrazují se údaje jiných zákazníků.
3. Zákazník označí jeden nebo dva navazující bloky. UI ukáže zvolený čas a délku; třetí nebo nesousedící blok nepřidá.
4. Při odeslání server znovu sestaví a ověří bloky pro odeslané sportoviště a den. Z klienta nepřebírá vypočtenou délku ani jeho tvrzení o dostupnosti.
5. Společná rezervační služba znovu pod ochranou proti souběhu ověří dostupnost a uloží `CONFIRMED` nebo `PENDING_APPROVAL` podle REQ-01. Úspěšné odeslání zachová vybraný den a sportoviště v rozvrhu.

**Časová pravidla:** Jeden blok trvá 60 skutečných minut, dva bloky nejvýše 120 minut. Musí bezprostředně navazovat; nesousedící bloky netvoří jednu rezervaci. BR-03 vynucuje limit i při ručním zadání a přes API. Při změně letního času má den 23 nebo 25 skutečných hodin; opakované časy se rozlišují UTC offsetem. Rozvrh nabízí jen celé hodinové bloky uvnitř provozní doby podle BR-09. Jeden výběr patří do jednoho dne; nelze spojit bloky různých dnů. Opakovaná hodina při změně času má samostatný řádek; neexistující hodina je označena pomlčkou.

**Chybové výsledky:** Prázdný výběr, více než dva bloky, mezera, opakovaná či neznámá hodnota bloku, neplatný den, neznámé sportoviště nebo již obsazený blok → chyba bez vytvoření rezervace. Pokud termín obsadí jiný požadavek až po načtení rozvrhu, rozhoduje aktuální kontrola rezervační služby.

**Ruční zadání:** Přepnutí na „Zadat přesný čas“ zachovává i necelé hodiny. Nadále platí validace a dvouhodinový limit. Bez JavaScriptu jsou dostupné obě části formuláře a konečnou platnost ověřuje server.

**Vedlejší účinky zobrazení:** Žádné. Výběr políček ani kontrola dostupnosti nevytváří rezervaci. Host musí před odesláním rezervace projít přihlášením.

**Akceptační příklady:**

| Vstup / situace | Očekávaný výsledek |
| --- | --- |
| 12:00–13:00 | Jedna rezervace dlouhá 1 hodinu |
| 12:00–13:00 a 13:00–14:00 | Jedna rezervace 12:00–14:00 |
| 12:00–13:00 a 14:00–15:00 | Odmítnutí bez vytvoření rezervace |
| Tři hodinové bloky | Odmítnutí bez vytvoření rezervace |
| Potvrzená rezervace 10:30–11:00 | Blok 10:00–11:00 obsazený; sousední bloky zůstávají volné |
| Nová kolize po načtení rozvrhu | Odmítnutí při odeslání, žádná dvojí alokace |
| Ruční délka 3 hodiny | Odmítnutí serverem i bez JavaScriptu |

[Návrh a vlastnictví pravidel](../design/hourly-schedule.md) · [Implementace, UI a konkrétní testy](../verification/coverage.md#req-12) · [Ověření změny](../verification/hourly-schedule.md) · [Přehled požadavků](README.md)

Aktuální upřesnění týdenní tabulky a provozní doby: [REQ-13](operating-hours.md) a [ověření změny](../verification/weekly-operating-hours.md).
