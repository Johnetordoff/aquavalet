import os
import datetime
import mimetypes

from aquavalet import metadata


class FileSystemMetadata(metadata.BaseMetadata):
    def __init__(self, raw=None, path=None):
        self.raw = {}
        path = path or raw["path"]
        self.default_segments = [self.provider]
        modified = datetime.datetime.utcfromtimestamp(os.path.getmtime(path)).replace(
            tzinfo=datetime.timezone.utc
        )
        self.raw.update(
            {
                "size": os.path.getsize(path),
                "modified": modified.isoformat(),
                "mime_type": mimetypes.guess_type(path)[0],
                "path": path,
                "name": os.path.basename(path.rstrip("/")),
            }
        )

    @classmethod
    def root(cls):
        raw = {
            "name": f"filesystem root",
            "kind": "folder",
            "modified": "",
            "etag": "",
            "path": "/",
        }

        return cls(raw)

    @property
    def provider(self):
        return "filesystem"

    @property
    def id(self):
        return self.raw["path"]

    @property
    def parent(self):
        if os.path.dirname(self.raw["path"].rstrip("/")) == "/":
            return "/"

        if not self.is_root:
            return os.path.dirname(self.raw["path"].rstrip("/")) + "/"
        else:
            return "/"

    @property
    def name(self):
        if self.is_root:
            return "filesystem root"
        return os.path.basename(self.raw["path"].rstrip("/"))

    def rename(self, new_name):
        self.raw["path"] = self.parent + new_name
        return self.path

    def child(self, new_name):
        return self.path + new_name.rstrip("/") + "/"

    @property
    def path(self):
        return self.raw["path"]

    @property
    def unix_path(self):
        return self.raw["path"]

    @property
    def size(self):
        return self.raw["size"]

    @property
    def modified(self):
        return self.raw["modified"]

    @property
    def mime_type(self):
        return self.raw["mime_type"]

    @property
    def etag(self):
        return "{}::{}".format(self.raw.get("modified"), self.raw["path"])

    @property
    def kind(self):
        if self.path.endswith("/"):
            return "folder"
        return "file"

    @property
    def is_file(self):
        return self.kind == "file"

    @property
    def is_folder(self):
        return self.kind == "folder"

    @property
    def is_root(self):
        return self.id == "/"
