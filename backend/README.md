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
| Image Processing | Pillow 10.0+ (EXIF / GPS metadata sanitization) |
| API Docs | drf-spectacular (Swagger + ReDoc) |
| Encryption | `cryptography` – AES-128/Fernet & HMAC-SHA256 |
| Testing | pytest + pytest-django |

---

## What is Real vs Simulated (Honesty Rule)

> [!IMPORTANT]
> **No live WhatsApp messages, SMS texts, or telephone calls are dispatched.**
> All telecommunication gateways run on deterministic **MOCK** providers.

- **Notification Mode**: Defaults strictly to `NOTIFICATION_PROVIDER_MODE=mock`. On server boot, a warning is logged:
  `"Notification providers are in MOCK mode - no real messages are sent"`.
- **Delivery Records**: Every delivery attempt is recorded with `provider="MOCK"` and `is_simulated=true`. Both fields are exposed in timelines and API responses.
- **Message Content**: All simulated text message bodies are prefixed with `[SIMULATED]`.
- **Provider Status**: A public inspection endpoint is available at `GET /api/v1/notifications/provider-status/`. It returns:
  ```json
  {
    "mode": "mock",
    "whatsapp_real_configured": false,
    "sms_real_configured": false,
    "voice_real_configured": false
  }
  ```
- **Real Provider Skeletons**: Skeleton adapters (`TwilioWhatsAppProvider`, `GupshupSmsProvider`, `ExotelVoiceProvider`) exist behind the unified `BaseNotificationProvider` interface. They do not store credentials and raise `ProviderNotConfigured` if selected without explicit vendor API keys. They are **never** configured as default.
- **Deterministic Mock Failure Injection**:
  Mock phone numbers ending in specific suffixes trigger deterministic failures to demo escalation flows:
  - `...0000`: WhatsApp delivery fails immediately $\rightarrow$ triggers instant escalation to SMS.
  - `...1111`: SMS delivery fails immediately $\rightarrow$ triggers instant escalation to automated voice call.
  - `...2222`: Voice call is unanswered $\rightarrow$ triggers retry up to `NOTIFICATION_CALL_RETRY_LIMIT` and marks chain `EXHAUSTED`.
  - `...3333`: All notification channels fail immediately.
  - Suffix failure channel can also be configured via environment variable `MOCK_FAIL_CHANNELS` (e.g. `WHATSAPP,SMS`).

---

## Quick Start

```bash
# 1. Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 2. Install dependencies (including Pillow)
pip install -r requirements.txt

# 3. Copy .env.example and configure
copy .env.example .env

# 4. Run migrations
python manage.py migrate

# 5. Start the development server
python manage.py runserver 0.0.0.0:8000

# 6. Run all test suites
python -m pytest -v
```

---

## Running Without Redis (Standalone Demo Mode)

For demos or environments without a running Redis server:
1. `fixpoint_backend/settings/development.py` activates `CELERY_TASK_ALWAYS_EAGER = True`.
2. Run the standalone crash-safe notification sweeper:
   ```bash
   python manage.py run_notification_sweeper --interval 2
   ```
   This polls Postgres / SQLite every 2 seconds, advances due chains through their escalation timelines, and recovers stale pending attempts.

### Demo Fast Timing Profile
For rapid live demonstrations without waiting minutes for WhatsApp timeouts:
```bash
# In .env or runtime environment
NOTIFICATION_WHATSAPP_WAIT_SECONDS=5
NOTIFICATION_SMS_TO_CALL_DELAY_SECONDS=3
NOTIFICATION_CALL_RETRY_LIMIT=1
NOTIFICATION_PENDING_STALE_SECONDS=10
```

---

## Detailed Endpoints Table (`/api/v1/`)

### Emergency Contacts (`/api/v1/contacts/`)

## Environment Variables

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY` | Django signing key |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis cache |
| `CELERY_BROKER_URL` | Celery broker |
| `FIELD_ENCRYPTION_KEY` | Fernet key for field-level encryption (32 url-safe base64 bytes) |

> **Generating a Fernet Key:**
> ```bash
> python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
> ```
> *Note: Set `FIELD_ENCRYPTION_KEY` in your `.env` file before running the application. Never commit encryption keys.*

---

## Detailed Endpoints Table (`/api/v1/`)

### Emergency Contacts (`/api/v1/contacts/`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/v1/contacts/` | Authenticated | List current user's emergency contacts (decrypted). |
| `POST` | `/api/v1/contacts/` | Authenticated | Add contact (E.164 normalized, max 5, duplicate prevention via HMAC-SHA256 hash). |
| `GET` | `/api/v1/contacts/<uuid:id>/` | Owner Only | Retrieve decrypted emergency contact. |
| `PUT` | `/api/v1/contacts/<uuid:id>/` | Owner Only | Update emergency contact details. |
| `PATCH` | `/api/v1/contacts/<uuid:id>/` | Owner Only | Partial update (preferences, notification channels, language). |
| `DELETE` | `/api/v1/contacts/<uuid:id>/` | Owner Only | Remove contact and cancel active notification chains. |
| `POST` | `/api/v1/contacts/<uuid:id>/consent/request/` | Owner Only | Issue 7-day single-use consent token; dispatches mock invite. |
| `GET` | `/api/v1/contacts/consent/<str:token>/` | Public | Public landing page showing requester's first name (no state change). |
| `POST` | `/api/v1/contacts/consent/<str:token>/` | Public | Accept (`accept`) or decline (`decline`) emergency contact consent. Single-use. |
| `POST` | `/api/v1/contacts/<uuid:id>/consent/withdraw/` | Owner Only | Immediately revoke consent and abort active notification chains. |

### Emergency Notifications (`/api/v1/notifications/`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/v1/notifications/provider-status/` | Public | Inspect active mock vs real provider configurations. |
| `GET` | `/api/v1/notifications/alerts/<uuid:alert_id>/timeline/` | Owner / Operator | View sanitized notification progress and attempts with masked phone numbers. |
| `GET` | `/api/v1/notifications/ack/<str:token>/` | Public | View alert summary and acknowledgement button (safe against link crawlers). |
| `POST` | `/api/v1/notifications/ack/<str:token>/` | Public | Idempotently acknowledge alert; stops further steps for that contact. |
| `POST` | `/api/v1/notifications/webhooks/mock/` | Mock Mode Only | HMAC-SHA256 verified inbound webhook simulating WhatsApp quick-reply / IVR press 1. |

### Incident Reporting (`/api/v1/incidents/`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/v1/incidents/` | Scoped | Customer sees own vehicles/reports; Operators/Admins see all. |
| `POST` | `/api/v1/incidents/` | Authenticated | File an incident report (`ACCIDENT`, `DAMAGE`, `TAMPERING`, `HAZARD`, `OTHER`). |
| `GET` | `/api/v1/incidents/queue/` | Operator / Admin | Operational command queue for unassigned/active incident triage. |
| `POST` | `/api/v1/incidents/report/<str:code_identifier>/` | Public (Throttled) | Anonymous citizen scan report (rate limited: 5/hr IP, 3/10m QR). |
| `GET` | `/api/v1/incidents/<str:incident_number>/` | Scoped | Retrieve full incident details, status, coordinates, and photo links. |
| `PATCH` | `/api/v1/incidents/<str:incident_number>/` | Operator / Admin | Advance incident status (`REPORTED` $\rightarrow$ `DISPATCHED` $\rightarrow$ `IN_PROGRESS` $\rightarrow$ `RESOLVED` $\rightarrow$ `CLOSED`). |
| `POST` | `/api/v1/incidents/<str:incident_number>/upgrade-to-alert/` | Operator / Admin | Upgrade incident to HIGH emergency alert and trigger contact notification chains. |
| `POST` | `/api/v1/incidents/<str:incident_number>/photos/` | Scoped | Attach photos (max 3, 5MB each, EXIF/GPS metadata permanently stripped). |
| `GET` | `/api/v1/incidents/<str:incident_number>/photos/<uuid:photo_id>/` | Scoped | Authenticated stream download for private incident photo. |

---

## User Roles & Permissions

| Role | Description | Capabilities |
|---|---|---|
| `CUSTOMER` | Registered vehicle owner | Manage contacts, view own incidents/alerts, manage QR badges. |
| `PUBLIC` | Anonymous citizen | Scan active QR badge, submit rate-limited incident report. |
| `POLICE_RESPONDER` | Police field unit | Respond to emergency dispatches (requires supervisor verification). |
| `MEDICAL_RESPONDER` | Medical paramedic unit | Respond to medical dispatches (requires supervisor verification). |
| `OPERATOR` | Command desk | Triage incidents, upgrade incidents to alerts, update dispatch status. |
| `SUPERVISOR` | Field supervisor | Approve responder registrations, view audit trails, oversee incidents. |
| `ADMIN` | System administrator | Full administrative control, system settings, user management. |

---

## Security Architecture

- **Field-level encryption**: Contact phone numbers and medical details are encrypted with AES-128 via Fernet (`FIELD_ENCRYPTION_KEY`).
- **Deterministic Blind Indexing**: Contact phone uniqueness is enforced using an HMAC-SHA256 hash (`phone_hash`) with a salt derived from `FIELD_ENCRYPTION_KEY`. Raw phone numbers and hashes are never exposed in logs or audit records.
- **Privacy Masking**: Phone numbers are masked across all APIs and audit trails (`+91******1234`).
- **Single-Use Hashed Tokens**: Consent and acknowledgement links store only URL-safe SHA-256 hashes in the database with strict expiration windows.
- **Metadata Sanitization**: Uploaded incident photos are decoded with Pillow, stripped of all EXIF, GPS, camera metadata, and re-encoded before saving to private storage.

---

## End-to-End Demo Script

See [`docs/DEMO.md`](docs/DEMO.md) for a complete `curl`-based walkthrough demonstrating:
1. User registration and contact addition
2. Consent request and public consent acceptance
3. SOS alert trigger and notification chain progression (WhatsApp $\rightarrow$ SMS $\rightarrow$ Call)
4. Public token acknowledgment and mock webhook callback
5. Deterministic failure injection demo (`...0000`)
6. Incident reporting, EXIF-stripped photo upload, and escalation upgrade to emergency alert
