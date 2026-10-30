import os
from django.conf import settings
from .base import BaseNotificationProvider
from .mock import MockWhatsAppProvider, MockSmsProvider, MockVoiceProvider
from .real_skeletons import RealWhatsAppProvider, RealSmsProvider, RealVoiceProvider

def get_provider(channel: str) -> BaseNotificationProvider:
    mode = getattr(settings, 'NOTIFICATION_PROVIDER_MODE', 'mock').lower()
    if mode == 'mock':
        if channel == 'WHATSAPP':
            return MockWhatsAppProvider()
        elif channel == 'SMS':
            return MockSmsProvider()
        elif channel in ['VOICE_CALL', 'CALL']:
            return MockVoiceProvider()
        else:
            return MockSmsProvider()
    else:
        if channel == 'WHATSAPP':
            return RealWhatsAppProvider()
        elif channel == 'SMS':
            return RealSmsProvider()
        elif channel in ['VOICE_CALL', 'CALL']:
            return RealVoiceProvider()
        else:
            return RealSmsProvider()

def get_provider_status() -> dict:
    mode = getattr(settings, 'NOTIFICATION_PROVIDER_MODE', 'mock').lower()
    return {
        'mode': mode,
        'whatsapp_real_configured': bool(
            os.environ.get('REAL_WHATSAPP_API_TOKEN') and os.environ.get('REAL_WHATSAPP_PHONE_NUMBER_ID')
        ),
        'sms_real_configured': bool(
            os.environ.get('REAL_SMS_AUTH_TOKEN') and os.environ.get('REAL_SMS_ACCOUNT_SID')
        ),
        'voice_real_configured': bool(
            os.environ.get('REAL_VOICE_API_KEY') and os.environ.get('REAL_VOICE_ACCOUNT_ID')
        ),
    }
