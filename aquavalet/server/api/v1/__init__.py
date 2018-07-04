from aquavalet.server.api.v1 import provider

HANDLERS = [
    provider.ProviderHandler.as_entry()
]
