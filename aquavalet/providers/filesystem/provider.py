import os
import shutil
import logging

from aquavalet.core import streams
from aquavalet.core import provider
from aquavalet.core import exceptions

from aquavalet.providers.filesystem.metadata import FileSystemMetadata

logger = logging.getLogger(__name__)


class FileSystemProvider(provider.BaseProvider):
    """Provider using the local filesystem as a backend-store

    This provider is used for local testing.  Files are stored by hash, preserving
    case-sensitivity on case-insensitive host filesystems.
    """
    name = 'filesystem'

    async def validate_item(self, path, **kwargs):
        if not os.path.exists(path) or os.path.isdir(path) and not path.endswith('/'):
            raise exceptions.NotFoundError(f'Item at \'{path}\' could not be found, folders must end with \'/\'')

        if path == '/':
            return FileSystemMetadata.root()

        return FileSystemMetadata(path=path)

    async def intra_copy(self, src_path, dest_path, dest_provider=None):
        try:
            if src_path.kind == 'file':
                shutil.copy(src_path.path, dest_path.path)
            else:
                shutil.copytree(src_path.path, dest_path.child(src_path.path))
        except FileNotFoundError as exc:
            raise exceptions.NotFoundError(f'Item at \'{exc.filename}\' could not be found, folders must end with \'/\'')

    async def intra_move(self, src_path, dest_path, dest_provider=None):
        try:
            shutil.move(src_path.path, dest_path.path)
        except FileNotFoundError as exc:
            raise exceptions.NotFoundError(f'Item at \'{exc.filename}\' could not be found, folders must end with \'/\'')

    async def rename(self, item, new_name):
        try:
            os.rename(item.path, item.rename(new_name))
        except FileNotFoundError as exc:
            raise exceptions.NotFoundError('Invalid path \'{}\' specified'.format(exc.filename))

    async def download(self, item, session=None, version=None, range=None):

        file_pointer = open(item.path, 'rb')

        if range is not None and range[1] is not None:
            return streams.FileStreamReader(file_pointer, range=range)

        return streams.FileStreamReader(file_pointer)

    async def upload(self, item, stream=None, new_name=None, conflict='warn'):
        if os.path.isfile(item.path + new_name):
            return await self.handle_conflict(item=item, conflict=conflict, new_name=new_name, stream=stream)

        with open(item.path + new_name, 'wb') as file_pointer:
            async for chunk in stream:
                file_pointer.write(chunk)

    async def delete(self, item, comfirm_delete=False):

        if item.is_file:
            try:
                os.remove(item.path)
            except FileNotFoundError:
                raise exceptions.NotFoundError(item.path)
        else:
            if item.is_root:
                raise Exception('That\'s the root!')
            shutil.rmtree(item.path)

    async def metadata(self, item, version=None):
        return item

    async def children(self, item):

        children = os.listdir(item.path)
        children = [os.path.join(item.path, child) for child in children]
        children = [child + '/' if os.path.isdir(child) else child for child in children]

        return [FileSystemMetadata(path=child) for child in children]

    async def parent(self, item):
        return FileSystemMetadata(path=item.parent)

    async def create_folder(self, item, new_name):
        os.makedirs(item.child(new_name), exist_ok=True)
        item.raw['path'] = item.child(new_name)  #TODO Do this better
        return item

    def can_intra_copy(self, dest_provider, item=None):
        return type(self) == type(dest_provider)

    def can_intra_move(self, dest_provider, item=None):
        return type(self) == type(dest_provider)

