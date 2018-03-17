import os

from pkg_resources import iter_entry_points
from kombu import Queue, Exchange

from waterbutler import settings


BROKER_URL = 'amqp://{}:{}//'.format(
        os.environ.get('RABBITMQ_PORT_5672_TCP_ADDR', ''),
        os.environ.get('RABBITMQ_PORT_5672_TCP_PORT', ''),
)

WAIT_TIMEOUT =  20
WAIT_INTERVAL = 0.5
ADHOC_BACKEND_PATH = '/tmp'

CELERY_CREATE_MISSING_QUEUES = False
CELERY_DEFAULT_QUEUE =  'waterbutler'
CELERY_QUEUES = (
    Queue('waterbutler', Exchange('waterbutler'), routing_key='waterbutler'),
)
CELERY_ALWAYS_EAGER = False
CELERY_RESULT_BACKEND =  None
CELERY_DISABLE_RATE_LIMITS =  True
CELERY_TASK_RESULT_EXPIRES =  60
CELERY_IMPORTS = [
    entry.module_name
    for entry in iter_entry_points(group='waterbutler.providers.tasks', name=None)
]
CELERY_IMPORTS.extend([
    'waterbutler.tasks.move'
])

CELERY_ACKS_LATE = True
CELERYD_HIJACK_ROOT_LOGGER = False
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
