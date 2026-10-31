import logging
from celery import shared_task
from .models import NotificationRecord, NotificationStatus

logger = logging.getLogger('apps.notifications')


@shared_task(name='apps.notifications.dispatch_notification_task')
def dispatch_notification_task(notification_id: str):
    logger.info(f"Queued notification dispatch task for ID={notification_id}")
    try:
        notification = NotificationRecord.objects.get(id=notification_id)
        if notification.status == NotificationStatus.CANCELLED:
            logger.info(f"Notification {notification_id} was cancelled before dispatch.")
            return {'status': 'cancelled', 'notification_id': notification_id}
        # Marking simulated queue state for foundation
        logger.info(f"Notification foundation task triggered for destination={notification.recipient_destination}")
        return {'status': 'success', 'notification_id': notification_id}
    except NotificationRecord.DoesNotExist:
        logger.error(f"Notification {notification_id} not found in database.")
        return {'status': 'not_found', 'notification_id': notification_id}


@shared_task(name='apps.notifications.process_chain_task')
def process_chain_task(chain_id: str):
    logger.info(f"Executing process_chain_task for chain_id={chain_id}")
    from .services import process_chain
    try:
        chain = process_chain(chain_id)
        return {'status': 'success', 'chain_id': chain_id, 'chain_status': chain.status if chain else None}
    except Exception as exc:
        logger.exception(f"Error processing notification chain {chain_id}: {exc}")
        raise exc


@shared_task(name='apps.notifications.tasks.process_due_chains_task')
def process_due_chains_task():
    """
    Celery Beat periodic task executed every 10 seconds to recover stale pending
    attempts and process due chains.
    """
    from .services import process_due_chains
    try:
        count = process_due_chains()
        return {'status': 'success', 'processed_count': count}
    except Exception as exc:
        logger.exception(f"Error running periodic notification sweeper: {exc}")
        raise exc
