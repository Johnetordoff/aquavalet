from aquavalet.providers.osfstyle import OsfProvider


class ArtifactsProvider(OsfProvider):
    NAME = 'artifacts'
    BASE_URL = 'https://files.artifacts.ai/v1/resources/'
