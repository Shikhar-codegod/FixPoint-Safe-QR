"""
Security Hardening Test Suite — Phase 1
FixPoint Drive Safe-QR SOS Backend

Covers:
1. Incident Authorization & Status Transitions
   - Customer cannot change incident status
   - Unrelated customer cannot modify another user's incident
   - Unrelated customer cannot view another user's incident
   - Unassigned responder cannot modify an incident
   - Assigned verified responder can perform permitted actions (e.g. DISPATCHED -> IN_PROGRESS, IN_PROGRESS -> RESOLVED)
   - Assigned responder cannot close an incident (requires operator/supervisor)
   - Operator and supervisor can perform authorized actions
   - Invalid status transitions are rejected with HTTP 400
   - Arbitrary/disallowed fields in PATCH payload are rejected with HTTP 400

2. Responder Dispatch Access Control
   - Unverified police responder receives HTTP 403
   - Unverified medical responder receives HTTP 403
   - Verified responder sees only dispatches assigned to them
   - Verified responder receives HTTP 403 when accessing another responder's dispatch detail
   - Customer cannot access dispatch records (HTTP 403)
   - Operator/supervisor can view dispatches

3. Field-Level Encryption Configuration & Integrity
   - Missing encryption key causes ImproperlyConfigured
   - Invalid encryption key is rejected with ImproperlyConfigured
   - Valid configured key successfully encrypts and decrypts data
   - Existing encryption/decryption behavior remains compatible
"""

import pytest
from django.test import TestCase, override_settings
from django.urls import reverse
from django.core.exceptions import ImproperlyConfigured
from rest_framework.test import APIClient
from rest_framework import status
from cryptography.fernet import Fernet

from apps.accounts.models import CustomUser, UserRole
from apps.incidents.models import IncidentRecord, IncidentStatus, IncidentType
from apps.responders.models import ResponderDispatch, DispatchStatus
from apps.contacts.models import EmergencyContact
from apps.common.encryption import FieldEncryptionService


def create_user(email, password, role=UserRole.CUSTOMER, is_verified=False, **kwargs):
    return CustomUser.objects.create_user(
        email=email,
        password=password,
        role=role,
        is_verified_responder=is_verified,
        **kwargs
    )


class TestIncidentAuthorization(TestCase):
    """
    Tests incident permission boundaries, transition validation, and field-level update gating.
    """

    def setUp(self):
        self.client = APIClient()
        self.token_url = reverse('accounts:token_obtain_pair')

        # Users
        self.customer_owner = create_user('owner@fixpoint.io', 'Pass1234!Owner', role=UserRole.CUSTOMER)
        self.customer_other = create_user('other@fixpoint.io', 'Pass1234!Other', role=UserRole.CUSTOMER)
        self.operator = create_user('operator@fixpoint.io', 'Pass1234!Operator', role=UserRole.OPERATOR)
        self.supervisor = create_user('supervisor@fixpoint.io', 'Pass1234!Supervisor', role=UserRole.SUPERVISOR)

        self.responder_assigned = create_user(
            'assigned@fixpoint.io', 'Pass1234!Assigned',
            role=UserRole.POLICE_RESPONDER, is_verified=True
        )
        self.responder_unassigned = create_user(
            'unassigned@fixpoint.io', 'Pass1234!Unassigned',
            role=UserRole.POLICE_RESPONDER, is_verified=True
        )
        self.responder_unverified = create_user(
            'unverified@fixpoint.io', 'Pass1234!Unverified',
            role=UserRole.POLICE_RESPONDER, is_verified=False
        )

        # Baseline incident created by customer_owner
        self.incident = IncidentRecord.objects.create(
            incident_number='INC-TEST-0001',
            incident_type=IncidentType.ROAD_ACCIDENT,
            status=IncidentStatus.REPORTED,
            reporter=self.customer_owner,
            description="Two-vehicle collision at junction."
        )

        # Assign responder_assigned to this incident
        self.dispatch = ResponderDispatch.objects.create(
            responder=self.responder_assigned,
            incident=self.incident,
            status=DispatchStatus.ASSIGNED
        )

    def _auth(self, user, password='Pass1234!Owner'):
        resp = self.client.post(self.token_url, {'email': user.email, 'password': password})
        token = resp.json()['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_customer_cannot_change_incident_status(self):
        """Customers must receive 403 when attempting to PATCH incident status, even on their own incident."""
        self._auth(self.customer_owner, 'Pass1234!Owner')
        url = reverse('incidents:incident-detail', kwargs={'incident_number': self.incident.incident_number})
        resp = self.client.patch(url, {'status': IncidentStatus.DISPATCHED})
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.json()['error']['code'] == 'permission_denied'

        self.incident.refresh_from_db()
        assert self.incident.status == IncidentStatus.REPORTED

    def test_unrelated_customer_cannot_modify_another_users_incident(self):
        """An unrelated customer must receive 403 when attempting to modify another user's incident."""
        self._auth(self.customer_other, 'Pass1234!Other')
        url = reverse('incidents:incident-detail', kwargs={'incident_number': self.incident.incident_number})
        resp = self.client.patch(url, {'status': IncidentStatus.DISPATCHED})
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_unrelated_customer_cannot_view_another_users_incident(self):
        """An unrelated customer must receive 403 when attempting to view another user's incident."""
        self._auth(self.customer_other, 'Pass1234!Other')
        url = reverse('incidents:incident-detail', kwargs={'incident_number': self.incident.incident_number})
        resp = self.client.get(url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_reporter_can_view_own_incident(self):
        """The reporting customer can view their own incident details."""
        self._auth(self.customer_owner, 'Pass1234!Owner')
        url = reverse('incidents:incident-detail', kwargs={'incident_number': self.incident.incident_number})
        resp = self.client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()['data']['incident_number'] == self.incident.incident_number

    def test_unassigned_responder_cannot_modify_incident(self):
        """A verified responder who is NOT assigned to the incident receives 403 Forbidden."""
        self._auth(self.responder_unassigned, 'Pass1234!Unassigned')
        url = reverse('incidents:incident-detail', kwargs={'incident_number': self.incident.incident_number})
        resp = self.client.patch(url, {'status': IncidentStatus.IN_PROGRESS})
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert 'actively assigned' in resp.json()['error']['message']

    def test_unverified_responder_cannot_modify_incident(self):
        """An unverified responder receives 403 Forbidden even if assigned."""
        ResponderDispatch.objects.create(
            responder=self.responder_unverified,
            incident=self.incident,
            status=DispatchStatus.ASSIGNED
        )
        self._auth(self.responder_unverified, 'Pass1234!Unverified')
        url = reverse('incidents:incident-detail', kwargs={'incident_number': self.incident.incident_number})
        resp = self.client.patch(url, {'status': IncidentStatus.IN_PROGRESS})
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert 'Unverified responders' in resp.json()['error']['message']

    def test_assigned_verified_responder_can_perform_permitted_status_update(self):
        """An assigned verified responder can update an incident from DISPATCHED to IN_PROGRESS."""
        # Set to DISPATCHED first
        self.incident.status = IncidentStatus.DISPATCHED
        self.incident.save()

        self._auth(self.responder_assigned, 'Pass1234!Assigned')
        url = reverse('incidents:incident-detail', kwargs={'incident_number': self.incident.incident_number})
        resp = self.client.patch(url, {'status': IncidentStatus.IN_PROGRESS})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()['data']['status'] == IncidentStatus.IN_PROGRESS

        self.incident.refresh_from_db()
        assert self.incident.status == IncidentStatus.IN_PROGRESS

    def test_responder_cannot_close_incident(self):
        """Responders are not permitted to close an incident; closure requires operator/supervisor."""
        self.incident.status = IncidentStatus.IN_PROGRESS
        self.incident.save()

        self._auth(self.responder_assigned, 'Pass1234!Assigned')
        url = reverse('incidents:incident-detail', kwargs={'incident_number': self.incident.incident_number})
        resp = self.client.patch(url, {'status': IncidentStatus.CLOSED})
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert 'not permitted to close incidents' in resp.json()['error']['message']

    def test_operator_can_perform_authorized_status_update(self):
        """Operators can update incident status through permitted transitions."""
        self._auth(self.operator, 'Pass1234!Operator')
        url = reverse('incidents:incident-detail', kwargs={'incident_number': self.incident.incident_number})
        resp = self.client.patch(url, {'status': IncidentStatus.DISPATCHED})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()['data']['status'] == IncidentStatus.DISPATCHED

    def test_supervisor_can_close_incident(self):
        """Supervisors can transition an in-progress incident to CLOSED."""
        self.incident.status = IncidentStatus.IN_PROGRESS
        self.incident.save()

        self._auth(self.supervisor, 'Pass1234!Supervisor')
        url = reverse('incidents:incident-detail', kwargs={'incident_number': self.incident.incident_number})
        resp = self.client.patch(url, {'status': IncidentStatus.CLOSED})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()['data']['status'] == IncidentStatus.CLOSED

    def test_invalid_status_transition_is_rejected(self):
        """Transition from REPORTED directly to RESOLVED without dispatch is rejected with 400 Bad Request."""
        self._auth(self.operator, 'Pass1234!Operator')
        url = reverse('incidents:incident-detail', kwargs={'incident_number': self.incident.incident_number})
        resp = self.client.patch(url, {'status': IncidentStatus.RESOLVED})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Invalid status transition' in resp.json()['error']['message']

    def test_closed_incident_cannot_transition_back_to_reported(self):
        """A CLOSED incident is terminal and cannot transition back to REPORTED."""
        self.incident.status = IncidentStatus.CLOSED
        self.incident.save()

        self._auth(self.operator, 'Pass1234!Operator')
        url = reverse('incidents:incident-detail', kwargs={'incident_number': self.incident.incident_number})
        resp = self.client.patch(url, {'status': IncidentStatus.REPORTED})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_disallowed_fields_in_patch_are_rejected(self):
        """Supplying immutable or unauthorized fields (e.g. incident_number, reporter) returns 400 Bad Request."""
        self._auth(self.operator, 'Pass1234!Operator')
        url = reverse('incidents:incident-detail', kwargs={'incident_number': self.incident.incident_number})
        resp = self.client.patch(url, {
            'status': IncidentStatus.DISPATCHED,
            'incident_number': 'HACKED-NUMBER',
            'reporter': str(self.operator.id)
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Fields not permitted for modification' in resp.json()['error']['message']


class TestResponderDispatchAccess(TestCase):
    """
    Tests responder dispatch access rules, verification gates, and object-level authorization.
    """

    def setUp(self):
        self.client = APIClient()
        self.token_url = reverse('accounts:token_obtain_pair')

        self.customer = create_user('cust@fixpoint.io', 'Pass1234!Cust', role=UserRole.CUSTOMER)
        self.operator = create_user('ops@fixpoint.io', 'Pass1234!Ops', role=UserRole.OPERATOR)

        # Responders
        self.police_unverified = create_user(
            'police_unverified@fixpoint.io', 'Pass1234!P1',
            role=UserRole.POLICE_RESPONDER, is_verified=False
        )
        self.medical_unverified = create_user(
            'med_unverified@fixpoint.io', 'Pass1234!M1',
            role=UserRole.MEDICAL_RESPONDER, is_verified=False
        )
        self.police_verified = create_user(
            'police_verified@fixpoint.io', 'Pass1234!P2',
            role=UserRole.POLICE_RESPONDER, is_verified=True
        )
        self.police_other_verified = create_user(
            'police_other@fixpoint.io', 'Pass1234!P3',
            role=UserRole.POLICE_RESPONDER, is_verified=True
        )

        # Incidents
        self.incident_a = IncidentRecord.objects.create(
            incident_number='INC-DISP-001',
            incident_type=IncidentType.ROAD_ACCIDENT,
            status=IncidentStatus.DISPATCHED,
            reporter=self.customer
        )
        self.incident_b = IncidentRecord.objects.create(
            incident_number='INC-DISP-002',
            incident_type=IncidentType.MEDICAL_EMERGENCY,
            status=IncidentStatus.DISPATCHED,
            reporter=self.customer
        )

        # Dispatches
        self.dispatch_a = ResponderDispatch.objects.create(
            responder=self.police_verified,
            incident=self.incident_a,
            status=DispatchStatus.ASSIGNED
        )
        self.dispatch_b = ResponderDispatch.objects.create(
            responder=self.police_other_verified,
            incident=self.incident_b,
            status=DispatchStatus.ASSIGNED
        )

    def _auth(self, user, password):
        resp = self.client.post(self.token_url, {'email': user.email, 'password': password})
        token = resp.json()['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_unverified_police_responder_receives_403(self):
        """Unverified police responder must receive HTTP 403 Forbidden."""
        self._auth(self.police_unverified, 'Pass1234!P1')
        resp = self.client.get(reverse('responders:responder-dispatches'))
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_unverified_medical_responder_receives_403(self):
        """Unverified medical responder must receive HTTP 403 Forbidden."""
        self._auth(self.medical_unverified, 'Pass1234!M1')
        resp = self.client.get(reverse('responders:responder-dispatches'))
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_customer_cannot_access_dispatch_records(self):
        """Customers must receive HTTP 403 Forbidden when attempting to access responder dispatches."""
        self._auth(self.customer, 'Pass1234!Cust')
        resp = self.client.get(reverse('responders:responder-dispatches'))
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_verified_responder_sees_only_assigned_dispatches(self):
        """A verified responder's dispatch list contains only dispatches assigned directly to them."""
        self._auth(self.police_verified, 'Pass1234!P2')
        resp = self.client.get(reverse('responders:responder-dispatches'))
        assert resp.status_code == status.HTTP_200_OK

        dispatches = resp.json()['data']
        assert len(dispatches) == 1
        assert dispatches[0]['id'] == str(self.dispatch_a.id)

    def test_verified_responder_cannot_access_another_responders_dispatch_detail(self):
        """Object-level check: A verified responder receives 403 when trying to access another responder's dispatch."""
        self._auth(self.police_verified, 'Pass1234!P2')
        url = reverse('responders:responder-dispatch-detail', kwargs={'dispatch_id': self.dispatch_b.id})
        resp = self.client.get(url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_verified_responder_can_access_own_dispatch_detail(self):
        """A verified responder can view details of their own assigned dispatch."""
        self._auth(self.police_verified, 'Pass1234!P2')
        url = reverse('responders:responder-dispatch-detail', kwargs={'dispatch_id': self.dispatch_a.id})
        resp = self.client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()['data']['id'] == str(self.dispatch_a.id)

    def test_operator_can_view_all_dispatches(self):
        """Operators can view the full dispatch list."""
        self._auth(self.operator, 'Pass1234!Ops')
        resp = self.client.get(reverse('responders:responder-dispatches'))
        assert resp.status_code == status.HTTP_200_OK
        dispatches = resp.json()['data']
        assert len(dispatches) >= 2


class TestFieldLevelEncryptionConfiguration(TestCase):
    """
    Tests encryption configuration validation, missing key handling, and data encryption/decryption compatibility.
    """

    def setUp(self):
        FieldEncryptionService.reset_cipher()
        self.valid_key = '-dH3bVNkLyz65qi4aCC9qxXJaUpe1947ZbGFpIM0E3s='

    def tearDown(self):
        FieldEncryptionService.reset_cipher()

    def test_missing_encryption_key_causes_improperly_configured(self):
        """When FIELD_ENCRYPTION_KEY is empty or missing, using cipher raises ImproperlyConfigured."""
        with override_settings(FIELD_ENCRYPTION_KEY=''):
            FieldEncryptionService.reset_cipher()
            with pytest.raises(ImproperlyConfigured) as exc_info:
                FieldEncryptionService.get_cipher()
            assert "FIELD_ENCRYPTION_KEY setting is required" in str(exc_info.value)

    def test_invalid_encryption_key_is_rejected(self):
        """An invalid Fernet key format raises ImproperlyConfigured without echoing the key in error."""
        with override_settings(FIELD_ENCRYPTION_KEY='not-a-valid-fernet-key-value'):
            FieldEncryptionService.reset_cipher()
            with pytest.raises(ImproperlyConfigured) as exc_info:
                FieldEncryptionService.get_cipher()
            assert "Invalid FIELD_ENCRYPTION_KEY format" in str(exc_info.value)
            # Verify the bad key is NOT leaked in the error message
            assert 'not-a-valid-fernet-key-value' not in str(exc_info.value)

    def test_valid_key_encrypts_and_decrypts_data(self):
        """A valid Fernet key properly encrypts plaintext and decrypts ciphertext back to original string."""
        with override_settings(FIELD_ENCRYPTION_KEY=self.valid_key):
            FieldEncryptionService.reset_cipher()
            plaintext = "+1 (555) 019-2834"
            ciphertext = FieldEncryptionService.encrypt(plaintext)
            assert ciphertext != plaintext
            assert ciphertext.startswith('gAAAAA')

            decrypted = FieldEncryptionService.decrypt(ciphertext)
            assert decrypted == plaintext

    def test_existing_encrypted_model_data_remains_compatible(self):
        """Model with EncryptedCharField encrypts at rest and decrypts on model load."""
        with override_settings(FIELD_ENCRYPTION_KEY=self.valid_key):
            FieldEncryptionService.reset_cipher()
            user = create_user('enc_test@fixpoint.io', 'Pass1234!Enc')
            contact = EmergencyContact.objects.create(
                user=user,
                name="Jane Doe",
                relationship="Spouse",
                phone_number="+1 555 999 8888",
                email="jane@example.com"
            )

            # Reload from DB
            loaded = EmergencyContact.objects.get(id=contact.id)
            assert loaded.phone_number == "+1 555 999 8888"
            assert loaded.email == "jane@example.com"



class TestPhase1Corrections(TestCase):
    """
    Regression tests for Phase 1 correction review.

    Covers:
    1. Unverified responder cannot GET an incident even when a dispatch record exists.
    2. Verified assigned responder can GET an authorized incident.
    3. Unassigned verified responder cannot GET an incident.
    4. Responder with a COMPLETED (inactive) assignment cannot access the incident.
    5. Responder with a CANCELLED (inactive) assignment cannot access the incident.
    6. Invalid dispatch status transition is rejected with HTTP 400.
    7. Completed dispatch cannot transition backwards (terminal state).
    8. Incident description modification creates an audit event.
    9. Operator access to incident GET continues to work.
    10. Supervisor access to incident PATCH continues to work.
    """

    def setUp(self):
        self.client = APIClient()
        self.token_url = reverse('accounts:token_obtain_pair')

        self.customer = create_user('corr_cust@fixpoint.io', 'Pass1234!C', role=UserRole.CUSTOMER)
        self.operator = create_user('corr_ops@fixpoint.io', 'Pass1234!O', role=UserRole.OPERATOR)
        self.supervisor = create_user('corr_sup@fixpoint.io', 'Pass1234!S', role=UserRole.SUPERVISOR)

        self.verified_responder = create_user(
            'corr_verified@fixpoint.io', 'Pass1234!V',
            role=UserRole.POLICE_RESPONDER, is_verified=True
        )
        self.unverified_responder = create_user(
            'corr_unverified@fixpoint.io', 'Pass1234!U',
            role=UserRole.POLICE_RESPONDER, is_verified=False
        )
        self.other_verified_responder = create_user(
            'corr_other@fixpoint.io', 'Pass1234!OV',
            role=UserRole.POLICE_RESPONDER, is_verified=True
        )

        self.incident = IncidentRecord.objects.create(
            incident_number='INC-CORR-0001',
            incident_type=IncidentType.ROAD_ACCIDENT,
            status=IncidentStatus.DISPATCHED,
            reporter=self.customer,
            description='Original description.'
        )

        # Active dispatch for verified_responder
        self.active_dispatch = ResponderDispatch.objects.create(
            responder=self.verified_responder,
            incident=self.incident,
            status=DispatchStatus.ASSIGNED
        )

    def _auth(self, user, password):
        resp = self.client.post(self.token_url, {'email': user.email, 'password': password})
        assert resp.status_code == 200, f"Auth failed for {user.email}: {resp.json()}"
        token = resp.json()['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def _incident_url(self):
        return reverse('incidents:incident-detail', kwargs={'incident_number': self.incident.incident_number})

    def _dispatch_detail_url(self, dispatch):
        return reverse('responders:responder-dispatch-detail', kwargs={'dispatch_id': dispatch.id})

    # ── Task 1 / Task 2 ────────────────────────────────────────────────────────

    def test_unverified_responder_cannot_get_incident_even_with_dispatch(self):
        """
        An unverified responder with an existing dispatch record must still receive
        HTTP 403 on GET. Verification check precedes assignment check.
        """
        # Give unverified responder a dispatch record (should NOT grant access)
        ResponderDispatch.objects.create(
            responder=self.unverified_responder,
            incident=self.incident,
            status=DispatchStatus.ASSIGNED
        )
        self._auth(self.unverified_responder, 'Pass1234!U')
        resp = self.client.get(self._incident_url())
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.json()['error']['code'] == 'permission_denied'
        assert 'Unverified' in resp.json()['error']['message']

    def test_verified_assigned_responder_can_get_incident(self):
        """
        A verified responder with an active (ASSIGNED) dispatch may GET the incident.
        """
        self._auth(self.verified_responder, 'Pass1234!V')
        resp = self.client.get(self._incident_url())
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()['data']['incident_number'] == self.incident.incident_number

    def test_unassigned_verified_responder_cannot_get_incident(self):
        """
        A verified responder with no dispatch record for this incident is denied.
        """
        self._auth(self.other_verified_responder, 'Pass1234!OV')
        resp = self.client.get(self._incident_url())
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.json()['error']['code'] == 'permission_denied'

    def test_responder_with_completed_assignment_cannot_get_incident(self):
        """
        Once a dispatch reaches COMPLETED (a terminal, inactive status), the responder
        must no longer access the incident via GET.
        """
        self.active_dispatch.status = DispatchStatus.COMPLETED
        self.active_dispatch.save(update_fields=['status', 'updated_at'])

        self._auth(self.verified_responder, 'Pass1234!V')
        resp = self.client.get(self._incident_url())
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_responder_with_cancelled_assignment_cannot_get_incident(self):
        """
        A CANCELLED dispatch is also inactive and must not grant incident access.
        """
        self.active_dispatch.status = DispatchStatus.CANCELLED
        self.active_dispatch.save(update_fields=['status', 'updated_at'])

        self._auth(self.verified_responder, 'Pass1234!V')
        resp = self.client.get(self._incident_url())
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    # ── Task 3 ─────────────────────────────────────────────────────────────────

    def test_invalid_dispatch_status_transition_is_rejected(self):
        """
        Attempting an invalid dispatch transition (e.g. ASSIGNED → COMPLETED, which skips
        EN_ROUTE and ON_SCENE) must return HTTP 400 with code 'invalid_transition'.
        """
        self._auth(self.operator, 'Pass1234!O')
        url = self._dispatch_detail_url(self.active_dispatch)
        # ASSIGNED → COMPLETED is not permitted; must go ASSIGNED → EN_ROUTE → ON_SCENE → COMPLETED
        resp = self.client.patch(url, {'status': DispatchStatus.COMPLETED}, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert resp.json()['error']['code'] == 'invalid_transition'
        assert 'Invalid dispatch status transition' in resp.json()['error']['message']

    def test_completed_dispatch_cannot_transition_backwards(self):
        """
        A COMPLETED dispatch is terminal. Any further status change must return HTTP 400.
        """
        self.active_dispatch.status = DispatchStatus.COMPLETED
        self.active_dispatch.save(update_fields=['status', 'updated_at'])

        self._auth(self.operator, 'Pass1234!O')
        url = self._dispatch_detail_url(self.active_dispatch)
        resp = self.client.patch(url, {'status': DispatchStatus.ASSIGNED}, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert resp.json()['error']['code'] == 'invalid_transition'

    # ── Task 4 ─────────────────────────────────────────────────────────────────

    def test_incident_description_change_creates_audit_event(self):
        """
        Patching an incident's description must persist an INCIDENT_DESCRIPTION_CHANGED
        audit event. The event payload must not contain the description text itself.
        """
        from apps.audit.models import AuditEvent

        self._auth(self.operator, 'Pass1234!O')
        new_description = 'Updated: three-vehicle collision, road blocked.'
        resp = self.client.patch(
            self._incident_url(),
            {'description': new_description},
            format='json'
        )
        assert resp.status_code == status.HTTP_200_OK

        event = AuditEvent.objects.filter(
            action='INCIDENT_DESCRIPTION_CHANGED',
            target_id=str(self.incident.id)
        ).order_by('-timestamp').first()

        assert event is not None, "Expected INCIDENT_DESCRIPTION_CHANGED audit event was not created."
        assert event.payload.get('description_changed') is True
        # Description content must NOT appear in the audit payload (privacy)
        assert new_description not in str(event.payload)
        assert 'Original description.' not in str(event.payload)

    # ── Regression: existing operator/supervisor permissions still work ─────────

    def test_operator_can_still_get_any_incident(self):
        """Operator access to incident detail (GET) is preserved after corrections."""
        self._auth(self.operator, 'Pass1234!O')
        resp = self.client.get(self._incident_url())
        assert resp.status_code == status.HTTP_200_OK

    def test_supervisor_can_still_close_incident(self):
        """Supervisor ability to close an in-progress incident is preserved."""
        self.incident.status = IncidentStatus.IN_PROGRESS
        self.incident.save()

        self._auth(self.supervisor, 'Pass1234!S')
        resp = self.client.patch(self._incident_url(), {'status': IncidentStatus.CLOSED}, format='json')
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()['data']['status'] == IncidentStatus.CLOSED
