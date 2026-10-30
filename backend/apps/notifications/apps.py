import logging
from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger('apps.notifications')

class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notifications'

    def ready(self):
        mode = getattr(settings, 'NOTIFICATION_PROVIDER_MODE', 'mock').lower()
        if mode == 'mock':
            logger.warning("Notification providers are in MOCK mode - no real messages are sent")
