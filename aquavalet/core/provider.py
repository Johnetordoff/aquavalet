import os
import abc
import time
import typing
import asyncio
import logging
import weakref
import functools
import itertools
from urllib import parse

import aiohttp

from aquavalet.core import streams
from aquavalet.core import exceptions
from aquavalet.settings import CONCURRENT_OPS
from aquavalet.core import metadata as wb_metadata
from aquavalet.core.streams import ZipStreamReader
from aquavalet.core.utils import ZipStreamGeneratorReader


logger = logging.getLogger(__name__)
_THROTTLES = weakref.WeakKeyDictionary()  # type: weakref.WeakKeyDictionary


def throttle(concurrency=10, interval=1):
    def _throttle(func):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            if asyncio.get_event_loop() not in _THROTTLES:
                count, last_call, event = 0, time.time(), asyncio.Event()
                _THROTTLES[asyncio.get_event_loop()] = (count, last_call, event)
                event.set()
            else:
                count, last_call, event = _THROTTLES[asyncio.get_event_loop()]

            await event.wait()
            count += 1
            if count > concurrency:
                count = 0
                if (time.time() - last_call) < interval:
                    event.clear()
                    await asyncio.sleep(interval - (time.time() - last_call))
                    event.set()

            last_call = time.time()
            _THROTTLES[asyncio.get_event_loop()] = (count, last_call, event)
            return await func(*args, **kwargs)
        return wrapped
    return _throttle


def build_url(base, *segments, **query):
    url = parse(base)
    # Filters return generators
    # Cast to list to force "spin" it
    url.path.segments = list(filter(
        lambda segment: segment,
        map(
            lambda segment: parse.quote(segment.strip('/')),
            itertools.chain(url.path.segments, segments)
        )
    ))
    url.args = query
    return url.url


class BaseProvider(metaclass=abc.ABCMeta):
    """The base class for all providers. Every provider must, at the least, implement all abstract
    methods in this class.

    .. note::
        When adding a new provider you must add it to setup.py's
        `entry_points` under the `aquavalet.providers` key formatted
        as: `<provider name> = aquavalet.providers.yourprovider:<FullProviderName>`

        Keep in mind that `yourprovider` modules must export the provider class
    """

    BASE_URL = None

    def __init__(self, auth: dict, retry_on: typing.Set[int]={408, 502, 503, 504}) -> None:
        """
        :param auth: ( :class:`dict` ) Information about the user this provider will act on the behalf of
        :param credentials: ( :class:`dict` ) The credentials used to authenticate with the provider,
            ofter an OAuth 2 token
        :param settings: ( :class:`dict` ) Configuration settings for this provider,
            often folder or repo
        """
        self._retry_on = retry_on
        self.auth = auth

    @property
    @abc.abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    def __eq__(self, other):
        try:
            return (
                type(self) == type(other) and
                self.credentials == other.credentials
            )
        except AttributeError:
            return False

    def serialized(self) -> dict:
        return {
            'name': self.name,
            'auth': self.auth,
            'settings': self.settings,
            'credentials': self.credentials,
        }

    def build_url(self, *segments, **query) -> str:
        """
        :param \*segments: ( :class:`tuple` ) A tuple of strings joined into /foo/bar/..
        :param \*\*query: ( :class:`dict` ) A dictionary that will be turned into query parameters ?foo=bar
        :rtype: :class:`str`
        """
        return build_url(self.BASE_URL, *segments, **query)

    @property
    def default_headers(self) -> dict:
        """Headers to be included with every request
        Commonly OAuth headers or Content-Type
        """
        return {}

    async def handle_response(self, resp=None, item=None, path=None, new_name=None, conflict='warn', stream=None):
        data = await resp.json()

        if resp.status == 409:
            return await self.handle_conflict(resp=resp, item=item, path=path, new_name=new_name, conflict=conflict, stream=stream)
        else:
            raise {
                400: exceptions.InvalidPathError(data),
                401: exceptions.AuthError(f'Bad credentials provided'),
                403: exceptions.Forbidden(f'Forbidden'),
                404: exceptions.NotFoundError(f'Item at path \'{path or item.name}\' cannot be found.'),
                409: self.handle_conflict(new_name=new_name, path=path, stream=stream, conflict=conflict),
                410: exceptions.Gone(f'Item at path \'{path or item.name}\' has been removed.')
            }[resp.status]

    async def handle_conflict(self, resp=None, item=None, path=None, new_name=None,  conflict='warn', stream=None):
        if conflict == 'warn':
            return await self.handle_conflict_warn(new_name)
        if conflict == 'replace':
            return await self.handle_conflict_replace(new_name, item, stream)
        if conflict == 'new_version':
            return await self.handle_conflict_new_version(resp=resp, item=item, path=path, new_name=new_name, conflict=conflict, stream=stream)
        if conflict == 'rename':
            return await self.handle_conflict_rename(new_name, item, stream)

    def handle_conflict_warn(self, new_name):
        raise exceptions.Conflict(f'Conflict \'{new_name}\'.')

    async def handle_conflict_replace(self, new_name, item, stream):
        # TODO: Optimize for name based providers (using Mixin?)
        blocking_item = next(child for child in (await self.children(item)) if child.name == new_name)
        await self.delete(blocking_item)
        await self.upload(item, stream=stream, new_name=new_name)

    def handle_conflict_new_version(self):
        raise NotImplementedError()

    async def handle_conflict_rename(self, new_name, item, stream):
        # TODO: Optimize for name based providers (using Mixin?)
        names = {child.name for child in (await self.children(item))}
        num = 1
        print(names)
        while new_name in names:
            name, ext = os.path.splitext(new_name)
            new_name = f'{name}({num}){ext}'
            num += 1
        await self.upload(item, stream=stream, new_name=new_name)


    async def move(self, dest_provider, item, destination_item, conflict):

        if item.is_folder:
            return await self._recursive_op(self.move, dest_provider, item, destination_item)  # type: ignore

        async with aiohttp.ClientSession() as session:
            download_stream = await self.download(item, session)
            await dest_provider.upload(destination_item, download_stream, new_name=item.name, conflict=conflict)

        await self.delete(item)

    async def copy(self, item, destination_item, dest_provider, conflict):

        if item.is_folder:
            return await self._recursive_op(self.copy, item, destination_item, dest_provider)

        async with aiohttp.ClientSession() as session:
            download_stream = await self.download(item, session)
            await dest_provider.upload(destination_item, download_stream, new_name=item.name, conflict=conflict)

    async def _recursive_op(self, func, src_path, dest_item, dest_provider):
        folder = await dest_provider.create_folder(item=dest_item, new_name=src_path.name)
        folder.children = []

        items = await self.children(item=src_path)

        for i in range(0, len(items), CONCURRENT_OPS):
            futures = []
            for item in items[i:i + CONCURRENT_OPS]:
                futures.append(asyncio.ensure_future(func(dest_provider, item=item, destination_item=folder)))

                if item.is_folder:
                    await futures[-1]

            if not futures:
                continue

            done, _ = await asyncio.wait(futures)

            for fut in done:
                folder.children.append(fut.result())

        return folder

    def can_intra_copy(self, other, path) -> bool:
        return False

    def can_intra_move(self, other, path) -> bool:
        return False

    async def zip(self, item, session) -> ZipStreamGeneratorReader:
        """Streams a Zip archive of the given folder

        :param  path: ( :class:`.AquaValetPath` ) The folder to compress
        """
        children = await self.children(item)
        return ZipStreamReader(ZipStreamGeneratorReader(self, item, children, session))

    @abc.abstractmethod
    async def download(self, item=None, version=None, range=None) -> streams.ResponseStreamReader:
        raise NotImplementedError

    @abc.abstractmethod
    async def upload(self, stream, new_name, item=None):
        raise NotImplementedError

    @abc.abstractmethod
    async def delete(self, item=None) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def metadata(self, item=None) -> wb_metadata.BaseMetadata:
        raise NotImplementedError

    @abc.abstractmethod
    async def children(self, item=None) -> wb_metadata.BaseMetadata:
        raise NotImplementedError

    @abc.abstractmethod
    async def validate_item(self, item=None) -> wb_metadata.BaseMetadata:
        raise NotImplementedError

    @abc.abstractmethod
    async def parent(self, item=None) -> wb_metadata.BaseMetadata:
        raise NotImplementedError

    async def versions(self, item=None) -> wb_metadata.BaseMetadata:
        """Return a list of :class:`.BaseFileRevisionMetadata` objects representing the revisions
        available for the file at ``path``.
        """
        return []  # TODO Raise 405 by default h/t @rliebz

    async def create_folder(self, path, item=None) -> wb_metadata.BaseMetadata:
        raise exceptions.ProviderError({'message': 'Folder creation not supported.'}, code=405)

    def _build_range_header(self, slice_tup: typing.Tuple[int, int]) -> str:
        start, end = slice_tup
        start = '' if start is None else start
        end = '' if end is None else end
        return 'bytes={}-{}'.format(start, end)
