import hmac
import hashlib
from datetime import timedelta
import pytest
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import CustomUser, UserRole
from apps.contacts.models import EmergencyContact, ConsentStatus
from apps.contacts.utils import compute_phone_hash
from apps.alerts.models import AlertRecord, AlertStatus, AlertSeverity
from apps.notifications.models import (
    NotificationRecord,
    ContactNotificationChain,
    ChainStatus,
    ChainStep,
    DeliveryAttempt,
    AttemptStatus,
)
from apps.notifications.services import (
    start_contact_chains_for_alert,
    process_chain,
    process_due_chains,
    acknowledge_chain_by_token,
    process_mock_webhook,
)
from apps.audit.models import AuditEvent

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user_with_contacts(db):
    user = CustomUser.objects.create_user(
        email='sos_victim@fixpoint.io',
        password='TestPassword!123',
        first_name='Vikram',
        last_name='Nair',
        role=UserRole.CUSTOMER
    )
    # Contact 1: GRANTED consent
    c1 = EmergencyContact.objects.create(
        user=user,
        name='Asha Nair',
        relationship='Spouse',
        phone_number='+919876543210',
        phone_hash=compute_phone_hash('+919876543210'),
        consent_status=ConsentStatus.GRANTED,
        consent_given_at=timezone.now(),
        notify_whatsapp=True,
        notify_sms=True,
        notify_call=True
    )
    # Contact 2: PENDING consent (must NOT be notified)
    c2 = EmergencyContact.objects.create(
        user=user,
        name='Rajesh Nair',
        relationship='Father',
        phone_number='+919876543212',
        phone_hash=compute_phone_hash('+919876543212'),
        consent_status=ConsentStatus.PENDING,
    )
    return user, c1, c2

@pytest.mark.django_db
class TestNotificationWorkflow:
    def test_provider_status_endpoint(self, api_client):
        url = reverse('notifications:provider-status')
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        data = res.json()['data']
        assert data['mode'] == 'mock'
        assert data['whatsapp_real_configured'] is False
        assert data['sms_real_configured'] is False
        assert data['voice_real_configured'] is False

    def test_only_granted_contacts_notified(self, user_with_contacts):
        user, c1_granted, c2_pending = user_with_contacts
        alert = AlertRecord.objects.create(
            user=user,
            status=AlertStatus.TRIGGERED,
            severity=AlertSeverity.CRITICAL
        )
        res = start_contact_chains_for_alert(alert)
        assert res['status'] == 'success'
        assert res['chains_created'] == 1

        # Only c1 has a notification chain
        assert ContactNotificationChain.objects.filter(alert=alert, contact=c1_granted).exists()
        assert not ContactNotificationChain.objects.filter(alert=alert, contact=c2_pending).exists()

    def test_no_eligible_contacts_handled(self, db):
        user = CustomUser.objects.create_user(
            email='lonely@fixpoint.io',
            password='TestPassword!123',
            role=UserRole.CUSTOMER
        )
        alert = AlertRecord.objects.create(
            user=user,
            status=AlertStatus.TRIGGERED,
            severity=AlertSeverity.CRITICAL
        )
        res = start_contact_chains_for_alert(alert)
        assert res['status'] == 'no_eligible_contacts'
        assert res['chains_created'] == 0
        assert AuditEvent.objects.filter(action='NO_ELIGIBLE_CONTACTS', actor=user).exists()

    def test_happy_path_timeline_progression_with_clock_injection(self, user_with_contacts):
        """Simulates WhatsApp -> wait 60s -> SMS -> wait 30s -> Voice Call with injected clock."""
        user, c1, _ = user_with_contacts
        alert = AlertRecord.objects.create(
            user=user,
            status=AlertStatus.TRIGGERED,
            severity=AlertSeverity.CRITICAL
        )
        start_res = start_contact_chains_for_alert(alert)
        chain = start_res['chains'][0]

        t0 = timezone.now()
        # 1. First run: WhatsApp step
        process_chain(str(chain.id), now=t0)
        chain.refresh_from_db()
        assert chain.current_step == ChainStep.SMS
        assert chain.next_action_at == t0 + timedelta(seconds=60)

        # Check delivery attempt for WhatsApp
        wa_attempt = chain.delivery_attempts.get(channel='WHATSAPP')
        assert wa_attempt.status == AttemptStatus.ACCEPTED
        assert wa_attempt.is_simulated is True
        assert wa_attempt.provider_name == 'MOCK'
        assert wa_attempt.masked_destination.startswith('+91')
        assert '*' in wa_attempt.masked_destination
        assert '+919876543210' not in wa_attempt.masked_destination

        # 2. Before 60s elapsed: SMS step must wait
        t_early = t0 + timedelta(seconds=30)
        process_chain(str(chain.id), now=t_early)
        chain.refresh_from_db()
        assert chain.current_step == ChainStep.SMS
        assert not chain.delivery_attempts.filter(channel='SMS').exists()

        # 3. At t0 + 60s: SMS step triggers
        t_sms = t0 + timedelta(seconds=60)
        process_chain(str(chain.id), now=t_sms)
        chain.refresh_from_db()
        assert chain.current_step == ChainStep.CALL
        assert chain.next_action_at == t_sms + timedelta(seconds=30)
        sms_attempt = chain.delivery_attempts.get(channel='SMS')
        assert sms_attempt.status == AttemptStatus.ACCEPTED

        # 4. At t0 + 90s: Voice call triggers
        t_call = t_sms + timedelta(seconds=30)
        process_chain(str(chain.id), now=t_call)
        chain.refresh_from_db()
        assert chain.call_attempts == 1
        call_attempt = chain.delivery_attempts.get(channel='VOICE_CALL')
        assert call_attempt.status == AttemptStatus.ACCEPTED

    def test_whatsapp_failure_escalates_immediately_to_sms(self, user_with_contacts):
        """Phone ending in 0000 triggers immediate WhatsApp failure -> SMS without waiting."""
        user, _, _ = user_with_contacts
        c_fail_wa = EmergencyContact.objects.create(
            user=user,
            name='Fail WA Contact',
            relationship='Friend',
            phone_number='+919876540000',  # ...0000 fails WhatsApp
            phone_hash=compute_phone_hash('+919876540000'),
            consent_status=ConsentStatus.GRANTED,
            consent_given_at=timezone.now()
        )
        alert = AlertRecord.objects.create(user=user, status=AlertStatus.TRIGGERED)
        chain = ContactNotificationChain.objects.create(
            alert=alert,
            contact=c_fail_wa,
            current_step=ChainStep.WHATSAPP
        )

        t0 = timezone.now()
        process_chain(str(chain.id), now=t0)
        chain.refresh_from_db()

        # WhatsApp attempt failed
        wa_att = chain.delivery_attempts.get(channel='WHATSAPP')
        assert wa_att.status == AttemptStatus.FAILED
        assert 'MOCK_WHATSAPP_UNAVAILABLE' in wa_att.error_code

        # Next step is SMS immediately scheduled for now (no 60s delay!)
        assert chain.current_step == ChainStep.SMS
        assert chain.next_action_at == t0

    def test_sms_failure_escalates_immediately_to_call(self, user_with_contacts):
        """Phone ending in 1111 triggers immediate SMS failure -> CALL without delay."""
        user, _, _ = user_with_contacts
        c_fail_sms = EmergencyContact.objects.create(
            user=user,
            name='Fail SMS Contact',
            relationship='Friend',
            phone_number='+919876541111',  # ...1111 fails SMS
            phone_hash=compute_phone_hash('+919876541111'),
            consent_status=ConsentStatus.GRANTED,
            consent_given_at=timezone.now()
        )
        alert = AlertRecord.objects.create(user=user, status=AlertStatus.TRIGGERED)
        chain = ContactNotificationChain.objects.create(
            alert=alert,
            contact=c_fail_sms,
            current_step=ChainStep.SMS,
            next_action_at=timezone.now()
        )

        t0 = timezone.now()
        process_chain(str(chain.id), now=t0)
        chain.refresh_from_db()

        sms_att = chain.delivery_attempts.get(channel='SMS')
        assert sms_att.status == AttemptStatus.FAILED
        assert 'MOCK_SMS_NETWORK_TIMEOUT' in sms_att.error_code

        # Escalates to CALL immediately
        assert chain.current_step == ChainStep.CALL
        assert chain.next_action_at == t0

    def test_call_unanswered_retries_once_then_exhausted(self, user_with_contacts):
        """Phone ending in 2222 fails call -> retries once -> EXHAUSTED."""
        user, _, _ = user_with_contacts
        c_fail_call = EmergencyContact.objects.create(
            user=user,
            name='Fail Call Contact',
            relationship='Friend',
            phone_number='+919876542222',  # ...2222 unanswered call
            phone_hash=compute_phone_hash('+919876542222'),
            consent_status=ConsentStatus.GRANTED,
            consent_given_at=timezone.now()
        )
        alert = AlertRecord.objects.create(user=user, status=AlertStatus.TRIGGERED)
        chain = ContactNotificationChain.objects.create(
            alert=alert,
            contact=c_fail_call,
            current_step=ChainStep.CALL,
            next_action_at=timezone.now()
        )

        t0 = timezone.now()
        # Attempt 1
        process_chain(str(chain.id), now=t0)
        chain.refresh_from_db()
        assert chain.call_attempts == 1
        assert chain.status == ChainStatus.ACTIVE
        assert chain.next_action_at is not None

        # Attempt 2 (Retry 1)
        t1 = chain.next_action_at
        process_chain(str(chain.id), now=t1)
        chain.refresh_from_db()
        assert chain.call_attempts == 2
        assert chain.status == ChainStatus.EXHAUSTED
        assert chain.current_step == ChainStep.DONE

    def test_acknowledgement_halts_further_steps(self, user_with_contacts, api_client):
        """Acknowledgement via token halts remaining steps and pending attempts."""
        user, c1, _ = user_with_contacts
        alert = AlertRecord.objects.create(user=user, status=AlertStatus.TRIGGERED)
        start_res = start_contact_chains_for_alert(alert)
        chain = start_res['chains'][0]
        raw_token = chain.raw_ack_token_for_demo

        ack_url = reverse('notifications:notification-ack', kwargs={'token': raw_token})

        # GET ack link does NOT acknowledge
        get_res = api_client.get(ack_url)
        assert get_res.status_code == status.HTTP_200_OK
        chain.refresh_from_db()
        assert chain.status == ChainStatus.ACTIVE

        # POST ack link acknowledges
        post_res = api_client.post(ack_url)
        assert post_res.status_code == status.HTTP_200_OK
        chain.refresh_from_db()
        assert chain.status == ChainStatus.ACKNOWLEDGED
        assert chain.acknowledged_at is not None
        assert chain.ack_channel == 'WEB'

        # Calling process_chain after ACK does nothing
        process_chain(str(chain.id), now=timezone.now() + timedelta(hours=1))
        chain.refresh_from_db()
        assert chain.status == ChainStatus.ACKNOWLEDGED
        assert chain.current_step == ChainStep.DONE

        # Double ACK is idempotent and returns 200
        double_ack = api_client.post(ack_url)
        assert double_ack.status_code == status.HTTP_200_OK

    def test_mock_webhook_acknowledgement(self, user_with_contacts, api_client):
        user, c1, _ = user_with_contacts
        alert = AlertRecord.objects.create(user=user, status=AlertStatus.TRIGGERED)
        start_res = start_contact_chains_for_alert(alert)
        chain = start_res['chains'][0]
        raw_token = chain.raw_ack_token_for_demo

        secret = settings.SECRET_KEY.encode('utf-8')
        sig = hmac.new(secret, f"{raw_token}:WHATSAPP".encode('utf-8'), hashlib.sha256).hexdigest()

        webhook_url = reverse('notifications:mock-webhook')
        res = api_client.post(
            webhook_url,
            {'token': raw_token, 'channel': 'WHATSAPP', 'response': '1'},
            format='json',
            HTTP_X_SIGNATURE=sig
        )
        assert res.status_code == status.HTTP_200_OK
        chain.refresh_from_db()
        assert chain.status == ChainStatus.ACKNOWLEDGED
        assert chain.ack_channel == 'WHATSAPP'

        # Replayed webhook returns 200 without error
        res_replay = api_client.post(
            webhook_url,
            {'token': raw_token, 'channel': 'WHATSAPP', 'response': '1'},
            format='json',
            HTTP_X_SIGNATURE=sig
        )
        assert res_replay.status_code == status.HTTP_200_OK

    def test_calling_process_chain_twice_creates_single_delivery_attempt(self, user_with_contacts):
        user, c1, _ = user_with_contacts
        alert = AlertRecord.objects.create(user=user, status=AlertStatus.TRIGGERED)
        start_res = start_contact_chains_for_alert(alert)
        chain = start_res['chains'][0]

        t0 = timezone.now()
        process_chain(str(chain.id), now=t0)
        count_first = DeliveryAttempt.objects.filter(chain=chain, channel='WHATSAPP').count()
        assert count_first == 1

        # Calling again at same time
        process_chain(str(chain.id), now=t0)
        count_second = DeliveryAttempt.objects.filter(chain=chain, channel='WHATSAPP').count()
        assert count_second == 1

    def test_stale_pending_sweeper_recovery(self, user_with_contacts):
        user, c1, _ = user_with_contacts
        alert = AlertRecord.objects.create(user=user, status=AlertStatus.TRIGGERED)
        chain = ContactNotificationChain.objects.create(alert=alert, contact=c1, status=ChainStatus.ACTIVE)

        t0 = timezone.now() - timedelta(seconds=60)
        stale_wa = DeliveryAttempt.objects.create(
            chain=chain,
            channel='WHATSAPP',
            attempt_no=1,
            status=AttemptStatus.PENDING,
            idempotency_key=f"{chain.id}:WHATSAPP:1",
            masked_destination='+91******3210'
        )
        # Update requested_at to past
        DeliveryAttempt.objects.filter(id=stale_wa.id).update(requested_at=t0)

        process_due_chains(now=timezone.now())

        stale_wa.refresh_from_db()
        assert stale_wa.status == AttemptStatus.FAILED
        assert stale_wa.error_code == 'STALE_PENDING_TIMEOUT'

    def test_alert_timeline_visibility(self, user_with_contacts, api_client):
        user, c1, _ = user_with_contacts
        alert = AlertRecord.objects.create(user=user, status=AlertStatus.TRIGGERED)
        start_res = start_contact_chains_for_alert(alert)
        chain = start_res['chains'][0]
        process_chain(str(chain.id))

        timeline_url = reverse('notifications:alert-timeline', kwargs={'alert_id': alert.id})

        # Unauthenticated gets 401
        assert api_client.get(timeline_url).status_code == status.HTTP_401_UNAUTHORIZED

        # Alert owner gets 200 with sanitized data
        api_client.force_authenticate(user=user)
        res = api_client.get(timeline_url)
        assert res.status_code == status.HTTP_200_OK
        data = res.json()['data']
        assert len(data) == 1
        assert data[0]['contact_name'] == 'Asha Nair'
        assert len(data[0]['attempts']) >= 1
        att = data[0]['attempts'][0]
        assert att['is_simulated'] is True
        assert att['provider_name'] == 'MOCK'
        assert '+919876543210' not in str(res.json())  # Raw phone never exposed

    def test_wave_escalation_wave2_cancelled_if_wave1_acknowledges(self, user_with_contacts):
        user, c1, _ = user_with_contacts
        # Create wave 2 contact
        c2_wave2 = EmergencyContact.objects.create(
            user=user,
            name='Kavita Nair',
            relationship='Sister',
            phone_number='+919876543299',
            phone_hash=compute_phone_hash('+919876543299'),
            consent_status=ConsentStatus.GRANTED,
            consent_given_at=timezone.now(),
            wave=2
        )
        alert = AlertRecord.objects.create(user=user, status=AlertStatus.TRIGGERED)
        res = start_contact_chains_for_alert(alert)
        assert res['chains_created'] == 2

        chain_w1 = ContactNotificationChain.objects.get(alert=alert, contact=c1)
        chain_w2 = ContactNotificationChain.objects.get(alert=alert, contact=c2_wave2)

        t0 = timezone.now()
        assert chain_w1.next_action_at <= t0
        assert chain_w2.next_action_at >= t0 + timedelta(minutes=2, seconds=50)

        # Before 3 minutes, wave 2 does not execute
        process_chain(str(chain_w2.id), now=t0)
        chain_w2.refresh_from_db()
        assert chain_w2.delivery_attempts.count() == 0

        # Wave 1 acknowledges via token
        w1_chain_obj = [c for c in res['chains'] if c.contact_id == c1.id][0]
        raw_token = w1_chain_obj.raw_ack_token_for_demo
        ok, msg, _ = acknowledge_chain_by_token(raw_token, channel='WHATSAPP')
        assert ok is True

        # Wave 2 is cancelled immediately
        chain_w2.refresh_from_db()
        assert chain_w2.status == ChainStatus.CANCELLED

        # Even after 3 minutes, sweeper will not run wave 2
        process_chain(str(chain_w2.id), now=t0 + timedelta(minutes=4))
        chain_w2.refresh_from_db()
        assert chain_w2.status == ChainStatus.CANCELLED
        assert chain_w2.delivery_attempts.count() == 0

    def test_wave2_starts_if_wave1_does_not_acknowledge(self, user_with_contacts):
        user, c1, _ = user_with_contacts
        c2_wave2 = EmergencyContact.objects.create(
            user=user,
            name='Sunil Nair',
            relationship='Brother',
            phone_number='+919876543288',
            phone_hash=compute_phone_hash('+919876543288'),
            consent_status=ConsentStatus.GRANTED,
            consent_given_at=timezone.now(),
            wave=2
        )
        alert = AlertRecord.objects.create(user=user, status=AlertStatus.TRIGGERED)
        res = start_contact_chains_for_alert(alert)
        chain_w2 = ContactNotificationChain.objects.get(alert=alert, contact=c2_wave2)

        t0 = timezone.now()
        # Fast-forward 3 minutes and 10 seconds: wave 1 did NOT acknowledge
        t_after_delay = t0 + timedelta(seconds=190)
        process_chain(str(chain_w2.id), now=t_after_delay)

        chain_w2.refresh_from_db()
        assert chain_w2.status == ChainStatus.ACTIVE
        attempt = chain_w2.delivery_attempts.first()
        assert attempt is not None
        assert attempt.channel == 'WHATSAPP'
        assert attempt.status == AttemptStatus.ACCEPTED

