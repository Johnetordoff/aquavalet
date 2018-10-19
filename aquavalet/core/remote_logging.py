import asyncio
import logging

from aquavalet.core import utils


@utils.async_retry(retries=0, backoff=0)
async def log_to_callback(action, source=None, destination=None, start_time=None, errors=[], request={}):
    """PUT a logging payload back to the callback given by the auth provider."""
    pass


def log_file_action(action, source, api_version, destination=None, request={},
                    start_time=None, errors=None, bytes_downloaded=None, bytes_uploaded=None):
    """Kick off logging actions in the background. Returns array of asyncio.Tasks."""
    return [
        log_to_callback(action, source=source, destination=destination,
                        start_time=start_time, errors=errors, request=request,)
    ]
