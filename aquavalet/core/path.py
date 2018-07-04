import os
import typing  # noqa
from itertools import zip_longest

from aquavalet.core import exceptions


class AquaValetPathPart:

    def __init__(self, part: str, *, _id: str=None) -> None:
        self._id = _id
        self._count = 0  # type: int
        self._orig_id = _id
        self._orig_part = part
        self._name, self._ext = os.path.splitext(self.original_value)

    DECODE = lambda x: x  # type: typing.Callable[[str], str]
    ENCODE = lambda x: x  # type: typing.Callable[[str], str]

    @property
    def id(self) -> str:
        return self._id

    @property
    def value(self) -> str:
        if self._count:
            return'{} ({}){}'.format(self._name, self._count, self._ext)
        return'{}{}'.format(self._name, self._ext)

    @property
    def raw(self) -> str:
        return self.value

    @property
    def original_value(self) -> str:
        return self._orig_part

    @property
    def original_raw(self) -> str:
        return self._orig_part

    @property
    def ext(self) -> str:
        return self._ext

    def increment_name(self, _id=None) -> 'AquaValetPathPart':
        self._id = _id
        self._count += 1
        return self

    def renamed(self, name: str) -> 'AquaValetPathPart':
        return self.__class__(self.__class__.ENCODE(name), _id=self._id)  # type: ignore

    def __repr__(self):
        return '{}({!r}, count={})'.format(self.__class__.__name__, self._orig_part, self._count)


class AquaValetPath:

    @classmethod
    def generic_path_validation(cls, path: str) -> None:

        if not path:
            raise exceptions.InvalidPathError('Must specify path')
        if not path.startswith('/'):
            raise exceptions.InvalidPathError('Invalid path \'{}\' specified'.format(path))
        if '//' in path:
            raise exceptions.InvalidPathError('Invalid path \'{}\' specified'.format(path))
        # Do not allow path manipulation via shortcuts, e.g. '..'
        absolute_path = os.path.abspath(path)
        if not path == '/' and path.endswith('/'):
            absolute_path += '/'
        if not path == absolute_path:
            raise exceptions.InvalidPathError('Invalid path \'{}\' specified'.format(absolute_path))

    @classmethod
    def from_parts(cls, parts, folder, **kwargs):
        _ids, _parts = [], []
        for part in parts:
            _ids.append(part.id)
            _parts.append(part.raw)

        path = '/'.join(_parts)
        if parts and not path:
            path = '/'

        return cls(path, _ids=_ids, folder=folder, **kwargs)  # type: ignore

    @classmethod
    def from_metadata(cls, path_metadata, **kwargs):
        _ids = path_metadata.path.rstrip('/').split('/') or []
        return cls(path_metadata.materialized_path, _ids=_ids, folder=path_metadata.is_folder, **kwargs)

    def __init__(self,
                 path: str,
                 _ids: typing.Sequence=(),
                 prepend: str=None,
                 folder: bool=None, **kwargs) -> None:
        # TODO: Should probably be a static method
        self.__class__.generic_path_validation(path)  # type: ignore

        self._orig_path = path

        self._prepend = prepend

        if prepend:
            self._prepend_parts = [AquaValetPathPart(part) for part in prepend.rstrip('/').split('/')]
        else:
            self._prepend_parts = []

        self._parts = [AquaValetPathPart(part, _id=_id) for _id, part in zip_longest(_ids, path.rstrip('/').split('/'))]

        if folder is not None:
            self.is_dir = bool(folder)
        else:
            self.is_dir = self._orig_path.endswith('/')

        if self.is_dir and not self._orig_path.endswith('/'):
            self._orig_path += '/'

    @property
    def is_root(self) -> bool:
        return len(self._parts) == 1

    @property
    def parts(self) -> list:
        return self._parts

    @property
    def name(self) -> str:
        return self._parts[-1].value

    @property
    def id(self) -> str:
        """ Returns the ID of the file or folder. """
        return self._parts[-1].id

    @property
    def identifier_path(self) -> str:
        return '/' + self._parts[-1].id + ('/' if self.is_dir else '')

    @property
    def ext(self) -> str:
        return self._parts[-1].ext

    @property
    def path(self) -> str:
        if len(self.parts) == 1:
            return ''

        return '/'.join([x.value for x in self.parts[1:]]) + ('/' if self.is_dir else '')

    @property
    def raw_path(self) -> str:
        """ Like `.path()`, but passes each path segment through the PathPart's ENCODE function.
        """
        if len(self.parts) == 1:
            return ''
        return '/'.join([x.raw for x in self.parts[1:]]) + ('/' if self.is_dir else '')

    @property
    def full_path(self) -> str:
        """ Same as `.path()`, but with the provider storage root prepended. """
        return '/'.join([x.value for x in self._prepend_parts + self.parts[1:]]) + ('/' if self.is_dir else '')

    @property
    def parent(self):
        if len(self.parts) == 1:
            return None
        return self.__class__.from_parts(self.parts[:-1], folder=True, prepend=self._prepend)

    def child(self, name: str, _id=None, folder: bool=False):

        return self.__class__.from_parts(  # type: ignore
            self.parts + [self.PART_CLASS(name, _id=_id)],
            folder=folder, prepend=self._prepend
        )

    def increment_name(self) -> 'AquaValetPath':
        self._parts[-1].increment_name()
        return self

    def rename(self, name) -> 'AquaValetPath':
        self._parts[-1] = self._parts[-1].renamed(name)
        return self

    def __eq__(self, other):
        return isinstance(other, self.__class__) and str(self) == str(other)


    def __repr__(self):
        return '{}({!r}, prepend={!r})'.format(self.__class__.__name__, self._orig_path, self._prepend)
