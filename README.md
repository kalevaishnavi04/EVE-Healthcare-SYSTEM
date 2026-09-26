# EVE Healthcare — Diagnostic Booking & Payments API

A backend service for browsing diagnostic centres/tests, booking a test, and
paying for it through a **simulated** payment flow (mock payment endpoint +
idempotent webhook). Built with Django + Django REST Framework.

## Tech stack

- Python 3.11, Django 5, Django REST Framework
- JWT auth via `djangorestframework-simplejwt`
- PostgreSQL in Docker (SQLite by default for zero-setup local runs)
- `drf-spectacular` for OpenAPI/Swagger docs (bonus)
- Django's built-in test runner (`APITestCase`) for tests

## Project layout

```
config/            Django project settings, root urls, wsgi/asgi
apps/
  users/           signup, login (JWT), /me
  centres/         DiagnosticCentre & DiagnosticTest CRUD (read: public, write: admin)
  bookings/        Booking create/list/retrieve/cancel, scoped to the logged-in user
  payments/        Simulated payment endpoint + idempotent webhook
templates/
  index.html       A small vanilla-JS frontend (signup/login, browse & book, pay, cancel)
```

### About the frontend

The assignment itself only asked for a backend, so this is a lightweight
extra: `templates/index.html` is a single self-contained page (no build
step, no npm, no framework) served by Django itself at `/`. It talks to the
same API documented below using plain `fetch()` calls with the JWT it gets
back from signup/login. It's there so you (or an interviewer) can click
through signup → browse tests → book → pay → cancel without needing
Postman/curl, not as a production-grade UI.

---

## Running locally (no Docker)

```bash
python -m venv venv
source venv/bin/activate          # venv\Scripts\activate on Windows
pip install -r requirements.txt

cp .env.example .env              # defaults to SQLite, nothing else required

python manage.py migrate
python manage.py createsuperuser  # optional, needed to create centres/tests via the API
python manage.py seed_data        # optional: creates 3 sample centres with tests
python manage.py runserver
```

Frontend (browse/book/pay UI): `http://127.0.0.1:8000/`
API root: `http://127.0.0.1:8000/api/`
Swagger UI: `http://127.0.0.1:8000/api/docs/`
Django admin: `http://127.0.0.1:8000/admin/`

Run the tests:

```bash
python manage.py test
```

## Running with Docker (PostgreSQL)

```bash
docker-compose up --build
```

This starts Postgres and the web app, runs migrations automatically, and
serves the API at `http://localhost:8000/api/`. Then, in another terminal:

```bash
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py seed_data
docker-compose exec web python manage.py test
```

---

## API reference

All authenticated endpoints expect `Authorization: Bearer <access_token>`.

### Auth — `apps/users`

| Method | Endpoint                  | Auth | Description                          |
|--------|----------------------------|------|--------------------------------------|
| POST   | `/api/auth/signup/`        | No   | Create account, returns JWT tokens   |
| POST   | `/api/auth/login/`         | No   | Obtain JWT access + refresh tokens   |
| POST   | `/api/auth/token/refresh/` | No   | Exchange refresh token for new access|
| GET    | `/api/auth/me/`            | Yes  | Current user's profile               |

**Signup**
```bash
curl -X POST http://localhost:8000/api/auth/signup/ \
  -H "Content-Type: application/json" \
  -d '{"username":"jane","email":"jane@example.com","password":"StrongPass123!"}'
```
```json
{
  "user": {"id": 1, "username": "jane", "email": "jane@example.com", "first_name": "", "last_name": ""},
  "access": "<jwt>",
  "refresh": "<jwt>"
}
```

**Login**
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"jane","password":"StrongPass123!"}'
```

### Centres & tests — `apps/centres`

| Method | Endpoint                        | Auth        | Description                       |
|--------|----------------------------------|-------------|------------------------------------|
| GET    | `/api/centres/`                  | No          | List centres (with nested tests)   |
| GET    | `/api/centres/{id}/`             | No          | Retrieve one centre                |
| POST   | `/api/centres/`                  | Admin/staff | Create a centre                    |
| PUT/PATCH/DELETE | `/api/centres/{id}/`  | Admin/staff | Update/delete a centre             |
| GET    | `/api/tests/`                    | No          | List tests (`?centre=<id>` filter) |
| GET    | `/api/tests/{id}/`               | No          | Retrieve one test                  |
| POST   | `/api/tests/`                    | Admin/staff | Create a test                      |

```bash
curl http://localhost:8000/api/centres/
curl "http://localhost:8000/api/tests/?centre=1"
```

### Bookings — `apps/bookings`

| Method | Endpoint                       | Auth | Description                                    |
|--------|----------------------------------|------|-------------------------------------------------|
| POST   | `/api/bookings/`                 | Yes  | Book a test (creates a `PENDING` booking)        |
| GET    | `/api/bookings/`                 | Yes  | List the current user's bookings                 |
| GET    | `/api/bookings/{id}/`            | Yes  | Retrieve one of the current user's bookings      |
| POST   | `/api/bookings/{id}/cancel/`     | Yes  | Cancel a `PENDING`/`CONFIRMED` booking            |

```bash
curl -X POST http://localhost:8000/api/bookings/ \
  -H "Authorization: Bearer <access>" -H "Content-Type: application/json" \
  -d '{"diagnostic_test": 1, "appointment_datetime": "2026-10-05T10:00:00Z"}'
```
`amount` and `centre` are derived from the chosen test — they are **not**
accepted from the client, so a user can't book at one price and pay another.

### Payments — `apps/payments`

| Method | Endpoint                    | Auth | Description                                     |
|--------|-------------------------------|------|--------------------------------------------------|
| POST   | `/api/payments/`              | Yes  | Simulate paying for a booking                     |
| POST   | `/api/payments/webhook/`      | No*  | Simulated provider webhook (idempotent)           |

\* In production this would be locked down with a shared secret / HMAC
signature check rather than left open — see "What I'd improve".

**Simulate a payment**
```bash
curl -X POST http://localhost:8000/api/payments/ \
  -H "Authorization: Bearer <access>" -H "Content-Type: application/json" \
  -d '{"booking_id": "<booking-uuid>"}'
```
Randomly resolves to `SUCCESS` (booking → `CONFIRMED`) or `FAILED` (booking →
`FAILED`).

**Webhook (idempotent)**
```bash
curl -X POST http://localhost:8000/api/payments/webhook/ \
  -H "Content-Type: application/json" \
  -d '{"event_id":"evt-1","booking_id":"<booking-uuid>","status":"SUCCESS","transaction_id":"TXN-1"}'
```
Sending the exact same body again returns `200 {"duplicate": true}` and makes
**no** further changes — no duplicate `Payment` row, no re-firing of side
effects, and the booking is not moved out of a terminal state it already
reached (see `apps/payments/views.py` docstring for the four safeguards).

---

## Database / schema design

```
User (Django auth) 1───* Booking *───1 DiagnosticTest *───1 DiagnosticCentre
                         │
                         1
                         │
                         *
                      Payment
WebhookEvent (standalone log, referenced by event_id only)
```

- **DiagnosticCentre** — name, location, address, is_active.
- **DiagnosticTest** — belongs to a centre, name, price, is_active.
  `unique_together(centre, name)` stops the same test being duplicated at a
  centre.
- **Booking** — UUID primary key (bookings are shared with an external
  "payment provider" and shouldn't be sequential/guessable ints); snapshots
  `amount` from the test's price *at booking time* so later price changes
  never retroactively change an existing booking; `status` is one of
  `PENDING/CONFIRMED/FAILED/CANCELLED`.
- **Payment** — one row per attempted payment (a booking can have several,
  e.g. FAILED then a later successful retry); `transaction_id` is unique,
  which is one of the idempotency guards.
- **WebhookEvent** — logs every webhook delivery keyed by the provider's
  `event_id` (unique) with a `processed` flag; this is the primary
  idempotency guard for the webhook endpoint.

## Assumptions

- Django's built-in `User` model is used as-is (username + email + password)
  rather than a custom user model, to keep the auth surface small for a
  3–4 hour assignment.
- A booking can only be created for a currently-active test, and only for a
  future `appointment_datetime`.
- `amount` and `centre` are always derived server-side from the chosen test,
  never trusted from the client.
- Only the booking's owner can view, cancel, or pay for it; centre/test
  management (`POST`/`PUT`/`DELETE`) is restricted to Django staff users.
- A booking already `CONFIRMED` or `CANCELLED` is treated as terminal enough
  that neither `/payments/` nor `/payments/webhook/` will touch it again —
  this is a deliberate simplification (see below).
- The simulated payment gateway resolves randomly (50/50) purely to exercise
  both code paths; a real integration would call out to an actual provider.
- Webhook authentication (HMAC signature / shared secret) was left out since
  there's no real provider to sign requests — flagged explicitly as a gap
  below rather than silently skipped.

## Edge cases handled

- Duplicate signup email, weak password → `400`.
- Wrong login credentials → `401`.
- Booking a past datetime, or an inactive test → `400`.
- Fetching/cancelling/paying for another user's booking → `404` (not `403`,
  so existence of the booking isn't leaked to non-owners).
- Unknown booking id (valid UUID, no row) → `404`.
- Paying for an already-`CONFIRMED` or `CANCELLED` booking → `400`.
- Cancelling an already-`CANCELLED`/`FAILED` booking, or a past appointment
  → `400`.
- Webhook replay (same `event_id` sent 1, 2, or N times) → processed exactly
  once; every replay after the first returns `200 {"duplicate": true}` with
  no state change.
- Webhook for an unknown booking id → `404`, event still marked processed
  (so the provider doesn't retry forever).
- Webhook arriving after the booking is already `CONFIRMED`/`CANCELLED` →
  ignored (`200`, booking untouched) instead of overwriting a later/valid
  state.
- Anonymous requests to any authenticated endpoint → `401`.
- Basic rate limiting on `/auth/*`, `/payments/`, and `/payments/webhook/`.

## Bonus items implemented

- Swagger/OpenAPI docs via `drf-spectacular` (`/api/docs/`).
- Structured logging around payment/webhook processing
  (`apps/payments/views.py`).
- Pagination (`PAGE_SIZE = 20`) on all list endpoints.
- Rate limiting (`ScopedRateThrottle`) on auth, payments, and the webhook.
- Docker + docker-compose (Postgres).
- Unit/integration tests for every app, focused especially on the webhook's
  idempotency and on cross-user access control.
- `seed_data` management command for quick manual testing.

Not implemented (see "What I'd improve"): Redis caching, Celery/background
retry handling for webhook processing.

## What I'd improve with more time

- **Webhook authentication.** Verify an HMAC signature (or shared secret
  header) from the "provider" instead of accepting any `POST` — right now
  anyone could call the webhook directly.
- **Async payment processing.** Move the simulated gateway call in
  `/payments/` onto a Celery task so the request returns immediately with a
  `PENDING` payment, and the real status arrives only via the webhook —
  closer to how real gateways behave, and avoids a slow synchronous request.
- **Retry/backoff for webhook side effects** (e.g. sending a confirmation
  email) using Celery, with the DB write staying synchronous/idempotent as
  it is now.
- **Redis caching** for the centre/test listing endpoints, which are public
  and read-heavy.
- **Custom user model** with a phone number and role (patient/admin) instead
  of overloading `is_staff` for centre management.
- **Soft-delete / audit trail** for bookings (who cancelled it, when) rather
  than just the current `status` field.
- **A `PATCH /api/bookings/{id}/reschedule/` endpoint**, since right now the
  only way to change an appointment time is to cancel and rebook.
- More exhaustive concurrency tests (e.g. firing two webhook deliveries for
  the same event truly in parallel with threads, not just sequentially).
