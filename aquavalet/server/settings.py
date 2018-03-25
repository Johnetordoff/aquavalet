import hashlib

from aquavalet import settings


ADDRESS = '0.0.0.0'
PORT = 7777
DOMAIN = "http://localhost:7777"

DEBUG = True

SSL_CERT_FILE = None
SSL_KEY_FILE = None

XHEADERS = False
CORS_ALLOW_ORIGIN = '*'

CHUNK_SIZE = 65536  # 64KB
MAX_BODY_SIZE = 4.9 * (1024 ** 3)  # 4.9 GB

HMAC_ALGORITHM = getattr(hashlib, 'sha256')

HMAC_SECRET = 'HMAC_SECRET'
if not settings.DEBUG:
    assert HMAC_SECRET, 'HMAC_SECRET must be specified when not in debug mode'
HMAC_SECRET = (HMAC_SECRET or 'changeme').encode('utf-8')
