import os

from pkg_resources import iter_entry_points
from kombu import Queue, Exchange

BROKER_URL = 'amqp://{}:{}//'.format(
    os.environ.get('RABBITMQ_PORT_5672_TCP_ADDR', ''),
    os.environ.get('RABBITMQ_PORT_5672_TCP_PORT', ''),
)

WAIT_TIMEOUT = 20
WAIT_INTERVAL = 0.5
ADHOC_BACKEND_PATH = '/tmp'

CELERY_CREATE_MISSING_QUEUES = False
CELERY_DEFAULT_QUEUE = 'aquavalet'
CELERY_QUEUES = (
    Queue('aquavalet', Exchange('aquavalet'), routing_key='aquavalet'),
)
CELERY_ALWAYS_EAGER = False
CELERY_RESULT_BACKEND = None
CELERY_DISABLE_RATE_LIMITS = True
CELERY_TASK_RESULT_EXPIRES = 60
CELERY_IMPORTS = [
    entry.module_name
    for entry in iter_entry_points(group='aquavalet.providers.tasks', name=None)
]
CELERY_IMPORTS.extend([
    'aquavalet.tasks.move'
])

CELERY_ACKS_LATE = True
CELERYD_HIJACK_ROOT_LOGGER = False
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
