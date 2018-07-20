import os
import glob
import json
import errno
import logging
import functools
import contextlib
import subprocess
from http import HTTPStatus

import aiohttp
from celery.utils.log import get_task_logger

from aquavalet.core import signing
from aquavalet.tasks.app import app
from aquavalet.providers.osfstorage import settings
from aquavalet.providers.osfstorage.tasks import exceptions


logger = get_task_logger(__name__)
logger.setLevel(logging.INFO)


def _log_task(func):
    """Decorator to add standardized logging to Celery tasks. Decorated tasks
    must also be decorated with `bind=True` so that `self` is available.
    """
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        logger.info(self.request)
        return func(self, *args, **kwargs)
    return wrapped


def _create_task(*args, **kwargs):
    """Decorator factory combining `_log_task` and `task(bind=True, *args,
    **kwargs)`. Return a decorator that turns the decorated function into a
    Celery task that logs its calls.
    """
    def wrapper(func):
        wrapped = _log_task(func)
        wrapped = app.task(bind=True, *args, **kwargs)(wrapped)
        return wrapped
    return wrapper


def task(*args, **kwargs):
    """Decorator or decorator factory for logged tasks. If passed a function,
    decorate it; if passed anything else, return a decorator.
    """
    if len(args) == 1 and callable(args[0]):
        return _create_task()(args[0])
    return _create_task(*args, **kwargs)


def get_countdown(attempt, init_delay, max_delay, backoff):
    multiplier = backoff ** attempt
    return min(init_delay * multiplier, max_delay)


@contextlib.contextmanager
def RetryTask(task, attempts, init_delay, max_delay, backoff, warn_idx, error_types):
    try:
        yield
    except error_types as exc_value:
        try_count = task.request.retries
        countdown = get_countdown(try_count, init_delay, max_delay, backoff)
        task.max_retries = attempts
        raise task.retry(exc=exc_value, countdown=countdown)


RetryUpload = functools.partial(
    RetryTask,
    attempts=settings.UPLOAD_RETRY_ATTEMPTS,
    init_delay=settings.UPLOAD_RETRY_INIT_DELAY,
    max_delay=settings.UPLOAD_RETRY_MAX_DELAY,
    backoff=settings.UPLOAD_RETRY_BACKOFF,
    warn_idx=settings.UPLOAD_RETRY_WARN_IDX,
    error_types=(Exception,),
)

RetryHook = functools.partial(
    RetryTask,
    attempts=settings.HOOK_RETRY_ATTEMPTS,
    init_delay=settings.HOOK_RETRY_INIT_DELAY,
    max_delay=settings.HOOK_RETRY_MAX_DELAY,
    backoff=settings.HOOK_RETRY_BACKOFF,
    warn_idx=settings.UPLOAD_RETRY_WARN_IDX,
    error_types=(Exception,),
)

RetryParity = functools.partial(
    RetryTask,
    attempts=settings.PARITY_RETRY_ATTEMPTS,
    init_delay=settings.PARITY_RETRY_INIT_DELAY,
    max_delay=settings.PARITY_RETRY_MAX_DELAY,
    backoff=settings.PARITY_RETRY_BACKOFF,
    warn_idx=settings.PARITY_RETRY_WARN_IDX,
    error_types=(Exception,),
)
