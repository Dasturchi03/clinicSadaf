from celery import Celery
from kombu import Exchange, Queue
import os


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinicSADAF.settings')

celery_app = Celery('clinicSADAF')

celery_app.config_from_object("clinicSADAF.celery_config")

celery_app.autodiscover_tasks(['apps.sms.tasks'])

queues = [
    Queue('send_sms_code',
    Exchange('send_sms_code'),
    routing_key='send_sms_code',
    queue_arguments={'x-max-priority': 10})
    
]

celery_app.conf.task_queues = queues

        
# celery -A clinicSADAF.celery_app worker --loglevel=info 