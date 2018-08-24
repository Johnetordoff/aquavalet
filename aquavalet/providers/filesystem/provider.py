import os
import shutil
import logging
import datetime
import mimetypes

from aquavalet.core import streams
from aquavalet.core import provider
from aquavalet.core import exceptions

from aquavalet.providers.filesystem import settings
from aquavalet.providers.filesystem.metadata import FileSystemMetadata

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

        if path == '/':
            return FileSystemMetadata.root()

        return FileSystemMetadata(path=path)

    def can_intra_copy(self, dest_provider, path=None):
        return type(self) == type(dest_provider)

    async def intra_copy(self, dest_provider, src_path, dest_path):
        try:
            shutil.copy(src_path.path, dest_path.path)
        except FileNotFoundError as exc:
            raise exceptions.InvalidPathError('Invalid path \'{}\' specified'.format(exc.filename))

    async def intra_move(self, dest_provider, src_path, dest_path):
        try:
            shutil.move(src_path.path, dest_path.path)
        except FileNotFoundError as exc:
            raise exceptions.InvalidPathError('Invalid path \'{}\' specified'.format(exc.filename))

    async def rename(self, new_name, item=None):
        item = item or self.item

        try:
            os.rename(item.path, item.rename(new_name))
        except FileNotFoundError as exc:
            raise exceptions.InvalidPathError('Invalid path \'{}\' specified'.format(exc.filename))

    async def download(self, session=None, item=None, version=None, range=None):
        item = item or self.item

        file_pointer = open(item.path, 'rb')

        if range is not None and range[1] is not None:
            return streams.FileStreamReader(file_pointer, range)

        return streams.FileStreamReader(file_pointer)

    async def upload(self, stream=None, item=None, new_name=None):
        item = item or self.item
        print(item.path + new_name)
        with open(item.path + new_name, 'wb') as file_pointer:
            async for chunk in stream.generator:
                file_pointer.write(chunk)

    async def delete(self, item=None):
        item = item or self.item

        if item.is_file:
            try:
                os.remove(item.path)
            except FileNotFoundError:
                raise exceptions.NotFoundError(item.path)
        else:
            if item.is_root:
                raise Exception('That\'s the root!')
            shutil.rmtree(item.path)

    async def metadata(self, version=None, item=None):
        item = item or self.item

        return item

    async def children(self, item=None):
        item = item or self.item

        children = os.listdir(item.path)
        children = [os.path.join(item.path, child) for child in children]
        children = [child + '/' if os.path.isdir(child) else child for child in children]

        return [FileSystemMetadata(path=child) for child in children]

    async def create_folder(self, new_name, item=None):
        item = self.item or item

        os.makedirs(item.child(new_name), exist_ok=True)
        item.raw['path'] = item.child(new_name)  #TODO Do this better
        return item
