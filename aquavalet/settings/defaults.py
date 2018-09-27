import logging.config
CHUNK_SIZE = 65536  # 64KB

PROJECT_NAME = 'aqua valet'

ROOT_PATTERN = r'(?P<provider>(?:\w|\d)+)(?P<path>/.*/?)'
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

DEBUG = True
CONCURRENT_OPS = 5

DEFAULT_CONFLICT = 'warn'

logging.config.dictConfig(DEFAULT_LOGGING_CONFIG)