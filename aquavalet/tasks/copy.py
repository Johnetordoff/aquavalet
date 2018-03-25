import time
import logging

from aquavalet.core import utils
from aquavalet.tasks import core
from aquavalet.core import remote_logging
from aquavalet.core.path import WaterButlerPath


logger = logging.getLogger(__name__)


@core.celery_task
async def copy(src_bundle, dest_bundle, request={}, start_time=None, **kwargs):
    start_time = start_time or time.time()

    src_path, src_provider = src_bundle.pop('path'), utils.make_provider(**src_bundle.pop('provider'))
    dest_path, dest_provider = dest_bundle.pop('path'), utils.make_provider(**dest_bundle.pop('provider'))

    logger.info('Starting copying {!r}, {!r} to {!r}, {!r}'
                .format(src_path, src_provider, dest_path, dest_provider))

    metadata, errors = None, []
    try:
        metadata, created = await src_provider.copy(dest_provider, src_path, dest_path, **kwargs)
    except Exception as e:
        logger.error('Copy failed with error {!r}'.format(e))
        errors = [e.__repr__()]
        raise  # Ensure sentry sees this
    else:
        logger.info('Copy succeeded')
        dest_path = WaterButlerPath.from_metadata(metadata)
    finally:
        source = LogPayload(src_bundle['nid'], src_provider, path=src_path)
        destination = LogPayload(
            dest_bundle['nid'], dest_provider, path=dest_path, metadata=metadata
        )

        await remote_logging.wait_for_log_futures(
            'copy', source=source, destination=destination, start_time=start_time,
            errors=errors, request=request, api_version='celery',
        )

    return metadata, created