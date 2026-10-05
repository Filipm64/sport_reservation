# Architektonické drivery pro C03

Zpřesnění pěti driverů z C02 vychází z [baseline v0.2](baseline-v0.2.md)
a [revize požadavků](requirements-review.md). ID AD-01 až AD-05 zůstávají
zachována. Každý driver popisuje tlak na architekturu a otázku k rozhodnutí;
konkrétní mechanismus se zvolí až při návrhu architektury.

| Podklad / zdroj | Proč ovlivňuje architekturu | Otázka, kterou musí architektura vyřešit |
| :--- | :--- | :--- |
| **AD-01 — Exkluzivita při souběhu.** `BR-02`, `BR-06`, `REQ-04`; scénáře souběhu Confirm/Confirm, Approve/Approve a Confirm/Approve z evidence C02. | Dva požadavky na různé rezervace stejného sportoviště mohou oba vidět „bez konfliktu“. Samostatná kontrola dostupnosti nezaručuje, že při následném potvrzení bude čas stále volný. Pokud každý rozhoduje nezávisle, mohou vzniknout dvě kolidující `CONFIRMED`. | Kde se provede autoritativní rozhodnutí o alokaci sportoviště a jaká je jeho hranice vůči ostatním potvrzením a schválením, aby ve všech uložených stavech platilo `BR-02` a při konfliktu uspěla nejvýše jedna alokace? |
| **AD-02 — Konzistentní přechody jedné rezervace.** `BR-05`, `BR-06`, `BR-07`, `REQ-05`, `REQ-06`; scénáře souběhu se zrušením z evidence C02. | Confirm, Approve, Cancel a expirace mohou pracovat se stejnou rezervací současně. Výsledek závisí na pořadí: zrušenou či vypršelou žádost již nelze schválit; úspěšné schválení naopak může před začátkem následovat platné zrušení. Rozdílné rozhodování jednotlivých vstupů může obnovit již ukončenou žádost. | Kdo vlastní pravidla povolených přechodů a jak se určí jejich závazné pořadí, aby všechny vstupy respektovaly aktuální stav a souběžné operace měly výsledek odpovídající povolenému sériovému pořadí? |
| **AD-03 — Dlouhotrvající schvalování a expirace.** `BR-07`, `REQ-06`, `OP-03`, `OP-05`; změna C02 umožňuje opožděné rozhodnutí a vypršení. | `PENDING_APPROVAL` trvá déle než původní požadavek a musí přežít restart aplikace. Rozhodnutí může přijít později nebo vůbec. Platnost žádosti končí v dřívějším z okamžiků „24 hodin od podání“ a „začátek rezervace“, i když uživatel nepošle další požadavek. | Kdo vlastní čekající stav a čas žádosti, kdo provede pozdější schválení, zamítnutí či expiraci a jak se proces obnoví po výpadku, aby prošlá žádost nemohla být přijata a nevyřízené záznamy byly nakonec označeny `EXPIRED`? |
| **AD-04 — Oprávnění na všech vstupech.** `OP-01` až `OP-05`, `REQ-01`, `REQ-03`, `REQ-05`, `REQ-06`; nález C02: admin umožňoval obejít životní cyklus rezervace. | Vlastník může potvrdit a zrušit vlastní rezervaci, správce může rozhodovat o čekajících žádostech. Vedle API existuje administrační vstup. Pokud každý vstup používá jiné kontroly nebo dovolí přímou změnu stavu, lze obejít vlastnictví, pravomoc správce i doménová pravidla. | Kde se vyhodnotí identita, vlastnictví a oprávnění a které vstupy smějí měnit rezervaci, aby žádná cesta neumožnila nepovolenou změnu ani obejití jejích pravidel? |
| **AD-05 — Jednotný význam času a intervalů.** `BR-01`, `BR-03`, `BR-05`, `BR-07`; hraniční příklady v baseline a testech C02. | Dostupnost, potvrzení, schválení, rušení a expirace porovnávají intervaly nebo aktuální čas. Rozdílný výklad pásma či hranice může způsobit, že jeden vstup žádost ještě přijme a druhý ji už považuje za prošlou. Sousední intervaly se nesmějí mylně vyhodnotit jako kolize. | Kdo poskytuje rozhodný čas a kde se vyhodnocují společná časová pravidla, aby všechny operace používaly intervaly `[start, end)`, stejný skutečný okamžik a shodné rozhodnutí na hranici začátku i expirace? |

## Hranice tohoto zpřesnění

Nebyly přidány nové drivery. Samostatný výstup Části A není v dostupné
dokumentaci; uvedené nálezy a scénáře pocházejí z revize C02 a jsou doloženy
v [evidenci](evidence-and-evolution.md). Notifikační služba zatím nemá
specifikované události ani požadované chování při selhání, proto její
spolehlivost není přijatým driverem tohoto systému.

Očekávané zatížení, cílová latence a nejvyšší přípustné zpoždění zápisu
`EXPIRED` nejsou stanovené. Pokud budou pro návrh potřebné, tým je doplní
jako explicitní požadavky. Technologie současné ukázky a její technické
mechanismy jsou popsané v evidenci; nepředstavují odpověď na otázky driverů.
