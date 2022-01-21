from aquavalet.providers.osfstyle.metadata import BaseOsfStyleItemMetadata


class OsfMetadata(BaseOsfStyleItemMetadata):
    @property
    def provider(self):
        return "osfstorage"

    BASE_URL = "https://files.osf.io/v1/resources/"
