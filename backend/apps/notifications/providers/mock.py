import uuid
import logging
from django.conf import settings
from .base import BaseNotificationProvider, ProviderResult

logger = logging.getLogger('apps.notifications')

def check_deterministic_failure(channel: str, to: str) -> tuple[bool, str, str]:
    """
    Checks if this dispatch should fail deterministically based on phone suffix or env settings.
    Returns: (should_fail, error_code, error_message)
    """
    fail_channels = [c.strip().upper() for c in getattr(settings, 'MOCK_FAIL_CHANNELS', '').split(',') if c.strip()]
    if channel.upper() in fail_channels:
        return True, "MOCK_ENV_FORCED_FAILURE", f"Mock dispatch for channel {channel} forced to fail by configuration."

    clean_digits = ''.join(c for c in to if c.isdigit())
    
    if clean_digits.endswith('3333'):
        return True, "MOCK_DETERMINISTIC_ALL_FAIL", f"Deterministic failure triggered for suffix 3333 on channel {channel}."
    
    if channel == 'WHATSAPP' and clean_digits.endswith('0000'):
        return True, "MOCK_WHATSAPP_UNAVAILABLE", "Simulated WhatsApp delivery rejected: recipient not reachable on WhatsApp."
    
    if channel == 'SMS' and clean_digits.endswith('1111'):
        return True, "MOCK_SMS_NETWORK_TIMEOUT", "Simulated SMS delivery timed out at mobile network operator."
    
    if channel == 'VOICE_CALL' and clean_digits.endswith('2222'):
        return True, "MOCK_CALL_UNANSWERED", "Simulated automated voice call was unanswered by recipient."

    return False, "", ""

class MockWhatsAppProvider(BaseNotificationProvider):
    def send(self, channel: str, to: str, body: str, idempotency_key: str) -> ProviderResult:
        simulated_body = body if body.startswith("[SIMULATED]") else f"[SIMULATED] {body}"
        logger.info(f"[SIMULATED WHATSAPP] Sending message. IdempotencyKey={idempotency_key}")
        
        should_fail, code, msg = check_deterministic_failure('WHATSAPP', to)
        msg_id = f"mock-wa-{uuid.uuid4().hex[:12]}"
        if should_fail:
            return ProviderResult(
                status='FAILED',
                provider_message_id=msg_id,
                error_code=code,
                error_message=msg
            )
        return ProviderResult(
            status='ACCEPTED',
            provider_message_id=msg_id
        )

class MockSmsProvider(BaseNotificationProvider):
    def send(self, channel: str, to: str, body: str, idempotency_key: str) -> ProviderResult:
        simulated_body = body if body.startswith("[SIMULATED]") else f"[SIMULATED] {body}"
        logger.info(f"[SIMULATED SMS] Sending message. IdempotencyKey={idempotency_key}")
        
        should_fail, code, msg = check_deterministic_failure('SMS', to)
        msg_id = f"mock-sms-{uuid.uuid4().hex[:12]}"
        if should_fail:
            return ProviderResult(
                status='FAILED',
                provider_message_id=msg_id,
                error_code=code,
                error_message=msg
            )
        return ProviderResult(
            status='ACCEPTED',
            provider_message_id=msg_id
        )

class MockVoiceProvider(BaseNotificationProvider):
    def send(self, channel: str, to: str, body: str, idempotency_key: str) -> ProviderResult:
        simulated_body = body if body.startswith("[SIMULATED]") else f"[SIMULATED] {body}"
        logger.info(f"[SIMULATED VOICE] Placing call. IdempotencyKey={idempotency_key}")
        
        should_fail, code, msg = check_deterministic_failure('VOICE_CALL', to)
        call_id = f"mock-call-{uuid.uuid4().hex[:12]}"
        if should_fail:
            return ProviderResult(
                status='FAILED',
                provider_message_id=call_id,
                error_code=code,
                error_message=msg
            )
        return ProviderResult(
            status='ACCEPTED',
            provider_message_id=call_id
        )
