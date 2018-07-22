import os
import shutil
import logging
import datetime
import mimetypes

from aquavalet.core import streams
from aquavalet.core import provider
from aquavalet.core import exceptions

from aquavalet.providers.filesystem import settings
from aquavalet.providers.filesystem.metadata import FileSystemItemMetadata

logger = logging.getLogger(__name__)


class FileSystemProvider(provider.BaseProvider):
    """Provider using the local filesystem as a backend-store

    This provider is used for local testing.  Files are stored by hash, preserving
    case-sensitivity on case-insensitive host filesystems.
    """
    NAME = 'filesystem'
    body = b''

    async def validate_item(self, path, **kwargs):
        if not os.path.exists(path) or os.path.isdir(path) and not path.endswith('/'):
            raise exceptions.NotFoundError(f'Item at \'{path}\' could not be found, folders must end with \'/\'')

        return FileSystemItemMetadata.build(path)

    def can_intra_copy(self, dest_provider, path=None):
        return type(self) == type(dest_provider)

    async def intra_copy(self, dest_provider, src_path, dest_path):
        shutil.copy(src_path.full_path, dest_path.full_path)

    async def intra_move(self, dest_provider, src_path, dest_path):
        shutil.move(src_path.full_path, dest_path.full_path)

    async def rename(self, path, new_name):
        try:
            os.rename(path.path, path.rename(new_name))
        except FileNotFoundError as exc:
            raise exceptions.InvalidPathError('Invalid path \'{}\' specified'.format(exc.filename))

    async def download(self, revision=None, range=None, **kwargs):
        file_pointer = open(self.item.path, 'rb')

        if range is not None and range[1] is not None:
            return streams.PartialFileStreamReader(file_pointer, range)

        return streams.FileStreamReader(file_pointer)

    async def upload(self, stream=None, new_name=None):

        async def stream_sender(stream=None):
            chunk = await stream.read(64 * 1024)
            while chunk:
                yield chunk
                chunk = await stream.read(64 * 1024)

        if not stream:
            with open(self.item.path + new_name, 'wb') as file_pointer:
                file_pointer.write(self.body)
        else:
            with open(self.item.path + new_name, 'wb') as file_pointer:
                async for chunk in stream_sender(stream):
                    file_pointer.write(chunk)

    async def delete(self, path, **kwargs):
        if self.item.is_file:
            try:
                os.remove(self.item.path)
            except FileNotFoundError:
                raise exceptions.NotFoundError(self.item.path)
        else:
            if self.item.is_root:
                raise Exception('That\'s the root!')
            shutil.rmtree(self.item.path)

    async def metadata(self, version=None):
        return self._describe_metadata(self.item)

    async def children(self):

        children = os.listdir(self.item.path)
        children = [os.path.join(self.item.path, child) for child in children]
        children = [child + '/' if os.path.isdir(child) else child for child in children]

        paths = [FileSystemItemMetadata.build(child) for child in children]
        return [self._describe_metadata(path) for path in paths]

    async def create_folder(self, new_name):
        return os.makedirs(self.item.child(new_name), exist_ok=True)

    def _describe_metadata(self, path):
        modified = datetime.datetime.utcfromtimestamp(os.path.getmtime(path.path)).replace(tzinfo=datetime.timezone.utc)
        metadata = {
            'path': path.path,
            'size': os.path.getsize(path.path),
            'modified': modified.isoformat(),
            'mime_type': mimetypes.guess_type(path.path)[0],
        }
        return FileSystemItemMetadata(metadata)
