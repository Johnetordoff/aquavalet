from aquavalet.providers.osfstyle.provider import OsfProvider
from aquavalet.settings import ARTIFACTS_TOKEN


class ArtifactsProvider(OsfProvider):
    NAME = 'artifacts'
    BASE_URL = 'https://files.artifacts.ai/v1/resources/'

    def __init__(self, auth):
       self.token = ARTIFACTS_TOKEN
