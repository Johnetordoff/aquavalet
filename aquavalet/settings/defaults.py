import logging.config
CHUNK_SIZE = 65536  # 64KB

PROJECT_NAME = 'aqua valet'

ROOT_PATTERN = r'/(?P<provider>(?:osfstorage|filesystem)+)(?P<path>/.*/?)'
DEFAULT_FORMATTER = {
    'format': '[%(asctime)s][%(levelname)s][%(name)s]: %(message)s',
    'pattern': '(?<=cookie=)(.*?)(?=&|$)',
    'mask': '***'
}

DEFAULT_LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': DEFAULT_FORMATTER,
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'console'
        },
        'syslog': {
            'class': 'logging.handlers.SysLogHandler',
            'level': 'INFO'
        }
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console']
    }
}

CONCURRENT_OPS = 5

DEFAULT_CONFLICT = 'warn'

logging.config.dictConfig(DEFAULT_LOGGING_CONFIG)

import hashlib

from aquavalet import settings


ADDRESS = '0.0.0.0'
PORT = 7777
DOMAIN = "http://localhost:7777"

DEBUG = True

XHEADERS = False
CORS_ALLOW_ORIGIN = '*'

MAX_BODY_SIZE = 4.9 * (1024 ** 3)  # 4.9 GB

HMAC_ALGORITHM = getattr(hashlib, 'sha256')

HMAC_SECRET = 'HMAC_SECRET'
if not DEBUG:
    assert HMAC_SECRET, 'HMAC_SECRET must be specified when not in debug mode'
HMAC_SECRET = (HMAC_SECRET or 'changeme').encode('utf-8')
