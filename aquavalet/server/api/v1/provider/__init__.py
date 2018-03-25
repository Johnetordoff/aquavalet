import os

import socket
import asyncio
import logging
from http import HTTPStatus

import tornado.gen

from aquavalet.core import utils
from aquavalet.server.api.v1 import core
from aquavalet.core import remote_logging
from aquavalet.server.auth import AuthHandler
from aquavalet.core.streams import RequestStreamReader
from aquavalet.server.api.v1.provider.movecopy import MoveCopyMixin

logger = logging.getLogger(__name__)
auth_handler = AuthHandler(None)

mime_types = {
    '.csv': 'text/csv',
    '.md': 'text/x-markdown',
}


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

    PATTERN = r'/providers/(?P<provider>(?:\w|\d)+)(?P<path>/.*/?)'

    async def prepare(self, *args, **kwargs):
        method = self.request.method.lower()

        self.path = self.path_kwargs['path'] or '/'
        provider = self.path_kwargs['provider']

        # Delay setup of the provider when method is post, as we need to evaluate the json body action.
        self.auth = await auth_handler.get(None, provider, self.request)
        self.provider = utils.make_provider(provider, self.auth['auth'], self.auth['credentials'], self.auth['settings'])
        self.path = await self.provider.validate_path(self.path)

        # The one special case
        if method == 'upload':
            self.rsock, self.wsock = socket.socketpair()

            self.reader, _ = await asyncio.open_unix_connection(sock=self.rsock)
            _, self.writer = await asyncio.open_unix_connection(sock=self.wsock)

            self.stream = RequestStreamReader(self.request, self.reader)
            self.uploader = asyncio.ensure_future(self.provider.upload(self.stream, self.path))
        else:
            self.stream = None
        self.body = b''

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
        pass

    async def get(self, provider,  path):
        action = self.get_query_argument('serve', default=None)

        if action == 'children':
            return await self.children(provider,  path)
        elif action == 'meta':
            return await self.metadata(provider,  path)
        elif action == 'upload':
            return await self.upload(provider,  path)
        elif action == 'create_folder':
            return await self.create_folder(provider,  path)
        elif action == 'download':
            return await self.download(provider,  path)
        else:
            return await self.children(provider,  path)

    async def upload(self, provider,  path):
        self.writer.write_eof()

        metadata, created = await self.uploader
        self.writer.close()
        self.wsock.close()
        if created:
            self.set_status(201)

        self.write({'data': metadata.json_api_serialized(self.resource)})

    async def create_folder(self, provider,  path):
        return (await self.provider.create_folder(self.path))

    async def post(self, **_):
        return await self.move_or_copy()

    async def copy(self, **_):
        return await self.move_or_copy()

    async def delete(self, provider,  path):
        await self.provider.delete(self.path)
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
        pass

    async def download(self, provider,  path):
        if 'Range' not in self.request.headers:
            request_range = None
        else:
            request_range = utils.parse_request_range(self.request.headers['Range'])

        version = self.get_query_argument('version', default=None) or self.get_query_argument('revision', default=None)
        stream = await self.provider.download(
            self.path,
            version=version,
            range=request_range,
        )
        print(stream.__dict__)
        if getattr(stream, 'partial', None):
            # Use getattr here as not all stream may have a partial attribute
            # Plus it fixes tests
            self.set_status(206)
            self.set_header('Content-Range', stream.content_range)

        if stream.content_type is not None:
            self.set_header('Content-Type', stream.content_type)

        if stream.content_range is not None:
            self.set_header('Content-Length', stream.content_range)

        # Build `Content-Disposition` header from `displayName` override,
        # headers of provider response, or file path, whichever is truthy first
        name = getattr(stream, 'name', None) or self.path.name
        self.set_header('Content-Disposition', 'attachment;filename="{}"'.format(name.replace('"', '\\"')))

        _, ext = os.path.splitext(name)
        # If the file extention is in mime_types
        # override the content type to fix issues with safari shoving in new file extensions
        if ext in mime_types:
            self.set_header('Content-Type', mime_types[ext])

        await self.write_stream(stream)

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
        # If the response code is not within the 200-302 range, the request was a HEAD or OPTIONS,
        # or the response code is 202 no callbacks should be sent and no metrics collected.
        # For 202s, celery will send its own callback.  Osfstorage and s3 can return 302s for file
        # downloads, which should be tallied.
        if any((method in ('HEAD', 'OPTIONS'), status == 202, status > 302, status < 200)):
            return

        if method == 'GET' and 'meta' in self.request.query_arguments:
            return

        # Done here just because method is defined
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
