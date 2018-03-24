from waterbutler.core.auth import AuthType


class AuthHandler:

    def __init__(self, names):
        pass

    async def fetch(self, request, bundle):
        return {'auth': 'fake_auth', 'credentials': 'fake_creds', 'settings': {'folder': 'platter/'}}

    async def get(self, resource, provider, request, action=None, auth_type=AuthType.SOURCE):
        return {'auth': 'fake_auth',
                'credentials': {'token': 'kRbI44xTJvXN74FjE2EHCSsdISehimyt4bHfyA6HPyUKQPvm1KetWzcT0czxF5LaLqVmMo'},
                'settings': {'folder': 'platter/',
                             'base_url': 'https://files.artifacts.ai/v1/resources/'}
                }

