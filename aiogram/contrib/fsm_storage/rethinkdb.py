import asyncio
import contextlib
import typing

import rethinkdb
from rethinkdb.asyncio_net.net_asyncio import Connection

from ...dispatcher.storage import BaseStorage

__all__ = ('RethinkDBStorage',)

r = rethinkdb.RethinkDB()
r.set_loop_type('asyncio')


class RethinkDBStorage(BaseStorage):
    """
    RethinkDB-based storage for FSM.

    Usage:

    .. code-block:: python3

        storage = RethinkDBStorage(db='aiogram', table='aiogram', user='aiogram', password='aiogram_secret')
        dispatcher = Dispatcher(bot, storage=storage)

    And need to close connection when shutdown

    .. code-block:: python3

        await storage.close()
        await storage.wait_closed()

    """

    def __init__(self,
                 host: str = 'localhost',
                 port: int = 28015,
                 db: str = 'aiogram',
                 table: str = 'aiogram',
                 auth_key: typing.Optional[str] = None,
                 user: typing.Optional[str] = None,
                 password: typing.Optional[str] = None,
                 timeout: int = 20,
                 ssl: typing.Optional[dict] = None,
                 loop: typing.Optional[asyncio.AbstractEventLoop] = None):
        self._host = host
        self._port = port
        self._db = db
        self._table = table
        self._auth_key = auth_key
        self._user = user
        self._password = password
        self._timeout = timeout
        self._ssl = ssl or {}
        self._loop = loop

        self._conn: typing.Optional[Connection] = None

    async def connect(self) -> Connection:
        """
        Get or create a connection.
        """
        if self._conn is None:
            self._conn = await r.connect(host=self._host,
                                         port=self._port,
                                         db=self._db,
                                         auth_key=self._auth_key,
                                         user=self._user,
                                         password=self._password,
                                         timeout=self._timeout,
                                         ssl=self._ssl,
                                         io_loop=self._loop)
        return self._conn

    @contextlib.asynccontextmanager
    async def connection(self):
        conn = await self.connect()
        yield conn

    async def close(self):
        """
        Close a connection.
        """
        self._conn.close()
        self._conn = None

    async def wait_closed(self):
        """
        Does nothing
        """
        pass

    async def get_state(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                        default: typing.Optional[str] = None) -> typing.Optional[str]:
        chat, user = map(str, self.check_address(chat=chat, user=user))
        async with self.connection() as conn:
            return await r.table(self._table).get(chat)[user]['state'].default(
                self.resolve_state(default) or None
            ).run(conn)

    async def get_data(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                       default: typing.Optional[str] = None) -> typing.Dict:
        chat, user = map(str, self.check_address(chat=chat, user=user))
        async with self.connection() as conn:
            return await r.table(self._table).get(chat)[user]['data'].default(default or {}).run(conn)

    async def set_state(self, *,
                        chat: typing.Union[str, int, None] = None,
                        user: typing.Union[str, int, None] = None,
                        state: typing.Optional[typing.AnyStr] = None):
        chat, user = map(str, self.check_address(chat=chat, user=user))
        async with self.connection() as conn:
            await r.table(self._table).insert(
                {'id': chat, user: {'state': self.resolve_state(state)}},
                conflict="update",
            ).run(conn)

    async def set_data(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                       data: typing.Dict = None):
        chat, user = map(str, self.check_address(chat=chat, user=user))
        async with self.connection() as conn:
            if await r.table(self._table).get(chat).run(conn):
                await r.table(self._table).get(chat).update({user: {'data': r.literal(data)}}).run(conn)
            else:
                await r.table(self._table).insert({'id': chat, user: {'data': data}}).run(conn)

    async def update_data(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                          data: typing.Dict = None,
                          **kwargs):
        chat, user = map(str, self.check_address(chat=chat, user=user))
        async with self.connection() as conn:
            await r.table(self._table).insert({'id': chat, user: {'data': data}}, conflict="update").run(conn)

    def has_bucket(self):
        return True

    async def get_bucket(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                         default: typing.Optional[dict] = None) -> typing.Dict:
        chat, user = map(str, self.check_address(chat=chat, user=user))
        async with self.connection() as conn:
            return await r.table(self._table).get(chat)[user]['bucket'].default(default or {}).run(conn)

    async def set_bucket(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                         bucket: typing.Dict = None):
        chat, user = map(str, self.check_address(chat=chat, user=user))
        async with self.connection() as conn:
            if await r.table(self._table).get(chat).run(conn):
                await r.table(self._table).get(chat).update({user: {'bucket': r.literal(bucket)}}).run(conn)
            else:
                await r.table(self._table).insert({'id': chat, user: {'bucket': bucket}}).run(conn)

    async def update_bucket(self, *, chat: typing.Union[str, int, None] = None,
                            user: typing.Union[str, int, None] = None, bucket: typing.Dict = None,
                            **kwargs):
        chat, user = map(str, self.check_address(chat=chat, user=user))
        async with self.connection() as conn:
                await r.table(self._table).insert({'id': chat, user: {'bucket': bucket}}, conflict="update").run(conn)

    async def get_states_list(self) -> typing.List[typing.Tuple[int, int]]:
        """
        Get list of all stored chat's and user's

        :return: list of tuples where first element is chat id and second is user id
        """
        async with self.connection() as conn:
            result = []

            items = (await r.table(self._table).run(conn)).items

            for item in items:
                chat = int(item.pop('id'))
                for key in item.keys():
                    user = int(key)
                    result.append((chat, user))

        return result

    async def reset_all(self):
        """
        Reset states in DB
        """
        async with self.connection() as conn:
            await r.table(self._table).delete().run(conn)
