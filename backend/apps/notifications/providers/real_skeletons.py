import os
from .base import BaseNotificationProvider, ProviderResult, ProviderNotConfigured

class RealWhatsAppProvider(BaseNotificationProvider):
    """
    Skeleton adapter for real WhatsApp Business API provider.
    Raises ProviderNotConfigured if required credentials are not found in environment.
    """
    def send(self, channel: str, to: str, body: str, idempotency_key: str) -> ProviderResult:
        api_token = os.environ.get('REAL_WHATSAPP_API_TOKEN')
        phone_number_id = os.environ.get('REAL_WHATSAPP_PHONE_NUMBER_ID')
        if not api_token or not phone_number_id:
            raise ProviderNotConfigured(
                "Real WhatsApp provider credentials are not configured in environment."
            )
        # Skeleton implementation only:
        raise NotImplementedError("Real WhatsApp transport is not implemented.")

class RealSmsProvider(BaseNotificationProvider):
    """
    Skeleton adapter for real SMS telephony provider.
    Raises ProviderNotConfigured if required credentials are not found in environment.
    """
    def send(self, channel: str, to: str, body: str, idempotency_key: str) -> ProviderResult:
        auth_token = os.environ.get('REAL_SMS_AUTH_TOKEN')
        account_sid = os.environ.get('REAL_SMS_ACCOUNT_SID')
        if not auth_token or not account_sid:
            raise ProviderNotConfigured(
                "Real SMS provider credentials are not configured in environment."
            )
        # Skeleton implementation only:
        raise NotImplementedError("Real SMS transport is not implemented.")

class RealVoiceProvider(BaseNotificationProvider):
    """
    Skeleton adapter for real automated voice telephony provider.
    Raises ProviderNotConfigured if required credentials are not found in environment.
    """
    def send(self, channel: str, to: str, body: str, idempotency_key: str) -> ProviderResult:
        api_key = os.environ.get('REAL_VOICE_API_KEY')
        account_id = os.environ.get('REAL_VOICE_ACCOUNT_ID')
        if not api_key or not account_id:
            raise ProviderNotConfigured(
                "Real Voice provider credentials are not configured in environment."
            )
        # Skeleton implementation only:
        raise NotImplementedError("Real Voice transport is not implemented.")
