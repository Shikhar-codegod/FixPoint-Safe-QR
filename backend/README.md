# FixPoint Drive – Safe-QR SOS · Backend

> Production-oriented Django REST Framework backend for the FixPoint Drive emergency assistance platform.

---

## Stack

| Layer | Technology |
|---|---|
| Language | Python 3.13 |
| Framework | Django 5.2 + Django REST Framework 3.18 |
| Auth | Simple JWT 5.5 |
| Database | PostgreSQL (production) / SQLite (dev fallback) |
| Task Queue | Celery 5.6 + Redis |
| Cache | Redis 8 |
| API Docs | drf-spectacular (Swagger + ReDoc) |
| Encryption | `cryptography` – AES-128/Fernet |
| Testing | pytest + pytest-django |

---

## Quick Start

```bash
# 1. Create and activate the virtual environment (already done)
python -m venv .venv --without-pip
pip install -r requirements.txt

# 2. Copy .env.example and configure
copy .env.example .env
# (edit .env with your PostgreSQL URL, Redis URL, secret key, etc.)

# 3. Run migrations
python manage.py migrate

# 4. Create a superuser
python manage.py createsuperuser

# 5. Start the development server
python manage.py runserver 0.0.0.0:8000

# 6. Run tests
python -m pytest tests/ -v
```

---

## API Routes (`/api/v1/`)

| Prefix | Namespace | Description |
|---|---|---|
| `health/` | `common` | Health check (public) |
| `auth/` | `accounts` | JWT login, register, user profile |
| `profiles/` | `profiles` | User & responder profiles |
| `qr/` | `qr_codes` | Safe-QR badge CRUD + public resolver |
| `contacts/` | `contacts` | Emergency contacts (AES encrypted) |
| `medical/` | `medical` | Medical profile (AES encrypted) |
| `alerts/` | `alerts` | Alert record foundation |
| `notifications/` | `notifications` | Notification records |
| `incidents/` | `incidents` | Incident lifecycle |
| `responders/` | `responders` | Responder dispatches |
| `operations/` | `operations` | Command operations log |
| `audit/` | `audit` | Immutable audit events |
| `schema/` | – | OpenAPI schema |
| `docs/` | – | Swagger UI |
| `redoc/` | – | ReDoc |

---

## User Roles

| Role | Description | Auto-verified? |
|---|---|---|
| `CUSTOMER` | Vehicle owner / driver | N/A |
| `PUBLIC` | Public citizen scanning QR | N/A |
| `POLICE_RESPONDER` | Police field responder | ❌ Requires supervisor approval |
| `MEDICAL_RESPONDER` | Medical field responder | ❌ Requires supervisor approval |
| `OPERATOR` | Command desk | ❌ Admin-assigned |
| `SUPERVISOR` | Command supervisor | ❌ Admin-assigned |
| `ADMIN` | System administrator | ❌ Admin-assigned |

---

## Security

- **JWT** Bearer tokens with role + responder-verification claims
- **Field-level encryption** (Fernet/AES-128) on `EmergencyContact` and `MedicalProfile` sensitive fields
- **Immutable audit log** for all state changes with sensitive-data redaction
- **Centralised permission classes** for all role gates
- **Standardised error envelope** (`success`, `error.code`, `error.message`, `error.details`)
- Secrets managed via environment variables — **never committed**

---

## Running Celery (requires Redis)

```bash
celery -A fixpoint_backend worker --loglevel=info
```

---

## Environment Variables

See [`.env.example`](.env.example) for the full list. Key variables:

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY` | Django signing key |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis cache |
| `CELERY_BROKER_URL` | Celery broker |
| `FIELD_ENCRYPTION_KEY` | Fernet key for field-level encryption |

---

## Project Structure

```
backend/
├── manage.py
├── requirements.txt
├── pytest.ini
├── .env.example
├── fixpoint_backend/
│   ├── settings/
│   │   ├── base.py         # Shared settings
│   │   ├── development.py  # Dev overrides (SQLite fallback, BrowsableAPI)
│   │   └── production.py   # Production overrides (strict security)
│   ├── celery.py
│   ├── urls.py             # Root versioned URL config
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── common/       # BaseModel, permissions, exceptions, health check
│   ├── audit/        # Immutable audit event log
│   ├── accounts/     # CustomUser model, JWT auth, registration
│   ├── profiles/     # UserProfile, ResponderProfile
│   ├── qr_codes/     # Safe-QR Badge management
│   ├── contacts/     # Emergency contacts (field-encrypted)
│   ├── medical/      # Medical profile (field-encrypted)
│   ├── alerts/       # Alert records + Celery tasks
│   ├── notifications/# Notification records + Celery dispatch tasks
│   ├── incidents/    # Incident lifecycle management
│   ├── responders/   # Responder dispatch assignment
│   └── operations/   # Command operations log
└── tests/
    └── test_foundation.py  # 34 foundation tests
```
