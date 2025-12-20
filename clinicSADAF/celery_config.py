broker_url = 'redis://127.0.0.1:6379'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'Asia/Tashkent'

task_acks_late = True
worker_prefetch_multiplier = 1
