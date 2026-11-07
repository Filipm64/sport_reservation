# OP-04 — Cancel Reservation

**Cíl / hodnota pro uživatele:** Vlastník může před začátkem zrušit svou
žádost nebo rezervaci.

**Spouštěcí událost:** Vlastník odešle požadavek na zrušení.

**Pozorovatelný požadavek:** Rezervace ve stavu
`PENDING_APPROVAL` nebo `CONFIRMED` se před začátkem změní na
`CANCELLED`; záznam zůstává.

**Předpoklady:** Rezervace existuje, patří uživateli, má stav
`PENDING_APPROVAL` nebo `CONFIRMED` a ještě nezačala. Čekající žádost lze
zrušit po celou dobu před začátkem, i když od jejího podání uplynulo více než 24 hodin.

**Stav po úspěšném provedení:** Záznam `CANCELLED`; již neblokuje Resource.

**Změna stavu:** `PENDING_APPROVAL | CONFIRMED → CANCELLED`.

**Odkaz na pravidla:** BR-02, BR-05, BR-06, BR-07.

**Hlavní úspěšný scénář:**
1. Vlastník požádá o zrušení.
2. Systém ověří vlastníka, stav a čas.
3. Systém nastaví `CANCELLED` bez smazání záznamu.

**Alternativní / chybové výsledky:** Cizí/neexistující rezervace,
nepovolený stav nebo začátek již nastal → odmítnuto.
Vypršelá čekající žádost → `EXPIRED` a odmítnuto (BR-07).
Souběh s Approve odpovídá BR-06.

**Příklady ověření:** Čekající žádost před začátkem → `CANCELLED` a
zůstává uložená; rezervace přesně na hranici začátku → odmítnuto.

**Zdůvodnění / zdroj:** Rušení je změna stavu. U čekající žádosti je třeba
umožnit vlastníkovi stáhnout požadavek.

## Související podklady

- [Vazby REQ-05: pravidla, návrh, implementace a testy](../verification/coverage.md#req-05)
- [Přehled požadavků](README.md)
- [Původní specifikace baseline v0.2](../history/baseline-v0.2.md)
