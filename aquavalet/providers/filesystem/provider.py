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

    def __init__(self, auth, credentials, settings):
        super().__init__(auth, credentials, settings)
        self.folder = self.settings['folder']
        os.makedirs(self.folder, exist_ok=True)

    async def validate_path(self, path, **kwargs):
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

    async def download(self, path, revision=None, range=None, **kwargs):
        file_pointer = open(path.path, 'rb')
        if range is not None and range[1] is not None:
            return streams.PartialFileStreamReader(file_pointer, range)

        return streams.FileStreamReader(file_pointer)

    async def upload(self, stream, path, new_name):
        uploaded_path = path.id + new_name

        with open(uploaded_path, 'wb') as file_pointer:
            chunk = await stream.read(settings.CHUNK_SIZE)
            while chunk:
                file_pointer.write(chunk)
                chunk = await stream.read(settings.CHUNK_SIZE)

    async def delete(self, path, **kwargs):
        if path.kind == 'file':
            try:
                os.remove(path.id)
            except FileNotFoundError:
                raise exceptions.NotFoundError(path.id)
        else:
            if path.is_root:
                raise Exception('That\'s the root!')
            shutil.rmtree(path.id)

    async def metadata(self, path, version=None):
        if not os.path.exists(path.path):
            raise exceptions.NotFoundError(path.path)

        return self._format_metadata(path)

    async def children(self, path):
        try:
            children = os.listdir(path.path)
        except FileNotFoundError:
            raise exceptions.NotFoundError(path.path)

        relative_path = path.path.replace(path.name, '')
        paths = [FileSystemItemMetadata.build(os.path.join(relative_path, child)) for child in children]
        return [self._format_metadata(path) for path in paths]

    async def create_folder(self, path, new_name):
        created_folder_path = path.child(new_name)
        return os.makedirs(created_folder_path.full_path, exist_ok=True)

    def _format_metadata(self, path):
        modified = datetime.datetime.utcfromtimestamp(os.path.getmtime(path.path)).replace(tzinfo=datetime.timezone.utc)
        metadata = {
            'path': path.path,
            'size': os.path.getsize(path.path),
            'modified': modified.isoformat(),
            'mime_type': mimetypes.guess_type(path.path)[0],
            'kind':  'folder' if os.path.isdir(path.path) else 'file'
        }
        return FileSystemItemMetadata(metadata)
