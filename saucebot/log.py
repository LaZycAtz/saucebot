# Set up logging
import logging

from saucebot.config import config

logLevel = getattr(logging, str(config.get('Bot', 'log_level', fallback='ERROR')).upper())
logFormat = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S")

log = logging.getLogger('saucebot')
log.setLevel(logLevel)

# logging.basicConfig(level=logging.DEBUG)

query_log = logging.getLogger('pony.orm.sql')
query_log.setLevel(logLevel)

ch = logging.StreamHandler()
ch.setLevel(logLevel)
ch.setFormatter(logFormat)

log.addHandler(ch)
query_log.addHandler(ch)
