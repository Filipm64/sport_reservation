# Doménová pravidla

<a id="br-01"></a>

- **BR-01 — Časový interval:** Interval je polouzavřený `[start, end)`;
  platí `start < end`. Dva intervaly, které se dotýkají pouze na hranici,
  se nepřekrývají.
<a id="br-02"></a>

- **BR-02 — Výhradní Resource:** Stejný Resource nesmí mít překrývající
  se rezervace `CONFIRMED`. K překryvu dochází, když
  `existing.start < requested.end` a `requested.start < existing.end`.
  `PENDING_APPROVAL`, `REJECTED`, `EXPIRED` a `CANCELLED`
  Resource neblokují.
<a id="br-03"></a>

- **BR-03 — Platný čas:** Začátek je nyní nebo v budoucnu, nejvýše 30 dní
  od aktuálního času. Délka je kladná a nejvýše 2 hodiny. Přesné hranice
  30 dní a 2 hodin jsou povolené.
<a id="br-04"></a>

- **BR-04 — Dostupný Resource:** Pro nedostupný Resource nelze vytvořit rezervaci ani schválit čekající žádost;
  Check Availability pro něj vrací `UNAVAILABLE`.
<a id="br-05"></a>

- **BR-05 — Zrušení:** Vlastník smí před začátkem zrušit rezervaci ve
  stavu `PENDING_APPROVAL` nebo `CONFIRMED`. Záznam se nemaže.
  Opakované zrušení ani zrušení po začátku není povoleno.
<a id="br-06"></a>

- **BR-06 — Souběh:** V jednom výsledném stavu nesmějí být dvě
  překrývající se rezervace stejného Resource `CONFIRMED`. Souběžné operace mají výsledek odpovídající sériovému pořadí.
  Pokud Approve uspěje dříve než Cancel, vlastník stále může
  před začátkem zrušit `CONFIRMED`. Pokud Cancel uspěje dříve,
  schválení již není povolené.
<a id="br-07"></a>

- **BR-07 — Schvalování:** Resource s `requires_approval = false` se může
  potvrdit bez správce. U Resource s `requires_approval = true` přejde
  vytvořená rezervace do `PENDING_APPROVAL`. Žádost čeká na rozhodnutí správce nebo zrušení vlastníkem
  nejdéle do začátku rezervace; pevný limit 24 hodin se nepoužívá.
  Žádost vyprší v okamžiku `reservation.starts_at` (`now >= starts_at`). Po vypršení již nesmí být schválena, zamítnuta ani zrušena.
  Stav `EXPIRED` se uloží při pokusu o Approve/Cancel nebo při běhu
  expiračního příkazu. Mezi těmito událostmi může uložený stav zůstat
  `PENDING_APPROVAL`; nejde o platnou žádost a Resource stejně neblokuje.

<a id="br-08"></a>

- **BR-08 — Automatické zamítnutí konkurentů:** Při každém vzniku `CONFIRMED`, ať vytvořením nebo schválením správcem, se všechny ostatní `PENDING_APPROVAL` stejného sportoviště s překrývajícím se intervalem změní na `REJECTED`. Sousední intervaly a jiná sportoviště nejsou dotčeny. Potvrzení i zamítnutí tvoří jednu transakci. Pozdější zrušení vítěze zamítnuté žádosti neobnovuje.

Pravidla vycházejí z [baseline v0.2](../history/baseline-v0.2.md#doménová-pravidla).
BR-07 byl změněn rozhodnutím uživatele 7. 11. 2026: expirace nastává pouze při začátku rezervace, bez 24hodinového limitu.

[Vazby požadavků na pravidla, implementaci a testy](../verification/coverage.md) · [Přehled požadavků](README.md)

Rozhodnutí uživatele 7. 11. 2026 dále ruší `DRAFT` a samostatný Confirm; rezervace vzniká rovnou jako `CONFIRMED` nebo `PENDING_APPROVAL`.

<a id="br-09"></a>

- **BR-09 — Provozní doba sportoviště:** Každé sportoviště má čas otevření a zavření v Europe/Prague, platný každý den. Musí platit `opens_at < closes_at`; tento rozsah nepodporuje provoz přes půlnoc. Celá rezervace musí ležet uvnitř jednoho denního provozního intervalu. Začátek přesně při otevření a konec přesně při zavření jsou povolené. Pravidlo platí pro vytvoření automatické i čekající rezervace, ruční a blokový vstup, API a opětovnou kontrolu při schválení. Mimo provozní dobu vrací dotaz na dostupnost UNAVAILABLE. Správu doby provádí současná role správce podle REQ-13. Změna doby zpětně neruší již potvrzené rezervace.

BR-09 byl přijat požadavkem uživatele 7. 11. 2026 a nahrazuje dosavadní informativní význam otevírací doby.
