from aquavalet.providers.osfstyle.provider import OsfProvider
from aquavalet.providers.osfstorage.metadata import OsfMetadata
from aquavalet.settings import OSF_TOKEN

class OSFStorageProvider(OsfProvider):
    BASE_URL = 'https://files.osf.io/v1/resources/'
    API_URL = 'https://api.osf.io/v2/files{path}/?meta='

    Item = OsfMetadata

    def __init__(self, auth):
       self.token = OSF_TOKEN

    @property
    def name(self):
        return 'osfstorage'