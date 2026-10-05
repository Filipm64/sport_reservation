# Rezervační systém sportovišť — C02

Django aplikace pro vytvoření žádosti, kontrolu dostupnosti, potvrzení,
zrušení a schvalování vybraných sportovišť.

- [Baseline v0.1](docs/baseline-v0.1.md) a [v0.2](docs/baseline-v0.2.md)
- [Kontrola splnění zadání a zbývající týmové úkoly](docs/c02-audit.md)
- [Revize požadavků a vazby na testy](docs/requirements-review.md)
- [Architektonické drivery pro C03](docs/architecture-drivers.md)
- [Evidence běhu a změn](docs/evidence-and-evolution.md)

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

## API a předvedení

API používá přihlášeného Django uživatele a CSRF ochranu. Všechny datové
vstupy používají časové údaje ISO 8601 s pásmem.

| Operace | HTTP rozhraní |
| --- | --- |
| Create | `POST /api/reservations/` — JSON `resource_id`, `starts_at`, `ends_at` |
| Availability | `GET /api/availability/?resource_id=...&starts_at=...&ends_at=...` |
| Confirm | `POST /api/reservations/<id>/confirm/` |
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
console.log(await post(`/api/reservations/${id}/confirm/`));
// Pro Resource vyžadující schválení, jako přihlášený správce:
// console.log(await post(`/api/reservations/${id}/approve/`, {decision: 'approve'}));
console.log(await post(`/api/reservations/${id}/cancel/`));
console.log(await post(`/api/reservations/${id}/cancel/`)); // opakování → 409
```

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

Při revizi prošlo všech 30 testů včetně souběhu. Testy přes Django client
předvádějí úspěšný i negativní/hraniční příklad každé operace. Pět testů
souběhu používá nezávislá spojení nad souborovou databází.

## Expirace a C03

```sh
.venv/bin/python sport_booking/manage.py expire_reservations
```

Čekající žádost vyprší po 24 hodinách nebo při začátku rezervace, podle
toho, co nastane dříve. Approve i Cancel deadline ověřují samy; příkaz
aktualizuje i nevyřízené záznamy. Plánované spouštění zůstává driverem C03.
SQLite nyní chrání souběžné změny režimem IMMEDIATE; budoucí architektura
musí zachovat stejný business výsledek.

## C01 / zamýšlený walking skeleton pro CP1

`POST /api/reservations/ → validace → persist → ID → automated check`.
C01 rámec a spike se znovu nevytvářejí; C03 doplní obhajitelnou architekturu.
