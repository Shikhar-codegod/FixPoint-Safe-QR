import logging
from celery import shared_task

logger = logging.getLogger('apps.incidents')

@shared_task(name='apps.incidents.sync_incident_metrics_task')
def sync_incident_metrics_task(incident_id: str):
    logger.info(f"Syncing incident metrics for incident_id={incident_id}")
    return {'status': 'metrics_synced', 'incident_id': incident_id}
