from aquavalet.providers.osfstyle.metadata import BaseOsfStyleItemMetadata

class ArtifactsMetadata(BaseOsfStyleItemMetadata):

    @property
    def provider(self):
        return 'artifacts'


    BASE_URL = 'https://files.artifacts.ai/v1/resources/'
