from dataclasses import dataclass
from typing import Optional

class ProviderNotConfigured(Exception):
    """Raised when attempting to use a real provider that has missing environment credentials."""
    pass

@dataclass
class ProviderResult:
    status: str  # 'ACCEPTED' or 'FAILED'
    provider_message_id: str
    error_code: str = ''
    error_message: str = ''

class BaseNotificationProvider:
    """
    Common interface for all notification delivery providers (SMS, WhatsApp, Voice Call).
    """
    def send(self, channel: str, to: str, body: str, idempotency_key: str) -> ProviderResult:
        raise NotImplementedError("Subclasses must implement send()")
