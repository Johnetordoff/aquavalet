from celery import Celery
from celery.signals import task_failure

from waterbutler.tasks import settings as tasks_settings


app = Celery()
app.config_from_object(tasks_settings)


def register_signal(client):
    """Adapted from `raven.contrib.celery.register_signal`. Remove args and
    kwargs from logs so that keys aren't leaked to Sentry.
    """
    def process_failure_signal(sender, task_id, *args, **kwargs):
        client.captureException(
            extra={
                'task_id': task_id,
                'task': sender,
            }
        )
    task_failure.connect(process_failure_signal, weak=False)

