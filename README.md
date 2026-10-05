## CP1 walking skeleton

POST /api/reservations/
→ validace
→ persist
→ return reservation ID
→ automated check

## Reservation demo (baseline v0.2)

Specification: [docs/baseline-v0.2.md](docs/baseline-v0.2.md).

Run the local Django application from `sport_booking/`:

```sh
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Create a Sport and Resource in `/admin/`. Set **Requires approval** on
Resources that need a staff decision. The JSON API uses the logged-in user:

- `POST /api/reservations/` — body: `resource_id`, `starts_at`, `ends_at`
  (ISO 8601 datetimes with timezone).
- `GET /api/availability/?resource_id=...&starts_at=...&ends_at=...`
- `POST /api/reservations/<id>/confirm/`
- `POST /api/reservations/<id>/approve/` — staff only; body:
  `{"decision":"approve"}` or `{"decision":"reject"}`.
- `POST /api/reservations/<id>/cancel/`

Run the automated examples for successful and rejected outcomes:

```sh
python manage.py test reservations
```

Pending approval requests expire after 24 hours or when their reservation
starts, whichever comes first. Run `python manage.py expire_reservations`
periodically to update expired records; scheduling that command is left for
the next architecture iteration.