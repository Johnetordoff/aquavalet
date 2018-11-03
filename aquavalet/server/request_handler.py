import asyncio
import logging
import mimetypes
import os
import socket

import aiohttp
import tornado.gen

from aquavalet import settings
from aquavalet.core import exceptions
from aquavalet.core import remote_logging
from aquavalet.core import utils
from aquavalet.core.streams import RequestStreamReader
from aquavalet.server import core

logger = logging.getLogger(__name__)


@tornado.web.stream_request_body
class ProviderHandler(core.BaseHandler):

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

    def initialize(self):
        self.stream = None

    async def prepare(self, *args, **kwargs):

        self.path = self.path_kwargs['path'] or '/'
        provider = self.path_kwargs['provider']

        self.auth = None  # Figure out best approach
        self.provider = utils.make_provider(provider, self.auth)
        self.provider.item = await self.provider.validate_item(self.path)

        if self.request.method == 'UPLOAD':
            self.stream = await self.prepare_stream()

    async def prepare_stream(self):
        # This is necessary
        self.rsock, self.wsock = socket.socketpair()
        self.reader, _ = await asyncio.open_unix_connection(sock=self.rsock)
        _, self.writer = await asyncio.open_unix_connection(sock=self.wsock)

        return RequestStreamReader(self.request, self.reader)

    async def data_received(self, chunk):
        """Note: Only called during uploads."""
        self.bytes_uploaded += len(chunk)
        if self.stream:
            self.writer.write(chunk)
            await self.writer.drain()


    async def metadata(self, provider,  path):

        version = self.get_query_argument('version', default=None)
        metadata = await self.provider.metadata(self.provider.item, version=version)

        return self.write({
            'data': metadata.json_api_serialized()
        })

    async def children(self, provider,  path):
        if not self.provider.item.is_folder:
            raise exceptions.InvalidPathError('Only folders can be queried for children.')

        metadata = await self.provider.children(self.provider.item)

        return self.write({
            'data': [metadata.json_api_serialized() for metadata in metadata]
        })

    async def rename(self, provider,  path):
        new_name = self.require_query_argument('new_name', "'new_name' is a required argument")

        await self.provider.rename(self.provider.item, new_name)


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
            self.stream = await self.prepare_stream()
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
        elif action == 'move':
            return await self.move(provider,  path)
        elif action == 'versions':
            return await self.versions(provider,  path)
        else:
            return await self.children(provider,  path)

    async def upload(self, provider,  path):
        new_name = self.require_query_argument('new_name', "'new_name' is a required argument")
        conflict = self.get_query_argument('conflict', default='warn')

        self.writer.write_eof()
        conflict = await self.provider.upload(self.provider.item, self.stream, new_name, conflict)
        if conflict in ['new_version', 'replace']:
            self.set_status(200)
        else:
            self.set_status(201)

        self.writer.close()
        self.wsock.close()

    async def create_folder(self, provider,  path):
        if not self.provider.item.is_folder:
            raise exceptions.InvalidPathError(f'{self.item.path} is not a directory, perhaps try using a trailing slash.')

        new_name = self.require_query_argument('new_name', "'new_name' is a required argument")

        await self.provider.create_folder(self.provider.item, new_name)

    async def get_destination(self, auth=None):
        dest_path = self.require_query_argument('to', "'to' is a required argument")
        dest_provider = self.require_query_argument('destination_provider', "'destination_provider' is a required argument")
        dest_provider = utils.make_provider(dest_provider, auth=auth)
        dest_provider.item = await dest_provider.validate_item(dest_path)
        return dest_provider

    async def copy(self, provider,  path):
        conflict = self.get_query_argument('conflict', default='warn')
        self.dest_provider = await self.get_destination()

        if self.provider.can_intra_copy(self.dest_provider):
            return await self.provider.intra_copy(self.provider.item, self.dest_provider.item, self.dest_provider)

        return await self.provider.copy(self.provider.item, self.dest_provider.item, self.dest_provider, conflict)

    async def move(self, provider,  path):
        conflict = self.get_query_argument('conflict', default='warn')
        self.dest_provider = self.get_destination()

        if self.provider.can_intra_move(self.dest_provider):
            return await self.provider.intra_move(self.provider.item, self.dest_provider)

        await self.provider.move(self.provider.item, self.dest_provider, conflict)

        await self.provider.delete()

    async def delete(self, provider,  path):
        comfirm_delete = self.get_query_argument('comfirm_delete', default=None)
        await self.provider.delete(self.provider.item, comfirm_delete)
        self.set_status(204)

    async def versions(self, provider,  path):
        if self.provider.item.is_folder:
            raise exceptions.InvalidPathError(message='Directories have no revisions')

        metadata = await self.provider.versions()

        return self.write({
            'data': [metadata.json_api_serialized() for metadata in metadata]
        })

    def get_header(self, key):
        return self.request.headers.get(key)

    async def download(self, provider,  path):
        range = self.get_header('Range')
        version = self.get_query_argument('version', default=None)

        #if self.provider.direct_download_url() and not range: auth problems
        #    self.redirect(self.provider.direct_download_url())
        #    return

        if range:
            range = tornado.httputil._parse_request_range(range)

        async with aiohttp.ClientSession() as session:
            stream = await self.provider.download(
                self.provider.item,
                session,
                version=version,
                range=range,
            )

            if range:
                await stream.response.content.readexactly(range[0])

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

            async for chunk in stream:
                self.write(chunk)
                self.bytes_downloaded += len(chunk)
                await self.flush()

            if getattr(stream, 'partial', False):
                await stream.response.release()

    async def download_folder_as_zip(self, provider,  path):
        zipfile_name = self.provider.item.name or '{}-archive'.format(self.provider.name)
        self.set_header('Content-Type', 'application/zip')
        self.set_header('Content-Disposition', 'attachment;filename="{}.zip"'.format(zipfile_name))

        async with aiohttp.ClientSession() as session:

            stream = await self.provider.zip(self.provider.item, session)

            chunk = await stream.read(settings.CHUNK_SIZE)
            while chunk:
                self.write(chunk)
                self.bytes_downloaded += len(chunk)
                chunk = await stream.read(settings.CHUNK_SIZE)
                await self.flush()

    def on_finish(self):
        status, method = self.get_status(), self.request.method.upper()

        #self._send_hook(action)

    def require_query_argument(self, param, message):
        value = self.get_query_argument(param, default=None)
        if not value:
            raise exceptions.InvalidParameters(message=message)
        return value
