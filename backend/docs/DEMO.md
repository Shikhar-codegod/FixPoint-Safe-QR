# FixPoint Safe-QR: End-to-End Demo Walkthrough

This interactive guide walks through the complete emergency workflow using `curl`.
All telecom interactions run on simulated **MOCK** providers—no real SMS, WhatsApp messages, or phone calls are dispatched.

---

## 0. Prerequisites & Fast Demo Setup

Ensure the backend server is running with the fast demo profile:

```bash
# Set fast timing profile in your environment or .env
export NOTIFICATION_WHATSAPP_WAIT_SECONDS=5
export NOTIFICATION_SMS_TO_CALL_DELAY_SECONDS=3
export NOTIFICATION_CALL_RETRY_LIMIT=1
export NOTIFICATION_PROVIDER_MODE=mock

# Start server
python manage.py runserver 0.0.0.0:8000
```

If Redis is not running, run the sweeper in a separate terminal:
```bash
python manage.py run_notification_sweeper --interval 2
```

Base URL: `http://localhost:8000/api/v1`

---

## 1. Verify Provider Status

Check that telecom gateways are safely running in simulation mode:

```bash
curl -X GET http://localhost:8000/api/v1/notifications/provider-status/
```

**Expected Response**:
```json
{
  "success": true,
  "data": {
    "mode": "mock",
    "whatsapp_real_configured": false,
    "sms_real_configured": false,
    "voice_real_configured": false
  },
  "message": null
}
```

---

## 2. Register & Authenticate Customer

Register a demo vehicle owner:

```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "priya.sharma@example.com",
    "password": "SecurePassword!123",
    "password_confirm": "SecurePassword!123",
    "first_name": "Priya",
    "last_name": "Sharma",
    "role": "CUSTOMER"
  }'
```

Log in and obtain JWT access token:

```bash
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "priya.sharma@example.com",
    "password": "SecurePassword!123"
  }'
```
*Save the `access` token returned:*
```bash
TOKEN="<paste_access_token_here>"
```

---

## 3. Emergency Contact Management & Consent Flow

### 3.1 Add Emergency Contact
Add an emergency contact with a standard 10-digit Indian phone number:

```bash
curl -X POST http://localhost:8000/api/v1/contacts/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Rohan Sharma",
    "relationship": "Brother",
    "phone_number": "9876543210",
    "preferred_language": "en",
    "notify_whatsapp": true,
    "notify_sms": true,
    "notify_call": true,
    "wave": 1
  }'
```
*Notice that the response shows `phone_number: "+919876543210"`, `consent_status: "PENDING"`, and `phone_hash` is never exposed. Save the contact ID (`CONTACT_ID`).*

### 3.2 Request Consent
Request consent for this contact. In mock mode, the API returns a simulated invite link:

```bash
curl -X POST http://localhost:8000/api/v1/contacts/<CONTACT_ID>/consent/request/ \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response**:
```json
{
  "success": true,
  "data": {
    "contact_id": "<CONTACT_ID>",
    "consent_status": "PENDING",
    "consent_expires_at": "...",
    "debug_consent_link": "http://localhost:8000/api/v1/contacts/consent/<CONSENT_TOKEN>/"
  },
  "message": "Consent request dispatched to contact."
}
```

### 3.3 Public Consent Preview (Safe against link crawlers)
Simulate opening the consent link in a browser. It previews the requester's first name without altering state:

```bash
curl -X GET http://localhost:8000/api/v1/contacts/consent/<CONSENT_TOKEN>/
```

**Expected Response**:
```json
{
  "success": true,
  "data": {
    "requester_first_name": "Priya",
    "contact_name": "Rohan Sharma",
    "status": "PENDING",
    "expires_at": "..."
  }
}
```

### 3.4 Public Consent Acceptance
The contact clicks "Accept":

```bash
curl -X POST http://localhost:8000/api/v1/contacts/consent/<CONSENT_TOKEN>/ \
  -H "Content-Type: application/json" \
  -d '{"decision": "accept"}'
```

**Expected Response**:
```json
{
  "success": true,
  "data": {
    "decision": "accept",
    "consent_status": "GRANTED"
  },
  "message": "Emergency contact consent successfully recorded."
}
```

---

## 4. Trigger SOS Alert & Notification Workflow

### 4.1 Trigger Alert
Trigger an SOS emergency alert:

```bash
curl -X POST http://localhost:8000/api/v1/alerts/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "severity": "CRITICAL",
    "latitude": "19.076090",
    "longitude": "72.877426",
    "location_address": "Western Express Highway, Mumbai",
    "notes": "Vehicle rollover accident"
  }'
```
*Save the `id` from the response as `ALERT_ID`.*

### 4.2 View Notification Timeline Progression
Immediately inspect the alert timeline:

```bash
curl -X GET http://localhost:8000/api/v1/notifications/alerts/<ALERT_ID>/timeline/ \
  -H "Authorization: Bearer $TOKEN"
```

**What you will see**:
1. At $t=0$: Step is `WHATSAPP` $\rightarrow$ `status: "ACCEPTED"`, `is_simulated: true`, `provider_name: "MOCK"`, `masked_destination: "+91******3210"`.
2. After 5 seconds without acknowledgment (sweeper ticks): Step escalates to `SMS` $\rightarrow$ `status: "ACCEPTED"`.
3. After 3 seconds without acknowledgment: Step escalates to automated `VOICE_CALL` $\rightarrow$ `status: "ACCEPTED"`.

---

## 5. Contact Acknowledgment

Each active notification includes a unique acknowledgment token.

### 5.1 Public Web Link Acknowledgment
Inspect the alert landing page (crawler-safe):

```bash
curl -X GET http://localhost:8000/api/v1/notifications/ack/<ACK_TOKEN>/
```

Submit acknowledgment:

```bash
curl -X POST http://localhost:8000/api/v1/notifications/ack/<ACK_TOKEN>/
```
*The chain immediately transitions to `ACKNOWLEDGED`, cancelling any remaining scheduled delivery attempts for that contact.*

### 5.2 Simulated Inbound Webhook (WhatsApp Quick-Reply / IVR)
When in mock mode, inbound simulated carrier webhooks are supported via HMAC-SHA256 signature:

```bash
# Expected HMAC signature = HMAC_SHA256(SECRET_KEY, "<ACK_TOKEN>:WHATSAPP")
curl -X POST http://localhost:8000/api/v1/notifications/webhooks/mock/ \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: <computed_signature>" \
  -d '{
    "token": "<ACK_TOKEN>",
    "channel": "WHATSAPP"
  }'
```

---

## 6. Deterministic Failure Injection Demo

To demo instant carrier escalation when WhatsApp fails:
1. Add an emergency contact with a phone number ending in `0000` (e.g. `9876540000`).
2. Grant consent and trigger an alert.
3. Check the timeline: WhatsApp fails immediately $\rightarrow$ the system escalates directly to `SMS` without waiting for the 5-second timeout!

Similarly:
- Numbers ending in `1111` fail SMS immediately $\rightarrow$ escalate to Call.
- Numbers ending in `2222` simulate unanswered voice calls $\rightarrow$ retries once then marks chain `EXHAUSTED`.

---

## 7. Incident Reporting & Metadata Stripping

### 7.1 Report Incident with EXIF Photo
File an incident report:

```bash
curl -X POST http://localhost:8000/api/v1/incidents/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_type": "ACCIDENT",
    "description": "Minor fender bender near intersection",
    "latitude": "19.0760",
    "longitude": "72.8777",
    "location_precision": "PRECISE",
    "reporter_contact_shared": true
  }'
```
*Save `incident_number` (e.g. `INC-A1B2C3D4`).*

### 7.2 Upload Photo with EXIF & GPS
Upload any image (even with GPS EXIF tags):

```bash
curl -X POST http://localhost:8000/api/v1/incidents/<INCIDENT_NUMBER>/photos/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "photo=@test_image.jpg"
```
*Pillow validates the image type (JPEG, PNG, WEBP), strips 100% of EXIF, GPS, and camera metadata, and saves the sanitized image under secure private storage.*

### 7.3 Operator Upgrade to Emergency Alert
An authorized operator, supervisor, or admin upgrades the incident to a HIGH severity emergency alert:

```bash
# Log in as operator
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "operator@fixpoint.io", "password": "OperatorPassword!123"}'

OP_TOKEN="<operator_access_token>"

# Upgrade incident to emergency alert
curl -X POST http://localhost:8000/api/v1/incidents/<INCIDENT_NUMBER>/upgrade-to-alert/ \
  -H "Authorization: Bearer $OP_TOKEN"
```

**Expected Response**:
```json
{
  "success": true,
  "data": {
    "incident_number": "INC-A1B2C3D4",
    "alert_id": "<NEW_ALERT_ID>",
    "alert_status": "TRIGGERED",
    "alert_severity": "HIGH"
  },
  "message": "Incident successfully upgraded to emergency alert."
}
```
*This links the incident to the new alert and automatically initiates contact notification chains for the vehicle owner's eligible contacts!*
