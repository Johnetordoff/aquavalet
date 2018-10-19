import logging
import functools
import contextlib

from aquavalet.providers.osfstorage import settings



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
