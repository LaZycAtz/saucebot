import hashlib
import typing
from time import time

import discord
from discord.ext.commands import Context
from pony.orm import *
from pysaucenao import GenericSource

from saucebot.config import config
from saucebot.log import log

db = Database()

if config.has_section('MySQL'):
    db.bind(provider='mysql', host=config.get('MySQL', 'hostname'), user=config.get('MySQL', 'username'),
            passwd=config.get('MySQL', 'password'), db=config.get('MySQL', 'database'))
else:
    db.bind(provider='sqlite', filename='database.sqlite', create_db=True)


# noinspection PyMethodParameters
class Servers(db.Entity):
    server_id = Required(int, size=64, unique=True)
    api_key = Optional(str, 40)

    @db_session
    def lookup_guild(guild: discord.Guild) -> typing.Optional[str]:
        """
        Gets the SauceNao API key for the specified guild
        Args:
            guild (discord.Guild):

        Returns:
            typing.Optional[str]
        """
        server = Servers.get(server_id=guild.id)
        if server:
            return server.api_key

    @db_session
    def register(guild: discord.Guild, api_key: str):
        # Delete any existing entry for this server
        server = Servers.get(server_id=guild.id)
        if server:
            server.delete()

        Servers(server_id=guild.id, api_key=api_key)
        log.info(f'Registering API key for server {guild.name} ({guild.id})')


# noinspection PyMethodParameters
class SauceCache(db.Entity):
    url_hash        = Required(str, 32, index=True, unique=True)
    created_at      = Required(int, size=32, index=True)
    header          = Required(Json)
    result          = Required(Json)
    result_class    = Required(str, 250)

    @db_session
    def fetch(self, url: str):
        """
        Fetch a cached result, if available
        Args:
            url ():

        Returns:

        """
        pass

    @db_session
    def add_or_update(url: str, result: GenericSource):
        """
        Cache a SauceNao result for 24-hours
        Args:
            url (str): Url to query
            result (GenericSource): Result to cache

        Returns:
            SauceQueries
        """
        now = int(time())

        h = hashlib.new('md5')
        h.update(url.encode())

        log.debug(f"Looking up cache entry {h.hexdigest()}")
        cache = SauceCache.get(url_hash=h.hexdigest())
        if cache:
            log.debug(f"Refreshing cache entry for {h.hexdigest()}")
            cache.delete()

        print(type(result).__name__)
        return SauceCache(url_hash=h.hexdigest(), created_at=now, header=result.header, result=result.data,
                          result_class=type(result).__name__)


# noinspection PyMethodParameters
class SauceQueries(db.Entity):
    server_id       = Required(int, size=64)
    user_id         = Required(int, size=64, index=True)
    url_hash        = Required(str, 32, index=True)
    queried         = Optional(int, size=32, index=True)

    @db_session
    def log(ctx: Context, url: str):
        """
        Gets the SauceNao API key for the specified guild
        Args:
            ctx (Context):
            url (str): URL to the image that was queries. Will be md5 hashed and stored in the database.

        Returns:
            SauceQueries
        """
        now = int(time())

        h = hashlib.new('md5')
        h.update(url.encode())

        log.debug(f"Logging query from user {ctx.author} with URL hash {h.hexdigest()}")
        return SauceQueries(server_id=ctx.guild.id, user_id=ctx.author.id, url_hash=h.hexdigest(), queried=now)


if str(config.get('Bot', 'LogLevel', fallback='INFO')).upper().strip() == 'DEBUG':
    sql_debug(True)

db.generate_mapping(create_tables=True)
