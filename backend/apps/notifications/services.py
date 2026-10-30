from .models import NotificationRecord, NotificationChannel, NotificationStatus
from .tasks import dispatch_notification_task

def queue_notification(
    recipient_destination: str,
    body: str,
    channel: str = NotificationChannel.SMS,
    title: str = '',
    recipient=None
) -> NotificationRecord:
    record = NotificationRecord.objects.create(
        recipient=recipient,
        recipient_destination=recipient_destination,
        channel=channel,
        title=title,
        body=body,
        status=NotificationStatus.QUEUED
    )
    # Trigger async background task (will run via Celery worker)
    try:
        dispatch_notification_task.delay(str(record.id))
    except Exception:
        pass
    return record
