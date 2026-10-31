"""
Phase 2 Test Suite: Emergency Alert Draft, Confirmation, Activation, and Closure.
FixPoint Drive Safe-QR SOS Backend

Covers:
1. Secure QR token generation (>=128 bits entropy), SHA-256 token hashing, token rotation, and public resolution privacy.
2. Alert draft creation (DRAFT only, optional location/notes, single-use confirmation token).
3. Duplicate active alert prevention (HTTP 409 Conflict).
4. Single-use confirmation mechanism (DRAFT -> CONFIRMED, replay prevention, expiry).
5. Public API privacy (no customer PII or sensitive data exposed).
6. Operator alert queue and claim workflow (CONFIRMED -> ACTIVE, concurrency conflict handling).
7. Alert closure (CLOSED terminal state, cancellation of pending queued notifications).
8. Optional evidence attachment.
"""

import hashlib
import secrets
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import CustomUser, UserRole
from apps.qr_codes.models import QRCodeBadge, QRCodeStatus
from apps.qr_codes.services import create_qr_badge, rotate_qr_badge, hash_qr_token
from apps.alerts.models import AlertRecord, AlertStatus, AlertSeverity, AlertConfirmationToken, AlertEvidence
from apps.alerts.services import create_alert_draft, confirm_alert, claim_alert, close_alert
from apps.contacts.models import EmergencyContact
from apps.notifications.models import NotificationRecord, NotificationStatus


def create_user(email, password, role=UserRole.CUSTOMER, is_verified=False, **kwargs):
    return CustomUser.objects.create_user(
        email=email,
        password=password,
        role=role,
        is_verified_responder=is_verified,
        **kwargs
    )


class TestSecureQRResolution(TestCase):
    """
    Tests secure QR token generation, storage as hash, rotation, and privacy-preserving public resolution.
    """

    def setUp(self):
        self.client = APIClient()
        self.customer = create_user('badge_owner@fixpoint.io', 'Pass1234!Owner', role=UserRole.CUSTOMER)
        self.badge = create_qr_badge(
            user=self.customer,
            vehicle_registration='KA-01-AB-1234',
            vehicle_model='Hyundai Creta'
        )
        self.raw_token = self.badge.raw_token

    def test_qr_token_has_sufficient_entropy_and_is_hashed(self):
        """
        QR token must contain at least 128 bits of entropy and be stored as a SHA-256 hash.
        """
        # raw_token generated via secrets.token_urlsafe(24) = 192 bits of entropy
        self.assertGreaterEqual(len(self.raw_token), 24)
        # token_hash stored in DB must match SHA-256 of raw_token
        expected_hash = hashlib.sha256(self.raw_token.encode('utf-8')).hexdigest()
        self.assertEqual(self.badge.token_hash, expected_hash)
        # Raw token must NOT be stored directly in the database
        db_badge = QRCodeBadge.objects.get(id=self.badge.id)
        self.assertNotEqual(db_badge.token_hash, self.raw_token)
        self.assertNotIn(self.raw_token, db_badge.code_identifier)

    def test_public_qr_resolution_identifies_vehicle_without_pii(self):
        """
        Public scanning resolves vehicle registration and model without leaking owner email,
        scan metrics, or personal information.
        """
        url = reverse('qr_codes:resolve-badge', kwargs={'code_identifier': self.raw_token})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.json()['data']
        self.assertEqual(data['vehicle_registration'], 'KA-01-AB-1234')
        self.assertEqual(data['vehicle_model'], 'Hyundai Creta')
        self.assertTrue(data['is_active'])

        # Security check: Privacy leak prevention
        self.assertNotIn('owner_email', data)
        self.assertNotIn('user', data)
        self.assertNotIn('scan_count', data)
        self.assertNotIn('last_scanned_at', data)
        self.assertNotIn('token_hash', data)

    def test_invalid_or_revoked_qr_token_returns_404(self):
        """
        Scanning an invalid or revoked QR token must return HTTP 404.
        """
        # Invalid token
        bad_url = reverse('qr_codes:resolve-badge', kwargs={'code_identifier': 'NON_EXISTENT_TOKEN_12345'})
        resp = self.client.get(bad_url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        # Revoked badge
        self.badge.status = QRCodeStatus.REVOKED
        self.badge.save(update_fields=['status'])
        resp_revoked = self.client.get(reverse('qr_codes:resolve-badge', kwargs={'code_identifier': self.raw_token}))
        self.assertEqual(resp_revoked.status_code, status.HTTP_404_NOT_FOUND)

    def test_scanning_qr_never_triggers_emergency_alert(self):
        """
        Scanning a QR code must be read-only and never create an alert record.
        """
        initial_alert_count = AlertRecord.objects.count()
        url = reverse('qr_codes:resolve-badge', kwargs={'code_identifier': self.raw_token})
        self.client.get(url)
        self.assertEqual(AlertRecord.objects.count(), initial_alert_count)

    def test_qr_token_rotation_invalidates_previous_token(self):
        """
        Rotating a badge generates a new secret token and invalidates the previous token.
        """
        old_token = self.raw_token
        _, new_token = rotate_qr_badge(self.badge)

        self.assertNotEqual(old_token, new_token)

        # Old token fails to resolve
        old_resp = self.client.get(reverse('qr_codes:resolve-badge', kwargs={'code_identifier': old_token}))
        self.assertEqual(old_resp.status_code, status.HTTP_404_NOT_FOUND)

        # New token resolves successfully
        new_resp = self.client.get(reverse('qr_codes:resolve-badge', kwargs={'code_identifier': new_token}))
        self.assertEqual(new_resp.status_code, status.HTTP_200_OK)


class TestAlertDraftAndConfirmationLifecycle(TestCase):
    """
    Tests the emergency alert lifecycle: DRAFT -> CONFIRMED -> ACTIVE -> CLOSED.
    """

    def setUp(self):
        self.client = APIClient()
        self.token_url = reverse('accounts:token_obtain_pair')

        self.customer = create_user('cust_alert@fixpoint.io', 'Pass1234!C', role=UserRole.CUSTOMER)
        self.operator = create_user('ops_alert@fixpoint.io', 'Pass1234!O', role=UserRole.OPERATOR)
        self.supervisor = create_user('sup_alert@fixpoint.io', 'Pass1234!S', role=UserRole.SUPERVISOR)
        self.unrelated_customer = create_user('unrelated@fixpoint.io', 'Pass1234!U', role=UserRole.CUSTOMER)

        self.badge = create_qr_badge(
            user=self.customer,
            vehicle_registration='DL-01-XY-9999',
            vehicle_model='Tata Nexon'
        )
        self.raw_qr_token = self.badge.raw_token

        # Register an emergency contact
        self.contact = EmergencyContact.objects.create(
            user=self.customer,
            name='Emergency Contact 1',
            relationship='Sibling',
            phone_number='+919876543210'
        )

    def _auth(self, user, password):
        resp = self.client.post(self.token_url, {'email': user.email, 'password': password})
        token = resp.json()['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_create_alert_creates_draft_only_and_returns_confirmation_token(self):
        """
        Creating an alert via public endpoint creates a record in DRAFT status only
        and returns a single-use confirmation token.
        """
        url = reverse('alerts:alerts-list-create')
        payload = {
            'qr_token': self.raw_qr_token,
            'latitude': 28.6139,
            'longitude': 77.2090,
            'location_address': 'Connaught Place, New Delhi',
            'notes': 'Vehicle collision at roundabout'
        }
        resp = self.client.post(url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        data = resp.json()['data']
        self.assertEqual(data['status'], AlertStatus.DRAFT)
        self.assertEqual(data['vehicle_registration'], 'DL-01-XY-9999')
        self.assertIn('confirmation_token', data)
        self.assertIsNotNone(data['confirmation_token'])

        # Check DB state
        alert = AlertRecord.objects.get(id=data['alert_id'])
        self.assertEqual(alert.status, AlertStatus.DRAFT)
        self.assertIsNone(alert.confirmed_at)

        # Raw confirmation token must be stored as SHA-256 hash
        conf_token_record = AlertConfirmationToken.objects.get(alert=alert)
        expected_hash = hashlib.sha256(data['confirmation_token'].encode('utf-8')).hexdigest()
        self.assertEqual(conf_token_record.token_hash, expected_hash)
        self.assertIsNone(conf_token_record.used_at)

    def test_location_and_notes_are_optional_in_draft(self):
        """
        An emergency alert draft can be created with only the QR token; location/notes are optional.
        """
        url = reverse('alerts:alerts-list-create')
        resp = self.client.post(url, {'qr_token': self.raw_qr_token}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.json()['data']['status'], AlertStatus.DRAFT)

    def test_duplicate_active_alert_creation_is_prevented(self):
        """
        Attempting to create another alert for a vehicle that already has an active alert
        must be rejected with HTTP 409 Conflict.
        """
        url = reverse('alerts:alerts-list-create')
        # Create first draft
        resp1 = self.client.post(url, {'qr_token': self.raw_qr_token}, format='json')
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)

        # Second creation attempt for same vehicle
        resp2 = self.client.post(url, {'qr_token': self.raw_qr_token}, format='json')
        self.assertEqual(resp2.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(resp2.json()['error']['code'], 'active_alert_exists')

    def test_confirmation_transitions_draft_to_confirmed_and_dispatches_notification(self):
        """
        Confirming an alert with its single-use token transitions status to CONFIRMED
        and creates queued notifications for emergency contacts.
        """
        # Create draft
        alert, raw_conf_token = create_alert_draft(qr_token=self.raw_qr_token)
        self.assertEqual(alert.status, AlertStatus.DRAFT)

        # Confirm
        url = reverse('alerts:alert-confirm', kwargs={'alert_id': alert.id})
        resp = self.client.post(url, {'confirmation_token': raw_conf_token}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        alert.refresh_from_db()
        self.assertEqual(alert.status, AlertStatus.CONFIRMED)
        self.assertIsNotNone(alert.confirmed_at)

        # Verify confirmation token is marked used
        token_record = AlertConfirmationToken.objects.get(alert=alert)
        self.assertIsNotNone(token_record.used_at)

        # Verify notification record was queued
        notifications = NotificationRecord.objects.filter(alert=alert)
        self.assertGreaterEqual(notifications.count(), 1)
        self.assertEqual(notifications.first().status, NotificationStatus.QUEUED)

    def test_single_use_token_cannot_be_reused(self):
        """
        Replaying a confirmation token must return HTTP 400.
        """
        alert, raw_conf_token = create_alert_draft(qr_token=self.raw_qr_token)
        url = reverse('alerts:alert-confirm', kwargs={'alert_id': alert.id})

        # First confirmation succeeds
        resp1 = self.client.post(url, {'confirmation_token': raw_conf_token}, format='json')
        self.assertEqual(resp1.status_code, status.HTTP_200_OK)

        # Replay attempt fails
        resp2 = self.client.post(url, {'confirmation_token': raw_conf_token}, format='json')
        self.assertEqual(resp2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp2.json()['error']['code'], 'invalid_token')

    def test_expired_confirmation_token_is_rejected(self):
        """
        An expired confirmation token must be rejected with HTTP 400.
        """
        alert, raw_conf_token = create_alert_draft(qr_token=self.raw_qr_token)
        # Fast-forward token expiry into the past
        token_record = AlertConfirmationToken.objects.get(alert=alert)
        token_record.expires_at = timezone.now() - timezone.timedelta(minutes=1)
        token_record.save(update_fields=['expires_at'])

        url = reverse('alerts:alert-confirm', kwargs={'alert_id': alert.id})
        resp = self.client.post(url, {'confirmation_token': raw_conf_token}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('expired', resp.json()['error']['message'].lower())

    def test_public_alert_detail_never_exposes_pii(self):
        """
        Public unauthenticated GET /api/v1/alerts/<id>/ must return minimal vehicle status
        and never expose user email, coordinates, notes, or emergency contacts.
        """
        alert, _ = create_alert_draft(
            qr_token=self.raw_qr_token,
            latitude=28.6139,
            longitude=77.2090,
            location_address='Secret Location',
            notes='Confidential medical notes'
        )

        url = reverse('alerts:alert-detail', kwargs={'alert_id': alert.id})
        # Unauthenticated request
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()['data']

        self.assertEqual(data['status'], AlertStatus.DRAFT)
        self.assertEqual(data['vehicle_registration'], 'DL-01-XY-9999')

        # Privacy checks: PII must NOT be present
        self.assertNotIn('user_email', data)
        self.assertNotIn('latitude', data)
        self.assertNotIn('longitude', data)
        self.assertNotIn('location_address', data)
        self.assertNotIn('notes', data)
        self.assertNotIn('confirmation_token', data)

    def test_owner_and_operator_receive_full_alert_detail(self):
        """
        The alert owner and authorized operators receive full alert details.
        """
        alert, _ = create_alert_draft(
            qr_token=self.raw_qr_token,
            latitude=28.6139,
            longitude=77.2090,
            location_address='Connaught Place',
            notes='Driver feels dizzy'
        )
        url = reverse('alerts:alert-detail', kwargs={'alert_id': alert.id})

        # Owner access
        self._auth(self.customer, 'Pass1234!C')
        resp_owner = self.client.get(url)
        self.assertEqual(resp_owner.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_owner.json()['data']['notes'], 'Driver feels dizzy')

        # Operator access
        self._auth(self.operator, 'Pass1234!O')
        resp_ops = self.client.get(url)
        self.assertEqual(resp_ops.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_ops.json()['data']['location_address'], 'Connaught Place')


class TestOperatorAlertClaimWorkflow(TestCase):
    """
    Tests operator queue retrieval and claiming transitions (CONFIRMED -> ACTIVE).
    """

    def setUp(self):
        self.client = APIClient()
        self.token_url = reverse('accounts:token_obtain_pair')

        self.customer = create_user('cust_ops@fixpoint.io', 'Pass1234!C', role=UserRole.CUSTOMER)
        self.operator1 = create_user('op1@fixpoint.io', 'Pass1234!Op1', role=UserRole.OPERATOR)
        self.operator2 = create_user('op2@fixpoint.io', 'Pass1234!Op2', role=UserRole.OPERATOR)
        self.customer_unrelated = create_user('cust_unrelated@fixpoint.io', 'Pass1234!U', role=UserRole.CUSTOMER)

        self.badge = create_qr_badge(user=self.customer, vehicle_registration='MH-02-CB-5555')
        self.alert, raw_conf = create_alert_draft(qr_token=self.badge.raw_token)
        confirm_alert(self.alert.id, raw_conf)

    def _auth(self, user, password):
        resp = self.client.post(self.token_url, {'email': user.email, 'password': password})
        token = resp.json()['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_operator_can_view_alert_queue(self):
        """
        Operators can view the queue of confirmed alerts.
        """
        self._auth(self.operator1, 'Pass1234!Op1')
        url = reverse('operations:operations-alert-queue')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        alerts = resp.json()['data']
        self.assertTrue(any(a['id'] == str(self.alert.id) for a in alerts))

    def test_customer_cannot_view_operator_alert_queue(self):
        """
        Customers must receive HTTP 403 when trying to access the operator queue.
        """
        self._auth(self.customer_unrelated, 'Pass1234!U')
        url = reverse('operations:operations-alert-queue')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_operator_can_claim_confirmed_alert(self):
        """
        Operator claiming a CONFIRMED alert transitions it to ACTIVE with claimed_by recorded.
        """
        self._auth(self.operator1, 'Pass1234!Op1')
        url = reverse('operations:operations-alert-claim', kwargs={'alert_id': self.alert.id})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.alert.refresh_from_db()
        self.assertEqual(self.alert.status, AlertStatus.ACTIVE)
        self.assertEqual(self.alert.claimed_by, self.operator1)
        self.assertIsNotNone(self.alert.activated_at)

    def test_already_claimed_alert_cannot_be_reclaimed(self):
        """
        Claiming an alert that has already been claimed returns HTTP 409 Conflict.
        """
        # Operator 1 claims
        self._auth(self.operator1, 'Pass1234!Op1')
        url = reverse('operations:operations-alert-claim', kwargs={'alert_id': self.alert.id})
        self.client.post(url)

        # Operator 2 attempts to claim same alert
        self._auth(self.operator2, 'Pass1234!Op2')
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(resp.json()['error']['code'], 'already_claimed')

    def test_operator_alert_queue_filtering_by_status_and_severity(self):
        """
        Operator alert queue supports filtering by status and severity query parameters.
        """
        self._auth(self.operator1, 'Pass1234!Op1')
        url = reverse('operations:operations-alert-queue')

        # Filter by status CONFIRMED (matches self.alert)
        resp = self.client.get(f"{url}?status=CONFIRMED")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(any(a['id'] == str(self.alert.id) for a in resp.json()['data']))

        # Filter by status ACTIVE (does not match self.alert yet)
        resp = self.client.get(f"{url}?status=ACTIVE")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(any(a['id'] == str(self.alert.id) for a in resp.json()['data']))

        # Filter by severity CRITICAL
        resp = self.client.get(f"{url}?severity=CRITICAL")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(any(a['id'] == str(self.alert.id) for a in resp.json()['data']))

    def test_operator_can_add_internal_notes_to_alert(self):
        """
        Operators can append internal triage notes to an active alert.
        """
        self._auth(self.operator1, 'Pass1234!Op1')
        url = reverse('operations:operations-alert-notes', kwargs={'alert_id': self.alert.id})
        resp = self.client.post(url, {'notes': 'Driver contacted; confirmed no injuries, tow truck required'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.alert.refresh_from_db()
        self.assertIn('tow truck required', self.alert.notes)

    def test_customer_cannot_add_notes_to_alert(self):
        """
        Non-operators receive HTTP 403 when trying to add internal operational notes.
        """
        self._auth(self.customer_unrelated, 'Pass1234!U')
        url = reverse('operations:operations-alert-notes', kwargs={'alert_id': self.alert.id})
        resp = self.client.post(url, {'notes': 'Unauthorized note attempt'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class TestAlertClosureAndNotificationCancellation(TestCase):
    """
    Tests alert closure and requirement 12: pending workflow actions must stop.
    """

    def setUp(self):
        self.client = APIClient()
        self.token_url = reverse('accounts:token_obtain_pair')

        self.customer = create_user('close_cust@fixpoint.io', 'Pass1234!C', role=UserRole.CUSTOMER)
        self.operator = create_user('close_ops@fixpoint.io', 'Pass1234!O', role=UserRole.OPERATOR)
        self.unrelated = create_user('close_unrelated@fixpoint.io', 'Pass1234!U', role=UserRole.CUSTOMER)

        self.badge = create_qr_badge(user=self.customer, vehicle_registration='KA-03-MG-1111')
        self.contact = EmergencyContact.objects.create(
            user=self.customer,
            name='Primary Contact',
            relationship='Parent',
            phone_number='+919988776655'
        )

        self.alert, raw_conf = create_alert_draft(qr_token=self.badge.raw_token)
        confirm_alert(self.alert.id, raw_conf)

    def _auth(self, user, password):
        resp = self.client.post(self.token_url, {'email': user.email, 'password': password})
        token = resp.json()['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_operator_closing_alert_cancels_pending_queued_notifications(self):
        """
        Closing an alert cancels all QUEUED notifications linked to this alert.
        """
        # Verify notifications are currently QUEUED
        initial_queued_count = NotificationRecord.objects.filter(alert=self.alert, status=NotificationStatus.QUEUED).count()
        self.assertGreaterEqual(initial_queued_count, 1)

        # Operator closes alert
        self._auth(self.operator, 'Pass1234!O')
        url = reverse('alerts:alert-close', kwargs={'alert_id': self.alert.id})
        resp = self.client.post(url, {'reason': 'False alarm confirmed with vehicle driver'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.alert.refresh_from_db()
        self.assertEqual(self.alert.status, AlertStatus.CLOSED)
        self.assertIsNotNone(self.alert.closed_at)
        self.assertEqual(self.alert.closed_by, self.operator)

        # Verify all queued notifications were marked CANCELLED
        cancelled_notifications = NotificationRecord.objects.filter(
            alert=self.alert,
            status=NotificationStatus.CANCELLED
        )
        self.assertEqual(cancelled_notifications.count(), initial_queued_count)

    def test_unrelated_user_cannot_close_alert(self):
        """
        An unrelated customer receives HTTP 403 Forbidden when attempting to close an alert.
        """
        self._auth(self.unrelated, 'Pass1234!U')
        url = reverse('alerts:alert-close', kwargs={'alert_id': self.alert.id})
        resp = self.client.post(url, {'reason': 'Malicious closure'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_optional_evidence_can_be_attached(self):
        """
        Optional photo / evidence attachment metadata can be uploaded to an alert.
        """
        url = reverse('alerts:alert-evidence', kwargs={'alert_id': self.alert.id})
        resp = self.client.post(url, {
            'file_url': 'https://storage.fixpoint.io/evidence/scene_photo_01.jpg',
            'caption': 'Front bumper collision damage'
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        evidence = AlertEvidence.objects.filter(alert=self.alert).first()
        self.assertIsNotNone(evidence)
        self.assertEqual(evidence.caption, 'Front bumper collision damage')

    def test_alert_closure_cancels_multi_step_notification_chains(self):
        """
        Closing an alert immediately cancels ContactNotificationChain records and pending DeliveryAttempt records.
        """
        from apps.notifications.models import ContactNotificationChain, DeliveryAttempt, ChainStatus, AttemptStatus
        from apps.contacts.models import ConsentStatus

        # Create an emergency contact with GRANTED consent
        from apps.contacts.utils import compute_phone_hash
        contact = EmergencyContact.objects.create(
            user=self.customer,
            name='Closure Contact',
            relationship='Sibling',
            phone_number='+919876543299',
            phone_hash=compute_phone_hash('+919876543299'),
            consent_status=ConsentStatus.GRANTED,
        )
        chain = ContactNotificationChain.objects.create(
            alert=self.alert,
            contact=contact,
            status=ChainStatus.ACTIVE
        )
        attempt = DeliveryAttempt.objects.create(
            chain=chain,
            channel='WHATSAPP',
            status=AttemptStatus.PENDING,
            idempotency_key=f"closure_test_attempt_{chain.id}"
        )

        # Operator closes alert
        self._auth(self.operator, 'Pass1234!O')
        url = reverse('alerts:alert-close', kwargs={'alert_id': self.alert.id})
        resp = self.client.post(url, {'reason': 'Emergency resolved on scene'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        chain.refresh_from_db()
        self.assertEqual(chain.status, ChainStatus.CANCELLED)

        attempt.refresh_from_db()
        self.assertEqual(attempt.status, AttemptStatus.CANCELLED)

