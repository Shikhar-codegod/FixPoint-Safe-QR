import logging
from celery import shared_task
from .models import NotificationRecord, NotificationStatus

logger = logging.getLogger('apps.notifications')

@shared_task(name='apps.notifications.dispatch_notification_task')
def dispatch_notification_task(notification_id: str):
    """
    Celery background worker queue for dispatching notifications.
    Third-party SMS/WhatsApp vendor integrations will hook in here in future phases.
    """
    logger.info(f"Queued notification dispatch task for ID={notification_id}")
    try:
        notification = NotificationRecord.objects.get(id=notification_id)
        # Marking simulated queue state for foundation
        logger.info(f"Notification foundation task triggered for destination={notification.recipient_destination}")
        return {'status': 'success', 'notification_id': notification_id}
    except NotificationRecord.DoesNotExist:
        logger.error(f"Notification {notification_id} not found in database.")
        return {'status': 'not_found', 'notification_id': notification_id}
