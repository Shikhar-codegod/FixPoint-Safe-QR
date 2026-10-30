import uuid
import pytest
from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import CustomUser, UserRole
from apps.contacts.models import EmergencyContact, ConsentStatus
from apps.contacts.utils import normalize_phone_number, compute_phone_hash
from apps.alerts.models import AlertRecord, AlertStatus, AlertSeverity
from apps.notifications.models import ContactNotificationChain, ChainStatus
from apps.audit.models import AuditEvent

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def customer_user(db):
    return CustomUser.objects.create_user(
        email='cust1@fixpoint.io',
        password='TestPassword!123',
        first_name='Aarav',
        last_name='Sharma',
        role=UserRole.CUSTOMER
    )

@pytest.fixture
def other_customer(db):
    return CustomUser.objects.create_user(
        email='cust2@fixpoint.io',
        password='TestPassword!123',
        first_name='Priya',
        last_name='Patel',
        role=UserRole.CUSTOMER
    )

@pytest.fixture
def auth_client(customer_user):
    client = APIClient()
    client.force_authenticate(user=customer_user)
    return client

@pytest.fixture
def other_auth_client(other_customer):
    client = APIClient()
    client.force_authenticate(user=other_customer)
    return client

@pytest.mark.django_db
class TestEmergencyContactCRUD:
    def test_create_and_list_contact(self, auth_client, customer_user):
        url = reverse('contacts:contacts-list-create')
        payload = {
            'name': 'Rohan Sharma',
            'relationship': 'Brother',
            'phone_number': '9876543210',  # 10-digit Indian mobile
            'email': 'rohan@example.com',
            'priority_order': 1,
            'is_primary': True,
            'preferred_language': 'en',
            'notify_whatsapp': True,
            'notify_sms': True,
            'notify_call': True,
        }
        res = auth_client.post(url, payload)
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()['data']
        assert data['name'] == 'Rohan Sharma'
        assert data['relationship'] == 'Brother'
        assert data['phone_number'] == '+919876543210'  # Normalised to E.164
        assert data['consent_status'] == ConsentStatus.PENDING
        assert 'phone_hash' not in data

        # List contacts
        list_res = auth_client.get(url)
        assert list_res.status_code == status.HTTP_200_OK
        assert len(list_res.json()['data']) == 1

    def test_retrieve_and_update_contact(self, auth_client, customer_user):
        contact = EmergencyContact.objects.create(
            user=customer_user,
            name='Original Name',
            relationship='Friend',
            phone_number='+919876543210',
            phone_hash=compute_phone_hash('+919876543210')
        )
        url = reverse('contacts:contact-detail', kwargs={'contact_id': contact.id})

        # GET detail
        get_res = auth_client.get(url)
        assert get_res.status_code == status.HTTP_200_OK
        assert get_res.json()['data']['name'] == 'Original Name'

        # PATCH update
        patch_res = auth_client.patch(url, {'name': 'Updated Name', 'relationship': 'Spouse'})
        assert patch_res.status_code == status.HTTP_200_OK
        assert patch_res.json()['data']['name'] == 'Updated Name'
        assert patch_res.json()['data']['relationship'] == 'Spouse'

        # PUT update
        put_payload = {
            'name': 'Full Updated Name',
            'relationship': 'Parent',
            'phone_number': '+919876543211',
            'email': 'parent@example.com',
            'priority_order': 2,
            'is_primary': False,
            'preferred_language': 'hi',
            'notify_whatsapp': False,
            'notify_sms': True,
            'notify_call': True,
        }
        put_res = auth_client.put(url, put_payload)
        assert put_res.status_code == status.HTTP_200_OK
        assert put_res.json()['data']['preferred_language'] == 'hi'
        assert put_res.json()['data']['notify_whatsapp'] is False

    def test_delete_contact(self, auth_client, customer_user):
        contact = EmergencyContact.objects.create(
            user=customer_user,
            name='To Delete',
            relationship='Colleague',
            phone_number='+919876543210',
            phone_hash=compute_phone_hash('+919876543210')
        )
        url = reverse('contacts:contact-detail', kwargs={'contact_id': contact.id})
        del_res = auth_client.delete(url)
        assert del_res.status_code == status.HTTP_200_OK
        assert not EmergencyContact.objects.filter(id=contact.id).exists()

    def test_ownership_isolation(self, auth_client, other_auth_client, customer_user, other_customer):
        """User A cannot view, update, or delete User B's contacts (must return 404)."""
        contact = EmergencyContact.objects.create(
            user=customer_user,
            name='User A Contact',
            relationship='Father',
            phone_number='+919876543210',
            phone_hash=compute_phone_hash('+919876543210')
        )
        url = reverse('contacts:contact-detail', kwargs={'contact_id': contact.id})

        # Other user attempts GET
        assert other_auth_client.get(url).status_code == status.HTTP_404_NOT_FOUND
        # Other user attempts PATCH
        assert other_auth_client.patch(url, {'name': 'Hacked'}).status_code == status.HTTP_404_NOT_FOUND
        # Other user attempts DELETE
        assert other_auth_client.delete(url).status_code == status.HTTP_404_NOT_FOUND
        # Contact still exists untouched
        assert EmergencyContact.objects.filter(id=contact.id).exists()

    def test_max_five_contacts_enforced(self, auth_client, customer_user):
        url = reverse('contacts:contacts-list-create')
        for i in range(5):
            res = auth_client.post(url, {
                'name': f'Contact {i}',
                'relationship': 'Family',
                'phone_number': f'987654321{i}'
            })
            assert res.status_code == status.HTTP_201_CREATED

        # 6th contact must be rejected
        res6 = auth_client.post(url, {
            'name': 'Contact 6',
            'relationship': 'Family',
            'phone_number': '9876543299'
        })
        assert res6.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Maximum 5 emergency contacts' in str(res6.json())

    def test_duplicate_phone_rejected_for_same_user(self, auth_client, other_auth_client, customer_user):
        url = reverse('contacts:contacts-list-create')
        # Add first contact
        res1 = auth_client.post(url, {
            'name': 'Contact One',
            'relationship': 'Sister',
            'phone_number': '9876543210'
        })
        assert res1.status_code == status.HTTP_201_CREATED

        # Attempt to add same phone with different formatting (e.g. +91 98765-43210)
        res2 = auth_client.post(url, {
            'name': 'Contact Two',
            'relationship': 'Sister',
            'phone_number': '+91 98765-43210'
        })
        assert res2.status_code == status.HTTP_400_BAD_REQUEST
        assert 'already exists' in str(res2.json())

        # Different user adding the same phone number succeeds
        res_other = other_auth_client.post(url, {
            'name': 'Other User Contact',
            'relationship': 'Mother',
            'phone_number': '9876543210'
        })
        assert res_other.status_code == status.HTTP_201_CREATED

    def test_invalid_phone_rejected(self, auth_client):
        url = reverse('contacts:contacts-list-create')
        for bad_phone in ['123', 'abcdef', '0000000', '+0000']:
            res = auth_client.post(url, {
                'name': 'Bad Phone Contact',
                'relationship': 'Friend',
                'phone_number': bad_phone
            })
            assert res.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
class TestConsentFlow:
    def test_consent_request_and_public_acceptance(self, auth_client, api_client, customer_user):
        contact = EmergencyContact.objects.create(
            user=customer_user,
            name='Rahul Verma',
            relationship='Uncle',
            phone_number='+919876543210',
            phone_hash=compute_phone_hash('+919876543210')
        )
        req_url = reverse('contacts:contact-consent-request', kwargs={'contact_id': contact.id})
        res = auth_client.post(req_url)
        assert res.status_code == status.HTTP_200_OK
        data = res.json()['data']
        assert 'debug_raw_token' in data
        token = data['debug_raw_token']

        # Verify only hash was stored in DB, not raw token
        contact.refresh_from_db()
        assert contact.consent_token_hash != token
        assert len(contact.consent_token_hash) == 64
        assert contact.consent_token_expires_at is not None

        # Public GET: shows first name only; does not change state
        public_url = reverse('contacts:public-contact-consent', kwargs={'token': token})
        info_res = api_client.get(public_url)
        assert info_res.status_code == status.HTTP_200_OK
        info_data = info_res.json()['data']
        assert info_data['requester_first_name'] == 'Aarav'
        assert 'phone' not in info_data
        assert 'email' not in info_data

        # State should still be PENDING after GET
        contact.refresh_from_db()
        assert contact.consent_status == ConsentStatus.PENDING

        # Public POST: accept decision
        dec_res = api_client.post(public_url, {'decision': 'accept'})
        assert dec_res.status_code == status.HTTP_200_OK
        contact.refresh_from_db()
        assert contact.consent_status == ConsentStatus.GRANTED
        assert contact.consent_given_at is not None

        # Reusing token must fail (single-use)
        reuse_res = api_client.post(public_url, {'decision': 'accept'})
        assert reuse_res.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]

    def test_consent_decline(self, auth_client, api_client, customer_user):
        contact = EmergencyContact.objects.create(
            user=customer_user,
            name='Kavita',
            relationship='Aunt',
            phone_number='+919876543210',
            phone_hash=compute_phone_hash('+919876543210')
        )
        req_url = reverse('contacts:contact-consent-request', kwargs={'contact_id': contact.id})
        res = auth_client.post(req_url)
        token = res.json()['data']['debug_raw_token']

        public_url = reverse('contacts:public-contact-consent', kwargs={'token': token})
        dec_res = api_client.post(public_url, {'decision': 'decline'})
        assert dec_res.status_code == status.HTTP_200_OK
        contact.refresh_from_db()
        assert contact.consent_status == ConsentStatus.DECLINED

    def test_consent_expired_token_rejected(self, api_client, customer_user):
        import hashlib
        expired_token = 'expired_token_xyz_1234567890123456'
        token_hash = hashlib.sha256(expired_token.encode('utf-8')).hexdigest()
        contact = EmergencyContact.objects.create(
            user=customer_user,
            name='Late Contact',
            relationship='Friend',
            phone_number='+919876543210',
            phone_hash=compute_phone_hash('+919876543210'),
            consent_token_hash=token_hash,
            consent_token_expires_at=timezone.now() - timedelta(days=1)
        )
        public_url = reverse('contacts:public-contact-consent', kwargs={'token': expired_token})
        assert api_client.get(public_url).status_code == status.HTTP_404_NOT_FOUND
        assert api_client.post(public_url, {'decision': 'accept'}).status_code == status.HTTP_400_BAD_REQUEST

    def test_consent_withdraw_cancels_active_chain(self, auth_client, customer_user):
        contact = EmergencyContact.objects.create(
            user=customer_user,
            name='Active Contact',
            relationship='Spouse',
            phone_number='+919876543210',
            phone_hash=compute_phone_hash('+919876543210'),
            consent_status=ConsentStatus.GRANTED,
            consent_given_at=timezone.now()
        )
        alert = AlertRecord.objects.create(
            user=customer_user,
            status=AlertStatus.TRIGGERED,
            severity=AlertSeverity.CRITICAL
        )
        chain = ContactNotificationChain.objects.create(
            alert=alert,
            contact=contact,
            status=ChainStatus.ACTIVE
        )

        withdraw_url = reverse('contacts:contact-consent-withdraw', kwargs={'contact_id': contact.id})
        res = auth_client.post(withdraw_url)
        assert res.status_code == status.HTTP_200_OK
        contact.refresh_from_db()
        assert contact.consent_status == ConsentStatus.WITHDRAWN
        assert contact.consent_withdrawn_at is not None

        # Chain must be CANCELLED
        chain.refresh_from_db()
        assert chain.status == ChainStatus.CANCELLED

    def test_audit_logs_do_not_contain_phone_numbers(self, auth_client, customer_user):
        url = reverse('contacts:contacts-list-create')
        auth_client.post(url, {
            'name': 'Secret Phone Contact',
            'relationship': 'Family',
            'phone_number': '9876543210'
        })
        # Check audit event payloads
        events = AuditEvent.objects.filter(actor=customer_user)
        for ev in events:
            payload_str = str(ev.payload)
            assert '9876543210' not in payload_str
            assert '+919876543210' not in payload_str
