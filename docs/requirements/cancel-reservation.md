# OP-04 — Cancel Reservation

**Cíl / hodnota pro uživatele:** Vlastník může před začátkem zrušit svou
žádost nebo rezervaci.

**Spouštěcí událost:** Vlastník odešle požadavek na zrušení.

**Pozorovatelný požadavek:** Rezervace ve stavu
`PENDING_APPROVAL` nebo `CONFIRMED` se před začátkem změní na
`CANCELLED`; záznam zůstává. U potvrzené rezervace navíc nesmí být překročena
uložená storno lhůta podle BR-05.

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
Pozdní storno potvrzené rezervace → HTTP 409 s vysvětlením lhůty,
stav i blokace termínu zůstávají zachované. Souběh s Approve odpovídá BR-06.

**Příklady ověření:** Čekající žádost před začátkem → `CANCELLED` a
zůstává uložená; rezervace přesně na hranici začátku → odmítnuto.

**Zdůvodnění / zdroj:** Rušení je změna stavu. U čekající žádosti je třeba
umožnit vlastníkovi stáhnout požadavek.

## Nastavení a zachování storno podmínek — C09

Provozovatel nastavuje `Resource.cancellation_notice_minutes` v administraci
sportoviště; potřebuje aktivní staff účet a oprávnění ke změně Resource.
Výchozí hodnota je 120 minut, přípustné jsou celé nezáporné minuty v rozsahu
použitého databázového pole. Zákazník si lhůtu nevolí. Při Create služba
v chráněné transakci zkopíruje aktuální hodnotu do
`Reservation.cancellation_notice_minutes`. Pozdější změna sportoviště,
schválení ani zrušení uloženou hodnotu nepřepisují. Admin rezervace ji
zobrazuje pouze pro čtení.

U CONFIRMED platí současně `now < starts_at` a
`now <= starts_at - uložená lhůta`. Přesně na storno hranici je zrušení
povolené, přesně při začátku už nikdy. Rozhoduje serverový čas, odečet
probíhá v UTC ve skutečných minutách; web zobrazuje Europe/Prague.
U PENDING_APPROVAL se storno lhůta neuplatňuje, stále platí expirace
při začátku. Vytvoření i schválení po storno hranici jsou možné, ale takto
potvrzenou rezervaci již vlastník zrušit nemůže.

Migrace `0004_cancellation_notice` zachová existujícím rezervacím původní
podmínky uložením 0 minut, sportovištím nastaví 120 minut. Nová rezervace
vytvořená při nastavení 0 se také smí zrušit kdykoliv před začátkem.

Zdroj: [CR-C08-01, přijatá připomínka z review](C08-change-request.md),
[implementace a evidence C09](../verification/c09-release-record.md).

## Související podklady

- [Vazby REQ-05: pravidla, návrh, implementace a testy](../verification/coverage.md#req-05)
- [Přehled požadavků](README.md)
- [Původní specifikace baseline v0.2](../history/baseline-v0.2.md)
