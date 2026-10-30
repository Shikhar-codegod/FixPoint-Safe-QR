# FixPoint Drive Safe-QR SOS

**A privacy-first, QR-enabled emergency assistance and incident reporting system for vehicles.**

## Overview

FixPoint Drive Safe-QR SOS is an emergency assistance platform designed to help people respond quickly when a vehicle owner or another road user needs assistance.

Every registered customer receives a unique QR code that can be attached to their vehicle. When someone scans the QR code, they can access a public emergency interface without being exposed to the vehicle owner's personal information, emergency contacts, or medical records.

The system enables emergency alert creation, incident reporting, emergency contact notifications, and coordinated response through FixPoint operations.

The platform is designed around privacy, reliability, consent, and accountability.

## Key Features

### 1. QR-Based Emergency Access

* Unique QR code for every registered customer.
* Secure, randomly generated QR tokens.
* QR scanning through a mobile application or web browser.
* No personal information embedded in the QR code.
* QR rotation and revocation support.

### 2. Public Emergency Interface

The public QR page provides four primary actions:

* **Call Ambulance:** Initiate an ambulance call.
* **Call Police:** Initiate a call to India's emergency number 112.
* **Report an Incident:** Report accidents, vehicle damage, tampering, or road hazards.
* **Create Emergency Alert:** Submit an emergency alert after reviewing and explicitly confirming the details.

Public users cannot access private customer profiles, emergency contact details, or medical records.

### 3. Emergency Alert Management

The emergency workflow follows these stages:

`DRAFT → CONFIRMED → ACTIVE → CLOSED`

* Create an emergency alert draft.
* Collect available location information and optional photographs.
* Allow the user to review the alert before submission.
* Require explicit confirmation before triggering notifications.
* Initiate independent response and notification workflows after confirmation.
* Support alert ownership, resolution, and closure.

### 4. Emergency Contact Notifications

The system is designed to support an independent notification workflow for each opted-in emergency contact.

Planned notification channels:

1. WhatsApp
2. SMS
3. Automated phone call

Contacts can acknowledge an alert through supported channels. Once acknowledged, remaining notification steps for that contact should be cancelled.

The notification system is designed with persistent attempt records, retry handling, idempotency, and recovery mechanisms.

### 5. Incident Reporting

Users can report non-emergency incidents such as:

* Accidents witnessed.
* Vehicle damage.
* Vehicle tampering.
* Road hazards.
* Other vehicle-related incidents.

Incident reports are handled separately from emergency alerts and do not automatically trigger the emergency contact notification chain.

### 6. FixPoint Operations

The operations system is intended to provide:

* Emergency alert monitoring.
* Operator alert claiming and ownership.
* Alert prioritization.
* Escalation to supervisors.
* Contact notification timelines.
* Authority call records.
* Internal notes and audit trails.
* Alert resolution and closure.

### 7. Responder Access Management

The platform is designed to support verified responders with role-based access.

Sensitive information is accessible only when the required authorization, consent, and active-alert conditions are satisfied.

### 8. Customer Privacy and Medical Information

Customers will be able to manage:

* Emergency contacts.
* Contact notification consent.
* Medical information.
* Medical document sharing permissions.
* QR code activation and revocation.
* Emergency alert history.
* Access history.

Medical information is not publicly accessible and is intended to be shared only with explicitly authorized parties.

---

## Technology Stack

| Component             | Technology                     |
| --------------------- | ------------------------------ |
| Backend Framework     | Python, Django                 |
| API Framework         | Django REST Framework          |
| Database              | PostgreSQL                     |
| Background Processing | Celery                         |
| Message Broker        | Redis                          |
| Authentication        | JWT                            |
| API Documentation     | OpenAPI / Swagger              |
| Testing               | Pytest / Django Test Framework |
| Frontend Integration  | REST APIs                      |

External notification providers and private object storage will be integrated through dedicated service adapters.

*The actual dependencies and integrations should be verified against the current repository.*

---

## System Architecture

The backend follows a modular architecture that separates authentication, customer data, emergency workflows, notifications, and operations.

### Proposed Application Structure

```text
fixpoint-backend/
│
├── config/
│   ├── settings/
│   ├── urls.py
│   ├── celery.py
│   └── wsgi.py
│
├── apps/
│   ├── accounts/
│   ├── profiles/
│   ├── qr_codes/
│   ├── contacts/
│   ├── alerts/
│   ├── notifications/
│   ├── incidents/
│   ├── responders/
│   ├── medical/
│   ├── operations/
│   ├── audit/
│   └── common/
│
├── tests/
├── requirements/
├── manage.py
├── .env.example
├── .gitignore
└── README.md
```

This represents the intended modular organization. The actual repository structure may differ as development progresses.

---

## Emergency Alert Workflow

```text
Vehicle QR Code Scan
        |
        v
Public Emergency Interface
        |
        +----------------------+
        |          |           |
        v          v           v
   Call 112    Report       Create
   /Ambulance  Incident     Alert
                            |
                            v
                       Create Draft
                            |
                            v
                    Collect Information
                    (Location / Photos)
                            |
                            v
                     Review Summary
                            |
                            v
                  Explicit Confirmation
                            |
                            v
                    Alert Confirmed
                            |
              +-------------+-------------+
              |             |             |
              v             v             v
          FixPoint       Emergency     Raiser
          Operations     Contacts      Confirmation
              |             |             |
              v             v             v
          Operator      Notification   Call 112
          Response      Workflows      Option
```

**Important:** Emergency authority calls are user-initiated through the phone dialer. The platform does not claim automatic dispatch or direct integration with government emergency systems.

---

## Installation and Local Setup

### Prerequisites

Install the following:

* Python 3.11 or a compatible supported version.
* PostgreSQL.
* Redis.
* Git.

### 1. Clone the Repository

```bash
git clone <repository-url>
cd fixpoint-backend
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

On Linux/macOS:

```bash
source venv/bin/activate
```

### 3. Install Dependencies

If the project uses a root requirements file:

```bash
pip install -r requirements.txt
```

If dependencies are organized into multiple files under `requirements/`, use the appropriate development requirements file.

### 4. Configure Environment Variables

Create a `.env` file using `.env.example` as a reference.

Example configuration:

```env
DEBUG=True
SECRET_KEY=your-django-secret-key

DATABASE_URL=postgresql://username:password@localhost:5432/fixpoint_db

REDIS_URL=redis://localhost:6379/0

ALLOWED_HOSTS=localhost,127.0.0.1

CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

Additional environment variables may be required for JWT, private file storage, and external notification providers.

Never commit `.env` files, credentials, API keys, or production secrets.

### 5. Apply Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create an Administrator

```bash
python manage.py createsuperuser
```

### 7. Start the Development Server

```bash
python manage.py runserver
```

### 8. Start Background Processing

When Celery tasks are configured, start a worker:

```bash
celery -A config worker -l info
```

Start Celery Beat separately if periodic tasks have been configured:

```bash
celery -A config beat -l info
```

Redis must be running before starting background workers.

*Run only the commands supported by the current repository configuration.*

---

## API Structure

The backend uses versioned REST API endpoints.

Base path:

```text
/api/v1/
```

The following are planned API domains:

| Module        | Responsibility                              |
| ------------- | ------------------------------------------- |
| accounts      | Registration, login and authentication      |
| profiles      | Customer profile management                 |
| qr-codes      | QR generation, scanning and revocation      |
| contacts      | Emergency contact management                |
| alerts        | Emergency alert lifecycle                   |
| notifications | Notification workflows and acknowledgements |
| incidents     | Incident reporting                          |
| responders    | Responder verification and access           |
| medical       | Medical information and documents           |
| operations    | Emergency operations management             |
| audit         | Security and activity records               |

Actual endpoint availability should be checked in the API documentation and source code.

---

## Security and Privacy Principles

Security is a core requirement of the platform.

The backend is designed around the following principles:

* Random, high-entropy QR tokens.
* Hashed storage of QR and acknowledgement tokens.
* Authentication and role-based authorization.
* Field-level restrictions for sensitive information.
* Encryption of sensitive customer data.
* Private storage for uploaded documents and photographs.
* Explicit consent before emergency contact notifications.
* Explicit consent for medical information sharing.
* Short-lived, authorized responder access.
* Audit logging for sensitive operations.
* Input validation and upload restrictions.
* Protection against duplicate emergency confirmations.
* Rate limiting and abuse prevention.

Public QR endpoints must never expose private customer information.

---

## Development Roadmap

Development is organized into incremental phases.

| Phase   | Scope                                                              |
| ------- | ------------------------------------------------------------------ |
| Phase 1 | Backend foundation, authentication, database and QR infrastructure |
| Phase 2 | Emergency alert creation, confirmation and lifecycle               |
| Phase 3 | Notification workflows, acknowledgement and retry mechanisms       |
| Phase 4 | FixPoint operations dashboard and escalation                       |
| Phase 5 | Real WhatsApp, SMS and calling provider integrations               |
| Phase 6 | Responder verification, medical access and incident reporting      |
| Phase 7 | Wrong-parking requests, security testing and production readiness  |

The roadmap is a development plan, not a statement that these features have already been completed.

---

## Testing

Run the project's test suite using:

```bash
python manage.py test
```

If pytest is configured:

```bash
pytest
```

Testing should cover:

* Authentication and authorization.
* QR token generation and validation.
* Public API privacy.
* Emergency alert lifecycle.
* Duplicate confirmation prevention.
* Contact notification workflows.
* Acknowledgement and cancellation.
* Retry and worker recovery.
* Responder access restrictions.
* Audit logging.
* File upload validation.

External notification services should be tested using mock providers before production integration.

---

## Important Design Decisions

1. **Privacy First:** Scanning a QR code does not grant access to private customer information.
2. **Explicit Confirmation:** An emergency alert cannot be activated without an explicit confirmation action.
3. **Independent Notification Chains:** Each emergency contact has an independently managed notification workflow.
4. **Database as Source of Truth:** Alert states and notification schedules must persist in PostgreSQL.
5. **Failure Resilience:** Temporary provider or worker failures must not silently discard emergency workflows.
6. **Human Oversight:** FixPoint operations personnel coordinate response; the platform does not guarantee emergency-service dispatch.
7. **Consent-Based Access:** Contact notifications and medical information sharing require appropriate consent.

---

## Current Development Status

**Project Status: Under Development**

This repository is being developed incrementally.

Features should be considered complete only after their implementation, permissions, database behavior, and relevant tests have been verified.

Mock integrations, placeholders, and planned functionality must not be represented as production-ready features.

---

## Contributing

Development should follow a phase-wise approach:

1. Understand the existing architecture.
2. Review the relevant technical requirements.
3. Implement one module at a time.
4. Run migrations and tests.
5. Review security and permissions.
6. Update API documentation.
7. Document completed functionality and known limitations.

Changes to the emergency workflow, security model, or database architecture should be reviewed before implementation.

---

## License

This project is currently under development. Licensing and distribution terms will be specified separately.

