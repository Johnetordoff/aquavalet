from aquavalet.providers.osfstyle.provider import OsfProvider
from aquavalet.settings import OSF_TOKEN

class OSFStorageProvider(OsfProvider):
    NAME = 'osfstorage'
    BASE_URL = 'https://files.osf.io/v1/resources/'

    def __init__(self, auth):
       self.token = OSF_TOKEN

