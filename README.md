# NexHr_V2 — Authentication + Organization Setup

Stack for **NexHr** (brand mark **N**, tagline **Enterprise HR Platform**).

## Stack

| Layer | Tech |
|-------|------|
| Backend | Django 4.2 + DRF + SimpleJWT + Argon2 |
| Frontend | React (Vite) + React Router |
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
Organization mount: `http://localhost:8000/api/organization/`

### 3. Frontend

```bash
cd Nexhr_v2_frontend
npm install
npm run dev
```

App: `http://localhost:5173` → `/auth/login`

## Auth + org flow

1. Register → verify email link
2. Sign in
3. If no organization membership → `/organizations/create`
4. Creates `UserProfile` (admin), `Organization`, and `OrganizationMembership`

## Environment variables (Backend)

| Variable | Purpose | Default |
|----------|---------|---------|
| `FRONTEND_URL` | Links in verify/reset emails | `http://localhost:5173` |
| `CORS_ALLOWED_ORIGINS` | Allowed frontends | `http://localhost:5173,...` |

Frontend API base defaults to `http://localhost:8000/api` (override with `VITE_API_BASE_URL`).
