## Doménová pravidla

Tato pravidla platí pro celý systém a jednotlivé operace na ně odkazují, aniž by je opakovaly v každé sekci.

- DR-01: `Reservation` je požadavek na alokaci `Resource` na konkrétní časový interval. Po vytvoření má stav `DRAFT`; teprve po potvrzení se stává platnou rezervací.
- DR-02: `Resource` je dostupný v intervalu, pokud v daném čase neexistuje jiná rezervace ve stavu `CONFIRMED` pro stejný `Resource`.
- DR-03: Pro stejný `Resource` nesmí existovat dvě `CONFIRMED` rezervace, které se časově překrývají.
- DR-04: Rezervace se vytvoří pouze pro časový interval, kde `end > start`.
- DR-05: `Reservation` může být vytvořena maximálně 30 dní dopředu.
- DR-06: Maximální délka jedné rezervace je 2 hodiny.
- DR-07: Rezervace, která byla potvrzena, může být zrušena jen formou přechodu do stavu `CANCELLED`; data nejsou fyzicky mazána.
- DR-08: `Cancel Reservation` neodstraňuje `Reservation` z evidence; pouze mění stav a zaznamenává důvod a čas zrušení.
- DR-09: `Check Availability` nevede ke změně stavu a nepřiděluje zdroj. Pouze vrací informaci o vhodnosti intervalu pro daný `Resource`.
- DR-10: `Reservation` a `Resource` jsou vždy asociovány s konkrétním sportovištěm a datem/časem, které je relevantní pro výpočet konfliktů a dostupnosti.

---

## OP-01 — Create Reservation

Cíl / hodnota pro uživatele:
- Uživatel může podat žádost o rezervaci sportoviště bez okamžitého potvrzení a získat informaci, že jeho požadavek byl uložen pro další zpracování.

Spouštěcí událost:
- Uživatel vyplní údaje o sportovišti, datumu, začátku, konci a odešle žádost o rezervaci.

Pozorovatelný požadavek / požadavky:
- Uživatel zadá `Resource`, počáteční a koncový čas, a osobní identifikaci `User`.
- Systém musí ověřit, že požadavek splňuje základní doménová pravidla a zároveň zůstává v důsledku neověřeného stavu v režimu `DRAFT`.

Předpoklady:
- `User` je známý a validní.
- `Resource` existuje a je správně definovaný.
- `start` a `end` jsou v očekávaném formátu a leží v rámci otevírací doby, pokud je to relevantní pro danou doménu.

Stav po úspěšném provedení:
- Vytvoří se nová `Reservation` ve stavu `DRAFT`.
- Rezervace je evidována v systému jako žádost, nikoli jako definitivní alokace.

Změna stavu:
- Nová entita přejde do stavu `DRAFT`.
- Není to ještě `CONFIRMED`; proto ještě neovlivňuje dostupnost `Resource` v běžném smyslu alokace.


Hlavní úspěšný scénář:
1. Uživatel zvolí `Resource` a vyplní časový interval.
2. Systém ověří, že interval je validní (viz pravidla).
3. Systém vytvoří `Reservation` ve stavu `DRAFT` s datem vytvoření a identifikací uživatele.
4. Rezervace je uložena.

Alternativní / chybové výsledky:
- Chyba: časový interval je neplatný (konec je před začátkem).
- Chyba: požadavek přesahuje limit 30 dní dopředu.
- Chyba: délka rezervace překračuje 2 hodiny.
- Chyba: zadané `Resource` neexistuje.
- Chyba: uživatel není autorizovaný nebo neexistuje.

Příklady ověření:
- Vytvoření rezervace na 15:00–16:30 pro sportovní hřiště v příštím dni => úspěch.
- Vytvoření rezervace na 18:00–17:00 => chyba.
- Vytvoření rezervace na 1. ledna 2027 pro čas 10:00–12:00, pokud je vytvoření limitováno na 30 dní => chyba.
- Vytvoření rezervace 3 hodin dlouhé => chyba.

Zdůvodnění / zdroj:
- Tento krok odpovídá počátečnímu návrhu systému: zákazník podává žádost, která se po potvrzení stává platnou rezervací.

---

## OP-02 — Check Availability

Cíl / hodnota pro uživatele:
- Uživatel nebo provozovatel může rychle zjistit, zda je vybrané sportoviště v požadovaném intervalu dostupné.

Spouštěcí událost:
- Uživatel zadá `Resource`, datum a čas začátku a konce a požaduje kontrolu dostupnosti.

Pozorovatelný požadavek / požadavky:
- Systém musí vrátit informaci o tom, zda je interval pro dané `Resource` volný.
- Kontrola nevede ke změně dat ani k vytvoření rezervace.

Předpoklady:
- `Resource` je známý a validní.
- Interval je správně zadán a splňuje základní validaci.

Stav po úspěšném provedení:
- Systém vrátí stav `AVAILABLE` nebo `UNAVAILABLE` pro zadaný interval.
- Datová struktura `Reservation` zůstává nezměněna.

Hlavní úspěšný scénář:
1. Uživatel zadá `Resource` a interval.
2. Systém ověří základní validaci intervalu.
3. Systém porovná požadovaný interval s ostatními `CONFIRMED` rezervacemi pro daný `Resource`.
4. Vrátí výsledek: `AVAILABLE` nebo `UNAVAILABLE`.

Alternativní / chybové výsledky:
- Chyba: interval je neplatný.
- Chyba: `Resource` neexistuje.
- Výsledek: `UNAVAILABLE` kvůli překryvu s již potvrzenou rezervací.
- Výsledek: `AVAILABLE`, pokud nejsou žádné konflikty.

Příklady ověření:
- Pro `Resource` A existuje potvrzená rezervace 10:00–11:30; dotaz na 11:00–12:00 => `UNAVAILABLE`.
- Stejný dotaz pro 12:00–13:00 => `AVAILABLE`.
- Dotaz pro neexistující `Resource` => chyba.

Zdůvodnění / zdroj:
- Tato operace odpovídá požadavku na předběžné ověření dostupnosti bez vytvoření rezervace, což je typická funkce v systému rezervací sportovišť.

---

## OP-03 — Confirm Reservation

Cíl / hodnota pro uživatele:
- Systém přijme žádost o rezervaci jako platnou alokaci sportoviště pouze tehdy, když je úspěšně uhrazena a rezervace se tak stává aktivní.

Spouštěcí událost:
- Uživatel dokončí platbu za existující `Reservation` ve stavu `DRAFT`.

Pozorovatelný požadavek / požadavky:
- Systém musí ověřit, že zadaná rezervace existuje, je ve vhodném stavu pro potvrzení, úspěšně obdržel platbu a nevyvolává konflikty s jinou potvrzenou rezervací.
- Potvrzení je podmínkou pro vytvoření platné alokace `Resource` a probíhá až po úspěšné platbě.

Předpoklady:
- `Reservation` existuje.
- `Reservation` má stav `DRAFT`.
- Platba byla úspěšně zpracována a je ve stavu `PAID`.
- V intervalu rezervace není jiná `CONFIRMED` rezervace pro stejný `Resource`.

Stav po úspěšném provedení:
- `Reservation` přejde do stavu `CONFIRMED`.
- Rezervace se stává aktivní a je považována za skutečně rezervovaný čas `Resource`.

Změna stavu:
- `DRAFT` → `CONFIRMED` po úspěšné platbě

Hlavní úspěšný scénář:
1. Uživatel vytvoří rezervaci ve stavu `DRAFT`.
2. Systém ověří, že pro daný `Resource` v daném intervalu neexistuje jiná `CONFIRMED` rezervace.
3. Uživatel zaplatí za rezervaci a platba je úspěšná.
4. Systém přepne stav rezervace na `CONFIRMED`.
5. Rezervace je zpřístupněna pro další operace, například zrušení nebo upozornění.

Alternativní / chybové výsledky:
- Chyba: rezervace již byla potvrzena.
- Chyba: rezervace je ve stavu `CANCELLED`.
- Chyba: platba nebyla úspěšně provedena.
- Chyba: v daném intervalu existuje jiná potvrzená rezervace pro stejný `Resource`.
- Chyba: rezervace neexistuje.

Příklady ověření:
- `DRAFT` rezervace na 10:00–11:00 pro `Resource` A bez konfliktu a s úspěšnou platbou => úspěch.
- Potvrzení `CANCELLED` rezervace => chyba.
- Pokus o potvrzení bez úspěšné platby => chyba.

Zdůvodnění / zdroj:
- Tato operace odpovídá modelu, v němž žádost není ještě rezervací v plném smyslu a stává se aktivní až po úspěšném zaplacení, které je rozhodujícím momentem pro potvrzení alokace `Resource`.

Předpoklad / neznámá / TBD:
- TBD: jak přesně bude v systému reprezentována platba (samostatná entita, payment status, webhook nebo sync zprostředkovatele); v baseline stačí, že `Confirm Reservation` je podmíněn úspěšnou platbou.

---

## OP-04 — Cancel Reservation

Cíl / hodnota pro uživatele:
- Uživatel nebo správce může zrušit existující rezervaci tak, aby byla zaznamenána jako zrušená, ale ne odstraněna z historie systému. Pokud rezervace zůstane v `DRAFT` a nebude do jednoho dne po vytvoření zaplacena, systém ji automaticky převede do stavu `CANCELLED`.

Spouštěcí událost:
- Uživatel nebo správce vyvolá zrušení rezervace v případě, že již neplatí, nebo je nutné uvolnit `Resource`.
- Automatický systémový proces vyhodnotí `DRAFT` rezervaci jeden den po vytvoření a pokud nebyla zaplacena, přesune ji do `CANCELLED`.

Pozorovatelný požadavek / požadavky:
- Systém musí převést rezervaci do stavu `CANCELLED` a zachovat původní data pro audit a historické záznamy.
- Operace nesmí fyzicky smazat rezervaci.
- Pokud je `Reservation` ve stavu `DRAFT` a není zaplacena do jednoho dne po vytvoření, přechází automaticky do `CANCELLED`.

Předpoklady:
- `Reservation` existuje.
- `Reservation` je v stavu, který lze zrušit (`DRAFT` nebo `CONFIRMED` v základním modelu).
- Systém podporuje logickou změnu stavu místo smazání dat.
- Pro `DRAFT` rezervaci je známo, zda byla úspěšně zaplacena.

Stav po úspěšném provedení:
- `Reservation` má stav `CANCELLED`.
- `Resource` se může nabídnout k nové rezervaci v daném intervalu po zrušení.

Změna stavu:
- `DRAFT` → `CANCELLED` nebo `CONFIRMED` → `CANCELLED`
- zvláštní případ: `DRAFT` bez úspěšné platby do jednoho dne po vytvoření → `CANCELLED`

Hlavní úspěšný scénář:
1. Uživatel nebo správce vybere rezervaci k zrušení.
2. Systém ověří, že rezervace existuje a je v běžném stavu pro zrušení.
3. Systém přepne stav na `CANCELLED`.
4. Záznam zůstává v systému pro audit, ale již se nepovažuje za aktivní rezervaci.

Automatický scénář pro nezaplacenou `DRAFT` rezervaci:
1. Systém jeden den po vytvoření zkontroluje všechny `DRAFT` rezervace.
2. Pokud neexistuje úspěšná platba pro rezervaci, systém ji převede do `CANCELLED`.
3. `Resource` se uvolní pro další rezervaci.
4. Záznam zůstává zachován jako historický auditní záznam.

Alternativní / chybové výsledky:
- Chyba: rezervace neexistuje.
- Chyba: rezervace je již ve stavu `CANCELLED`.
- Chyba: pokus o zrušení v nepovoleném kontextu (pokud by systém v budoucnu rozlišoval další stavy).
- Informace: `DRAFT` rezervace bez úspěšné platby byla jeden den po vytvoření automaticky zrušena.

Příklady ověření:
- `CONFIRMED` rezervace 12:00–13:00 => zrušení => stav `CANCELLED`.
- `DRAFT` rezervace před potvrzením => zrušení => stav `CANCELLED`.
- `DRAFT` rezervace bez úspěšné platby jeden den po vytvoření => automatický přechod do `CANCELLED`.
- Již zrušená rezervace => chyba nebo idempotentní výsledek v závislosti na implementaci.

Zdůvodnění / zdroj:
- Tato operace odpovídá požadavku, aby zrušení nebylo fyzickým odstraněním dat, ale logickou změnou stavu, jak je běžné v rezervních systémech. V tomto baseline je důležité, že nezaplacená `DRAFT` rezervace nemůže zůstat otevřená déle než jeden den po vytvoření a musí být automaticky zrušena.

