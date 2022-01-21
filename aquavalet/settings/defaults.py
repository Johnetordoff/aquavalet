import logging.config

ADDRESS = "0.0.0.0"
PORT = 8000
DOMAIN = "http://localhost:{}".format(PORT)

DEBUG = True

CHUNK_SIZE = 65536  # 64KB
DEFAULT_CONFLICT = "warn"
CONCURRENT_OPS = 5

ROOT_PATTERN = r"/(?P<provider>(?:osfstorage|filesystem)+)(?P<path>/.*/?)"

DEFAULT_FORMATTER = {
    "format": "[%(asctime)s][%(levelname)s][%(name)s]: %(message)s",
    "pattern": "(?<=cookie=)(.*?)(?=&|$)",
    "mask": "***",
}

DEFAULT_LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": DEFAULT_FORMATTER,
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "console",
        },
        "syslog": {"class": "logging.handlers.SysLogHandler", "level": "INFO"},
    },
    "loggers": {"": {"handlers": ["console"], "level": "INFO", "propagate": False}},
    "root": {"level": "INFO", "handlers": ["console"]},
}

logging.config.dictConfig(DEFAULT_LOGGING_CONFIG)
