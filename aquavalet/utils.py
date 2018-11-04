import asyncio
import logging
import functools

logger = logging.getLogger(__name__)



def make_provider(name: str, auth: dict):
    """Returns an instance of :class:`aquavalet.core.provider.BaseProvider`

    :param str name: The name of the provider to instantiate. (s3, box, etc)
    :param dict auth:
    :param dict \*\*kwargs: currently there to absorb ``callback_url``

    :rtype: :class:`waterbutler.core.provider.BaseProvider`
    """
    from aquavalet.providers.filesystem import FileSystemProvider
    from aquavalet.providers.osfstorage import OSFStorageProvider

    return {
        'filesystem': FileSystemProvider,
        'osfstorage': OSFStorageProvider
    }[name](auth)

def as_task(func):
    if not asyncio.iscoroutinefunction(func):
        func = asyncio.coroutine(func)

    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        return asyncio.ensure_future(func(*args, **kwargs))

    return wrapped


def async_retry(retries=5, backoff=1, exceptions=(Exception, )):

    def _async_retry(func):

        @as_task
        @functools.wraps(func)
        async def wrapped(*args, __retries=0, **kwargs):
            try:
                return await asyncio.coroutine(func)(*args, **kwargs)
            except exceptions as e:
                if __retries < retries:
                    wait_time = backoff * __retries
                    logger.warning('Task {0} failed with {1!r}, {2} / {3} retries. Waiting {4} seconds before retrying'.format(func, e, __retries, retries, wait_time))
                    await asyncio.sleep(wait_time)
                    return await wrapped(*args, __retries=__retries + 1, **kwargs)
                else:
                    # Logs before all things
                    logger.error('Task {0} failed with exception {1}'.format(func, e))

                    # If anything happens to be listening
                    raise e

        # Retries must be 0 to start with
        # functools partials dont preserve docstrings
        return wrapped

    return _async_retry


def lreplace(pattern, sub, string):
    """
    Replaces 'pattern' in 'string' with 'sub' if 'pattern' starts 'string'.
    """
    import re
    return re.sub('^%s' % pattern, sub, string)
