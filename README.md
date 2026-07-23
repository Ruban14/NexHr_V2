# NexHr_V2 — Authentication

Authentication-only stack for **NexHr** (brand mark **N**, tagline **Enterprise HR Platform**). No org multi-tenancy, IAM, people, or invitations.

## Stack

| Layer | Tech |
|-------|------|
| Backend | Django 4.2 + DRF + SimpleJWT + Argon2 |
| Frontend | Angular 19 standalone + Angular Material + signals |
| Database | PostgreSQL (`NexHr_V2` / user `NexHRMS`) |

## Quick start

### 1. Database

PostgreSQL must be running with:

- Database: `NexHr_V2`
- User / password: `NexHRMS` / `NexHRMS`

### 2. Backend

```bash
cd Backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit SECRET_KEY / email as needed
python manage.py migrate
python manage.py runserver
```

API base: `http://localhost:8000/api`  
Auth mount: `http://localhost:8000/api/auth/`

In development, emails print to the console (`EMAIL_BACKEND=console`).

### 3. Frontend

```bash
cd Frontend
npm install
npm start
```

App: `http://localhost:4200` → redirects to `/auth/login`

## Environment variables (Backend)

| Variable | Purpose | Default |
|----------|---------|---------|
| `SECRET_KEY` | Django secret | insecure placeholder |
| `DEBUG` | Debug mode | `True` |
| `FRONTEND_URL` | Links in verify/reset emails | `http://localhost:4200` |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` | Postgres | `NexHr_V2` / `NexHRMS` / `NexHRMS` / `localhost` / `5432` |
| `CORS_ALLOWED_ORIGINS` | Allowed frontends | `http://localhost:4200,...` |
| `EMAIL_BACKEND` | Mail transport | console backend |
| `DEFAULT_FROM_EMAIL` | From address | `noreply@nexhr.local` |
| `AUTH_MAX_LOGIN_ATTEMPTS` | Failures before throttle/lock | `5` |
| `AUTH_LOCKOUT_WINDOW_MINUTES` | Attempt window | `15` |
| `AUTH_LOCKOUT_DURATION_MINUTES` | Account lock duration | `15` |
| `AUTH_ACCOUNT_LOCK_MIN_IPS` | Distinct IPs to lock account | `2` |

Frontend API base is configured in `Frontend/src/app/core/config/api.config.ts` (`http://localhost:8000/api`).

## Auth routes (UI)

| Route | Purpose |
|-------|---------|
| `/auth/login` | Sign in |
| `/auth/register` | Sign up (no auto-login) |
| `/auth/forgot-password` | Request reset email |
| `/auth/reset-password?token=` | Set new password |
| `/auth/verify-email?token=` | Verify email |
| `/app` | Authenticated home stub (name + logout) |

## Auth API (`/api/auth/`)

Envelope: `{ "success", "message", "data", "errors" }`

| Method | Path | Notes |
|--------|------|-------|
| POST | `/register` | Creates unverified user; sends verify email; **no tokens** |
| POST | `/login` | Returns `{ user, tokens }` only if verified |
| POST | `/logout` | Bearer + `{ refresh }` — kills session |
| POST | `/refresh` | Rotates refresh; returns new access+refresh |
| POST | `/forgot-password` | Always generic success |
| POST | `/reset-password` | `{ token, password }` — invalidates sessions |
| POST | `/verify-email` | `{ token }` |
| POST | `/resend-verification` | `{ email }` |
| GET | `/me` | Bearer — user profile |

## Security highlights

- Password min length **9** + Django validators; **Argon2** hasher
- Email verification required before login
- Verify/reset tokens stored as SHA-256 hashes (constant-time compare)
- JWT access ~15m, refresh ~8h; rotate + blacklist
- Access JWT requires active session claim `sid`
- Dual lockout (same email+IP throttle; multi-IP account lock)
- Auth throttles: anon ~20/min, user ~60/min

## Tests

```bash
cd Backend && source venv/bin/activate
python manage.py test apps.authentication
```

## Admin

Custom user uses **email** as username. Example staff user (after migrate):

```bash
DJANGO_SUPERUSER_PASSWORD='NexHRMS' python manage.py createsuperuser --email NexHRMS@nexhr.com
```

Then set `is_staff` / `is_superuser` / `is_email_verified` as needed (or use Django shell).
