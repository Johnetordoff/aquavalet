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
from aquavalet.server.auth import AuthHandler
from aquavalet.server.api.v1 import core
from aquavalet.server.api.v1.provider.movecopy import MoveCopyMixin

logger = logging.getLogger(__name__)
auth_handler = AuthHandler(None)


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

        self.auth = await auth_handler.get(None, provider, self.request)
        self.provider = utils.make_provider(provider, self.auth['auth'], self.auth['credentials'], self.auth['settings'])
        self.path = await self.provider.validate_path(self.path)

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
        metadata = await self.provider.metadata(self.path, version=version)

        return self.write({
            'data': metadata.json_api_serialized()
        })

    async def children(self, provider,  path):
        metadata = await self.provider.children(self.path)

        return self.write({
            'data': [metadata.json_api_serialized() for metadata in metadata]
        })

    async def rename(self, provider,  path):
        new_name = self.get_query_argument('new_name', default=None)
        if new_name is None:
            raise exceptions.InvalidPathError('new_name is a required parameter for renaming.')

        await self.provider.rename(self.path, new_name)


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
        else:
            return await self.children(provider,  path)

    async def upload(self, provider,  path):
        new_name = self.get_query_argument('new_name', default=None)

        self.writer.write_eof()
        self.writer.close()
        self.wsock.close()

        await self.provider.upload(self.stream, self.path, new_name)

    async def create_folder(self, provider,  path):
        if not self.path.is_folder:
            raise exceptions.InvalidPathError(message=f'{self.path.path} is not a directory, perhaps try using a trailing slash.')

        new_name = self.get_query_argument('new_name', default=None)
        await self.provider.create_folder(self.path, new_name)



    async def copy(self, provider,  path):
        dest_path = self.get_query_argument('to', default=None)
        dest_provider = self.get_query_argument('destination_provider', default=None)

        self.dest_auth = await auth_handler.get(None)
        self.dest_provider = utils.make_provider(dest_provider,
                                                 self.auth['auth'],
                                                 self.auth['credentials'],
                                                 self.auth['settings'])

        return await self.provider.copy(path, dest_provider, dest_path)

    async def delete(self, provider,  path):
        comfirm_delete = self.get_query_argument('comfirm_delete', default=None)
        await self.provider.delete(self.path, comfirm_delete)
        self.set_status(int(HTTPStatus.NO_CONTENT))

    async def data_received(self, chunk):
        """Note: Only called during uploads."""
        self.bytes_uploaded += len(chunk)
        if self.stream:
            self.writer.write(chunk)
            await self.writer.drain()
        else:
            self.body += chunk

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
                self.path,
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

            self.set_header('Content-Disposition', 'attachment;filename="{}"'.format(self.path.name))

            _, ext = os.path.splitext(self.path.name)
            if ext in mimetypes.types_map:
                self.set_header('Content-Type', mimetypes.types_map[ext])

            async for chunk in stream.response.content.iter_any():
                self.write(chunk)
                self.bytes_downloaded += len(chunk)
                await self.flush()

            if getattr(stream, 'partial', False):
                await stream.response.release()

    async def download_folder_as_zip(self):
        zipfile_name = self.path.name or '{}-archive'.format(self.provider.NAME)
        self.set_header('Content-Type', 'application/zip')
        self.set_header(
            'Content-Disposition',
            utils.make_disposition(zipfile_name + '.zip')
        )

        result = await self.provider.zip(self.path)

        await self.write_stream(result)

    def on_finish(self):
        status, method = self.get_status(), self.request.method.upper()

        print(self.provider.resp._body)
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
