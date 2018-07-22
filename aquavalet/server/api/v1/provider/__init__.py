import os

import socket
import asyncio
import aiohttp
import logging
from http import HTTPStatus

import tornado.gen
import mimetypes
from aquavalet import settings

from aquavalet.core import utils
from aquavalet.core import exceptions
from aquavalet.core import remote_logging
from aquavalet.core.streams import RequestStreamReader
from aquavalet.server.api.v1 import core
from aquavalet.server.api.v1.provider.movecopy import MoveCopyMixin

logger = logging.getLogger(__name__)


@tornado.web.stream_request_body
class ProviderHandler(core.BaseHandler, MoveCopyMixin):

    bytes_downloaded = 0
    bytes_uploaded = 0

    SUPPORTED_METHODS = core.BaseHandler.SUPPORTED_METHODS + ('METADATA',
                                                              'CHILDREN',
                                                              'UPLOAD',
                                                              'CREATE_FOLDER',
                                                              'RENAME',
                                                              'DOWNLOAD',
                                                              'REVISIONS',
                                                              'MOVE',
                                                              'COPY')

    PATTERN = settings.ROOT_PATTERN

    async def prepare(self, *args, **kwargs):

        self.path = self.path_kwargs['path'] or '/'
        provider = self.path_kwargs['provider']

        self.auth = None  # Figure out best approach
        self.provider = utils.make_provider(provider, self.auth)
        self.provider.item = await self.provider.validate_item(self.path)

        if self.request.method == 'UPLOAD':
            # This is necessary
            self.rsock, self.wsock = socket.socketpair()
            self.reader, _ = await asyncio.open_unix_connection(sock=self.rsock)
            _, self.writer = await asyncio.open_unix_connection(sock=self.wsock)

            self.stream = RequestStreamReader(self.request, self.reader)
        else:
            self.stream = None

    async def metadata(self, provider,  path):

        version = self.get_query_argument('version', default=None)
        metadata = await self.provider.metadata(version=version)

        return self.write({
            'data': metadata.json_api_serialized()
        })

    async def children(self, provider,  path):
        if not self.provider.item.is_folder:
            raise exceptions.InvalidPathError('Only folders can be queried for children.')

        metadata = await self.provider.children()

        return self.write({
            'data': [metadata.json_api_serialized() for metadata in metadata]
        })

    async def rename(self, provider,  path):
        new_name = self.get_query_argument('new_name', default=None)
        if new_name is None:
            raise exceptions.InvalidPathError('new_name is a required parameter for renaming.')

        await self.provider.rename(new_name)


    async def get(self, provider,  path):
        action = self.get_query_argument('serve', default=None)

        if action == 'children':
            return await self.children(provider,  path)
        if action == 'delete':
            return await self.delete(provider,  path)
        elif action == 'meta':
            return await self.metadata(provider,  path)
        elif action == 'rename':
            return await self.rename(provider,  path)
        elif action == 'upload':
            return await self.upload(provider,  path)
        elif action == 'create_folder':
            return await self.create_folder(provider,  path)
        elif action == 'download':
            return await self.download(provider,  path)
        elif action == 'download_as_zip':
            return await self.download_folder_as_zip(provider,  path)
        elif action == 'parent':
            metadata = await self.provider.parent()
            self.write({
                'data': metadata.json_api_serialized()
            })
        elif action == 'copy':
            return await self.copy(provider,  path)
        else:
            return await self.children(provider,  path)

    async def upload(self, provider,  path):
        new_name = self.get_query_argument('new_name', default=None)
        self.writer.write_eof()
        await self.provider.upload(self.stream, new_name)

        self.writer.close()
        self.wsock.close()

    async def create_folder(self, provider,  path):
        if not self.provider.item.is_folder:
            raise exceptions.InvalidPathError(f'{self.item.path} is not a directory, perhaps try using a trailing slash.')

        new_name = self.get_query_argument('new_name', default=None)
        await self.provider.create_folder(new_name)

    async def copy(self, provider,  path):
        dest_path = self.get_query_argument('to', default=None)
        dest_provider = self.get_query_argument('destination_provider', default=None)
        self.dest_provider = utils.make_provider(dest_provider, None)

        self.dest_provider.item = await self.dest_provider.validate_item(dest_path)
        return await self.provider.copy(self.dest_provider)

    async def delete(self, provider,  path):
        comfirm_delete = self.get_query_argument('comfirm_delete', default=None)
        await self.provider.delete(comfirm_delete)

    async def data_received(self, chunk):
        """Note: Only called during uploads."""
        self.bytes_uploaded += len(chunk)
        if self.stream and self.provider.NAME != 'filesystem':
            self.writer.write(chunk)
            await self.writer.drain()
        else:
            self.provider.body += chunk

    async def revisions(self):
        if self.path.is_folder:
            raise exceptions.InvalidPathError(message='Directories have no revisions')

        raise self.provider.revisions()

    async def download(self, provider,  path):
        if 'Range' not in self.request.headers:
            request_range = None
        else:
            request_range = utils.parse_request_range(self.request.headers['Range'])

        version = self.get_query_argument('version', default=None) or self.get_query_argument('revision', default=None)
        async with aiohttp.ClientSession() as session:
            stream = await self.provider.download(
                session,
                version=version,
                range=request_range,
            )

            if getattr(stream, 'partial', None):
                self.set_status(206)
                self.set_header('Content-Range', stream.content_range)

            if stream.content_type is not None:
                self.set_header('Content-Type', stream.content_type)

            if stream.content_range is not None:
                self.set_header('Content-Length', stream.content_range)

            self.set_header('Content-Disposition', 'attachment;filename="{}"'.format(self.provider.item.name))

            _, ext = os.path.splitext(self.provider.item.name)
            if ext in mimetypes.types_map:
                self.set_header('Content-Type', mimetypes.types_map[ext])

            if self.provider.NAME == 'filesystem':
                await self.write_non_aiohttp_stream(stream)
            else:
                async for chunk in stream.response.content.iter_any():
                    self.write(chunk)
                    self.bytes_downloaded += len(chunk)
                    await self.flush()

            if getattr(stream, 'partial', False):
                await stream.response.release()

    async def write_non_aiohttp_stream(self, stream):
        # Needs work
        stream.file_gen = stream.make_chunk_reader(stream)
        async for chunk in stream.file_gen:
            print(chunk)
            self.write(chunk)


    async def download_folder_as_zip(self, provider,  path):
        zipfile_name = self.provider.item.name or '{}-archive'.format(self.provider.NAME)
        self.set_header('Content-Type', 'application/zip')
        self.set_header('Content-Disposition', 'attachment;filename="{}.zip"'.format(zipfile_name))

        async with aiohttp.ClientSession() as session:

            stream = await self.provider.zip(session)

            # Needs work
            self.write(await stream.read())

    def on_finish(self):
        status, method = self.get_status(), self.request.method.upper()

        #self._send_hook(action)

    def _send_hook(self, action):
        source = None
        destination = None

        if action in ('move', 'copy'):
            # if provider can't intra_move or copy, then the celery task will take care of logging
            if not getattr(self.provider, 'can_intra_' + action)(self.dest_provider, self.path):
                return

            source = LogPayload(self.resource, self.provider, path=self.path)
            destination = LogPayload(
                self.dest_resource,
                self.dest_provider,
                metadata=self.dest_meta,
            )
        elif action in ('create', 'create_folder', 'update'):
            source = LogPayload(self.resource, self.provider, metadata=self.metadata)
        elif action in ('delete', 'download_file', 'download_zip'):
            source = LogPayload(self.resource, self.provider, path=self.path)
        else:
            return

        remote_logging.log_file_action(action, source=source, destination=destination, api_version='v1',
                                       request=None,
                                       bytes_downloaded=self.bytes_downloaded,
                                       bytes_uploaded=self.bytes_uploaded,)
