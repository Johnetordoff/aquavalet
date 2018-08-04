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
from aquavalet import settings as wb_settings
from aquavalet.core import metadata as wb_metadata
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

    def __init__(self, auth: dict,
                 retry_on: typing.Set[int]={408, 502, 503, 504}) -> None:
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
    def NAME(self) -> str:
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
            'name': self.NAME,
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

    def build_headers(self, **kwargs) -> dict:
        headers = self.default_headers
        headers.update(kwargs)
        return {
            key: value
            for key, value in headers.items()
            if value is not None
        }

    async def handle_response(self, resp, item=None, path=None):
        data = await resp.json()
        return {
            400: exceptions.InvalidPathError(data),
            401: exceptions.AuthError(f'Bad credentials provided'),
            403: exceptions.Forbidden(f'Forbidden'),
            404: exceptions.NotFoundError(f'Item at path \'{path or item.path}\' cannot be found.'),
            409: exceptions.Conflict(f'Conflict \'{path or item.path}\'.'),
            410: exceptions.Gone(f'Item at path \'{path or item.path}\' has been removed.')
        }[resp.status]

    async def move(self, dest_provider, item=None, destination_item=None):
        item = item or self.item
        destination_item = destination_item or dest_provider.item

        if item.is_folder:
            return await self._recursive_op(self.move, dest_provider, item, destination_item)  # type: ignore

        async with aiohttp.ClientSession() as session:
            download_stream = await self.download(session, item=item)
            return await dest_provider.upload(download_stream, item=destination_item, new_name=item.name)

        await self.delete(item)

    async def copy(self, dest_provider, item=None, destination_item=None):
        item = item or self.item
        destination_item = destination_item or dest_provider.item

        if item.is_folder:
            return await self._recursive_op(self.copy, dest_provider, item, destination_item)  # type: ignore

        async with aiohttp.ClientSession() as session:
            download_stream = await self.download(session, item=item)
            return await dest_provider.upload(download_stream, item=destination_item, new_name=item.name)

    async def _recursive_op(self, func, dest_provider, src_path, dest_item, **kwargs):
        folder = await dest_provider.create_folder(item=dest_item, new_name=src_path.name)
        folder.children = []

        items = await self.children(item=src_path)

        for i in range(0, len(items), wb_settings.OP_CONCURRENCY):
            futures = []
            for item in items[i:i + wb_settings.OP_CONCURRENCY]:
                futures.append(asyncio.ensure_future(func(dest_provider, item=item, destination_item=folder)))

                if item.is_folder:
                    await futures[-1]

            if not futures:
                continue

            done, _ = await asyncio.wait(futures)

            for fut in done:
                folder.children.append(fut.result())

        return folder

    async def handle_naming(self, src_path, dest_path, rename: str=None, conflict: str='replace'):
        """Given a :class:`.AquaValetPath` and the desired name, handle any potential naming issues.

        i.e.:

        ::

            cp /file.txt /folder/           ->    /folder/file.txt
            cp /folder/ /folder/            ->    /folder/folder/
            cp /file.txt /folder/file.txt   ->    /folder/file.txt
            cp /file.txt /folder/file.txt   ->    /folder/file (1).txt
            cp /file.txt /folder/doc.txt    ->    /folder/doc.txt


        :param src_path: ( :class:`.AquaValetPath` ) The object that is being copied
        :param dest_path: ( :class:`.AquaValetPath` ) The path that is being copied to or into
        :param rename: ( :class:`str` ) The desired name of the resulting path, may be incremented
        :param conflict: ( :class:`str` ) The conflict resolution strategy, ``replace`` or ``keep``

        :rtype: :class:`.AquaValetPath`
        """
        if self.item.is_folder and dest_path.is_file:
            # Cant copy a directory to a file
            raise ValueError('Destination must be a directory if the source is')

        if not dest_path.is_file:
            # Directories always are going to be copied into
            # cp /folder1/ /folder2/ -> /folder1/folder2/
            dest_path = await self.revalidate_path(
                dest_path,
                rename or src_path.name,
                folder=src_path.is_dir
            )

        dest_path, _ = await self.handle_name_conflict(dest_path, conflict=conflict)

        return dest_path

    def can_intra_copy(self, other: 'BaseProvider', path) -> bool:
        """Indicates if a quick copy can be performed between the current provider and `other`.

        .. note::
            Defaults to False

        :param other: ( :class:`.BaseProvider` ) The provider to check against
        :param  path: ( :class:`.AquaValetPath` ) The path of the desired resource
        :rtype: :class:`bool`
        """
        return False

    def can_intra_move(self, other: 'BaseProvider', path) -> bool:
        """Indicates if a quick move can be performed between the current provider and `other`.

        .. note::
            Defaults to False

        :param other: ( :class:`.BaseProvider` ) The provider to check against
        :param path: ( :class:`.AquaValetPath` ) The path of the desired resource
        :rtype: :class:`bool`
        """
        return False

    async def intra_copy(self, dest_provider: 'BaseProvider', source_path, dest_path) -> typing.Tuple[wb_metadata.BaseMetadata, bool]:
        """If the provider supports copying files and/or folders within itself by some means other
        than download/upload, then ``can_intra_copy`` should return ``True``.  This method will
        implement the copy.  It accepts the destination provider, a source path, and the
        destination path.  Returns the metadata for the newly created file and a boolean indicating
        whether the copied entity is completely new (``True``) or overwrote a previously-existing
        file (``False``).

        :param  dest_provider: ( :class:`.BaseProvider` )  a provider instance for the destination
        :param  src_path: ( :class:`.AquaValetPath` )  the Path of the entity being copied
        :param  dest_path: ( :class:`.AquaValetPath` ) the Path of the destination being copied to
        :rtype: (:class:`.BaseFileMetadata`, :class:`bool`)
        """
        raise NotImplementedError

    async def intra_move(self, dest_provider: 'BaseProvider', src_path, dest_path) -> typing.Tuple[wb_metadata.BaseMetadata, bool]:
        """If the provider supports moving files and/or folders within itself by some means other
        than download/upload/delete, then ``can_intra_move`` should return ``True``.  This method
        will implement the move.  It accepts the destination provider, a source path, and the
        destination path.  Returns the metadata for the newly created file and a boolean indicating
        whether the moved entity is completely new (``True``) or overwrote a previously-existing
        file (``False``).

        :param  dest_provider: ( :class:`.BaseProvider` ) a provider instance for the destination
        :param  src_path: ( :class:`.AquaValetPath` ) the Path of the entity being moved
        :param  dest_path: ( :class:`.AquaValetPath` ) the Path of the destination being moved to
        :rtype: (:class:`.BaseFileMetadata`, :class:`bool`)
        """
        data, created = await self.intra_copy(dest_provider, src_path, dest_path)
        #await self.delete(src_path)
        return data, created

    async def exists(self, path, **kwargs) \
            -> typing.Union[bool, wb_metadata.BaseMetadata, typing.List[wb_metadata.BaseMetadata]]:
        """Check for existence of AquaValetPath

        Attempt to retrieve provider metadata to determine existence of a AquaValetPath.  If
        successful, will return the result of `self.metadata()` which may be `[]` for empty
        folders.

        :param  path: ( :class:`.AquaValetPath` ) path to check for
        :rtype: (`self.metadata()` or False)
        """
        try:
            return await self.metadata(path, **kwargs)
        except exceptions.NotFoundError:
            return False
        except exceptions.MetadataError as e:
            if e.code != 404:
                raise
        return False

    async def handle_name_conflict(self, path, conflict: str='replace', **kwargs):
        """Check AquaValetPath and resolve conflicts

        Given a AquaValetPath and a conflict resolution pattern determine
        the correct file path to upload to and indicate if that file exists or not

        :param  path: ( :class:`.AquaValetPath` ) Desired path to check for conflict
        :param conflict: ( :class:`str` ) replace, keep, warn
        :rtype: (:class:`.AquaValetPath` or False)
        :raises: :class:`.NamingConflict`
        """
        exists = await self.exists(path, **kwargs)
        if (not exists and not exists == []) or conflict == 'replace':
            return path, exists  # type: ignore
        if conflict == 'warn':
            raise exceptions.NamingConflict(path.name)

        while True:
            path.increment_name()
            test_path = await self.revalidate_path(
                path.parent,
                path.name,
                folder=path.is_dir
            )

            exists = await self.exists(test_path, **kwargs)
            if not (exists or exists == []):
                break

        return path, False

    async def zip(self, session, **kwargs) -> asyncio.StreamReader:
        """Streams a Zip archive of the given folder

        :param  path: ( :class:`.AquaValetPath` ) The folder to compress
        """

        children = await self.children()  # type: ignore
        return ZipStreamGeneratorReader(self, self.item, children, session)  # type: ignore

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
    async def validate_item(self, item=None) -> wb_metadata.BaseMetadata:
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
        return 'bytes={}-{}'.format(
            '' if start is None else start,
            '' if end is None else end
        )

    def __repr__(self):
        # Note: credentials are not included on purpose.
        return '<{}({}, {})>'.format(self.__class__.__name__, self.auth, self.settings)
