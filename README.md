# Rezervační systém sportovišť — C02/C03

Django aplikace pro vytvoření žádosti, kontrolu dostupnosti, potvrzení,
zrušení a schvalování vybraných sportovišť.

## Dokumentace

- [Rozcestník dokumentace](docs/README.md)
- [Požadavky a business pravidla](docs/requirements/README.md)
- [Vazby požadavků na návrh, implementaci a testy](docs/verification/coverage.md)
- [Architektura](docs/architecture/README.md) a [detailní návrh](docs/design/README.md)
- [Ověřování a evidence](docs/verification/README.md)
- [Historie, baseline a školní etapy](docs/history/README.md)
- [Zadání cvičení](assigments/README.md)

## Spuštění z kořene projektu

Použijte Python kompatibilní s Django z `requirements.txt`; při revizi
ověřeno na Python 3.14.6 a Django 6.1.1.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python sport_booking/manage.py migrate
.venv/bin/python sport_booking/manage.py createsuperuser
.venv/bin/python sport_booking/manage.py runserver
```

V `/admin/` vytvořte Sport a Resource. Příznak `Requires approval` určuje,
zda potvrzení musí posoudit správce. Rezervace v adminu slouží pouze
k prohlížení; jejich změny procházejí API.

## Webové rozhraní

Po spuštění serveru otevřete `http://127.0.0.1:8000/`. Veřejný katalog
zobrazuje dostupná sportoviště; zákazník si může vytvořit účet přes
**Vytvořit účet**, přihlásit se, ověřit dostupnost a spravovat své rezervace.
Správci se přihlašují svým Django účtem s `is_staff`; na úvodní stránce
vyřizují čekající žádosti. Veřejná registrace vytváří pouze běžné účty.

Čas lze vybrat také v [týdenním hodinovém rozvrhu](docs/requirements/hourly-schedule.md): jeden nebo dva navazující bloky, maximálně 2 hodiny. Přepínač zachovává i ruční zadání přesného času. Obsazenost se znovu ověřuje při odeslání.

Katalog Sport/Resource se nadále spravuje v `/admin/`. Web i API používají
stejné rezervační služby a pravidla. Uživatelské rozhraní nepřidává
notifikace ani automatické spouštění expirace. Časy ve formuláři se
zobrazují v časovém pásmu `Europe/Prague`; API nadále vyžaduje ISO 8601
datum a čas s pásmem.

## API a předvedení

API používá přihlášeného Django uživatele a CSRF ochranu. Všechny datové
vstupy používají časové údaje ISO 8601 s pásmem.

| Operace | HTTP rozhraní |
| --- | --- |
| Create | `POST /api/reservations/` — JSON `resource_id`, `starts_at`, `ends_at` |
| Availability | `GET /api/availability/?resource_id=...&starts_at=...&ends_at=...` |
| Approve | `POST /api/reservations/<id>/approve/` — správce; JSON `{"decision":"approve"}` nebo `{"decision":"reject"}` |
| Cancel | `POST /api/reservations/<id>/cancel/` |

Pro ruční ukázku se přihlaste do adminu, v konzoli prohlížeče na stejné
stránce spusťte například následující kód (nahraďte `resource_id`):

```js
const csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;
const post = async (path, body = {}) => {
  const response = await fetch(path, {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrf},
    body: JSON.stringify(body),
  });
  return {http: response.status, body: await response.json()};
};
const start = new Date(Date.now() + 86400000);
const input = {
  resource_id: 1,
  starts_at: start.toISOString(),
  ends_at: new Date(start.getTime() + 3600000).toISOString(),
};
const created = await post('/api/reservations/', input);
console.log(created);
console.log(await fetch('/api/availability/?' + new URLSearchParams(input)).then(r => r.json()));
const id = created.body.id;
// Pro Resource vyžadující schválení, jako přihlášený správce:
// console.log(await post(`/api/reservations/${id}/approve/`, {decision: 'approve'}));
console.log(await post(`/api/reservations/${id}/cancel/`));
console.log(await post(`/api/reservations/${id}/cancel/`)); // opakování → 409
```

Create vrací rovnou `CONFIRMED`, nebo `PENDING_APPROVAL` podle sportoviště. Potvrzení automaticky zamítne překrývající se čekající žádosti stejného sportoviště. Samostatný krok Confirm byl odstraněn.

Po aktualizaci projektu spusťte migrace:

```sh
.venv/bin/python sport_booking/manage.py migrate
```

Migrace `0003` zachová staré záznamy `DRAFT` jako `CANCELLED`; nevytváří z nich automaticky potvrzené rezervace ani žádosti.

## Reprodukovatelné ověření

```sh
.venv/bin/python sport_booking/manage.py test reservations
.venv/bin/python sport_booking/manage.py check
.venv/bin/python sport_booking/manage.py makemigrations --check --dry-run
```

Výchozí paměťová SQLite přeskočí pět testů souběhu. Pro **úplné ověření**
použijte vyhrazený dočasný soubor testovací DB (test runner ho vytváří
a odstraňuje; nepoužívejte cestu k aplikační databázi):

```sh
SPORT_BOOKING_TEST_DB=/tmp/sport-booking-c02-tests.sqlite3 .venv/bin/python sport_booking/manage.py test reservations
```

Ověření před C09: **101 testů, všechny prošly**, včetně souběhu, rollbacku a migrace starých DRAFT. [Výsledek a vazby na konkrétní testy](docs/verification/weekly-operating-hours.md).
Čtyři testy souběhu používají nezávislá spojení; pátý ověřuje expiraci v samostatném procesu.

## Automatické ověření a GitHub CI

[Workflow CI](.github/workflows/ci.yml) se spouští při každém pushi do `main`,
při otevření, aktualizaci nebo znovuotevření pull requestu do libovolné větve
a ručně přes záložku **Actions → CI → Run workflow**.
Používá Ubuntu 24.04 a Python 3.14, nainstaluje `requirements.txt` a spustí
stejný [ověřovací skript](scripts/check.py), který lze použít lokálně:

```sh
.venv/bin/python scripts/check.py
```

Skript kontroluje konzistenci závislostí (`pip check`), Django konfiguraci,
chybějící migrace, dokumentaci a celý balík `reservations`. Pro každý běh
vytvoří vlastní dočasnou souborovou SQLite DB, takže proběhnou i testy
souběhu. Existující `SPORT_BOOKING_TEST_DB` nepřebírá. Při selhání kterékoliv
kontroly skončí nenulovým exit kódem; ostatní kontroly ještě zaznamená.
Závislosti musí být před lokálním spuštěním nainstalované podle úvodu README.

Log `.ci-output/check.log` obsahuje commit, stav pracovního stromu, prostředí,
verze nainstalovaných balíčků, příkazy a exit kódy. Při dalším lokálním běhu
se přepíše; vlastní cestu lze zadat pomocí `--log /tmp/sport-booking-check.log`.
Na GitHubu se log nahraje jako artefakt `verification-<run_id>-<run_attempt>`
s uchováním 30 dní, i při selhání ověřovacího skriptu. Pokud selže instalace
závislostí ještě před spuštěním skriptu, je příčina v logu kroku na GitHubu.
CI nepotřebuje vlastní secrets ani zápisová oprávnění k repozitáři.

Konfigurace je připravená; výsledek skutečného běhu na GitHubu se doloží
až po commitnutí a pushnutí změn. CI samo nenastavuje zákaz merge při
neúspěchu — případné povinné kontroly se nastavují v pravidlech větve.
Syntaxe spouštění odpovídá [dokumentaci GitHub Actions](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax).

## Expirace a C03

```sh
.venv/bin/python sport_booking/manage.py expire_reservations
```

Čekající žádost vyprší při začátku rezervace. Do té doby ji může vlastník
zrušit a správce schválit nebo zamítnout; pevný 24hodinový limit neplatí. Approve i Cancel deadline ověřují samy; příkaz
aktualizuje i nevyřízené záznamy. Plánované spouštění zůstává driverem C03.
SQLite nyní chrání souběžné změny režimem IMMEDIATE; budoucí architektura
musí zachovat stejný business výsledek.

## C01 / zamýšlený walking skeleton pro CP1

`POST /api/reservations/ → validace → persist → ID → automated check`.
C01 rámec a spike se znovu nevytvářejí; C03 doplní obhajitelnou architekturu.

## Realizace C03

HTTP vstupy jsou v `reservations/api.py`; společné rozhodování vlastní
`ReservationService` v `services.py`. `rules.py` a `domain.py` obsahují
časová pravidla a doménové objekty, `identity.py` oprávnění a `persistence.py`
rozhraní ukládání s Django adaptérem. `wiring.py` propojuje tyto části.
Expirační command volá stejnou službu. Aktuální změna odstraňuje DRAFT a endpoint Confirm;
[popis změny a migrace](docs/verification/reservation-lifecycle.md). Evidence C03 zachovává historické ověření.

## Provozní doba sportovišť

Správce ji nastaví na úvodní stránce v části **Nastavit provozní dobu sportovišť**, případně v administraci. Jedna denní doba platí každý den. Celá rezervace musí být uvnitř této doby, včetně ručního zadání a API; při schválení se kontroluje znovu. Viz [REQ-13](docs/requirements/operating-hours.md).

## C09 — storno lhůta uložená k rezervaci

Provozovatel nastavuje **Storno lhůtu (minuty)** v `/admin/` u sportoviště;
potřebuje staff účet a oprávnění ke změně Resource. Výchozí hodnota je
120 minut, 0 znamená zrušení kdykoliv před začátkem. Nová rezervace si
při vytvoření uloží aktuální lhůtu. Pozdější změna nastavení ani schválení
žádosti ji nemění. Čekající žádost lze stáhnout kdykoliv před začátkem.
Potvrzenou rezervaci lze zrušit přesně na storno hranici včetně, ale vždy
jen před začátkem. Rozhoduje čas serveru, web zobrazuje Europe/Prague.

Při aktualizaci zastavte server i další zapisující procesy a vytvořte
konzistentní zálohu SQLite DB. Potom spusťte:

```sh
.venv/bin/python sport_booking/manage.py migrate
```

Migrace `0004_cancellation_notice` zachová ID, stavy, vztahy a časy starých
rezervací a přiřadí jim lhůtu 0 minut. Sportoviště dostanou výchozích
120 minut. Před obnovením provozu ověřte tyto hodnoty a nové vytvoření.
Stará a nová verze aplikace nesmějí současně zapisovat. Migrace je připravená;
při implementačním ověření byla aplikována pouze na oddělenou testovací DB.

Návrat ke starému kódu po vytvoření rezervací s kladnou lhůtou by znovu
povolil pozdní storno. Obrácení migrace odstraní uložené lhůty; bezpečná
obnova musí tyto podmínky zachovat. Automatický rollback není ověřený.
Přímé SQL a vlastní ORM zápisy mimo službu nehlídají časové storno pravidlo;
Reservation nemá implicitní výchozí lhůtu pro nové přímé ORM zápisy.

[Záznam implementace C09 a její ověření](docs/verification/c09-release-record.md).
