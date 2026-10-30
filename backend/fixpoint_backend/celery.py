import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fixpoint_backend.settings.development')

app = Celery('fixpoint_backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Celery Request: {self.request!r}')
