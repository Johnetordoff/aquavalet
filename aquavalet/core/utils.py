import json
import pytz
import asyncio
import logging
import functools
# from concurrent.futures import ProcessPoolExecutor  TODO Get this working

import aiohttp
from stevedore import driver

from aquavalet.core import exceptions
from aquavalet.server import settings as server_settings
from aquavalet.core.streams import EmptyStream


logger = logging.getLogger(__name__)


sentry_dsn = None


def make_provider(name: str, auth: dict):
    """Returns an instance of :class:`aquavalet.core.provider.BaseProvider`

    :param str name: The name of the provider to instantiate. (s3, box, etc)
    :param dict auth:
    :param dict \*\*kwargs: currently there to absorb ``callback_url``

    :rtype: :class:`waterbutler.core.provider.BaseProvider`
    """
    try:
        manager = driver.DriverManager(
            namespace='aquavalet.providers',
            name=name,
            invoke_on_load=True,
            invoke_args=(auth, ),
        )
    except RuntimeError:
        raise exceptions.ProviderNotFound(name)

    return manager.driver


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

class ZipStreamGenerator:
    def __init__(self, provider, parent_path, metadata_objs, session):
        self.session = session
        self.provider = provider
        self.parent_path = parent_path
        self.remaining = metadata_objs

    async def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.remaining:
            raise StopAsyncIteration
        current = self.remaining.pop(0)
        if current.is_folder:
            items = await self.provider.children(current)
            if items:
                self.remaining.extend(items)
                return await self.__anext__()
            else:
                return current.unix_path, EmptyStream()

        return current.unix_path, await self.provider.download(self.session, item=current)
