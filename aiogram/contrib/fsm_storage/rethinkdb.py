import asyncio
import typing
import weakref

import rethinkdb as r

from ...dispatcher import BaseStorage

__all__ = ['RethinkDBStorage', 'ConnectionNotClosed']

r.set_loop_type('asyncio')


# TODO: rewrite connections pool


class ConnectionNotClosed(Exception):
    """
    Indicates that DB connection wasn't closed.
    """


class RethinkDBStorage(BaseStorage):
    """
    RethinkDB-based storage for FSM.

    Usage:

    ..code-block:: python3

        storage = RethinkDBStorage(db='aiogram', table='aiogram', user='aiogram', password='aiogram_secret')
        dispatcher = Dispatcher(bot, storage=storage)

    And need to close connection when shutdown

    ..code-clock:: python3

        await storage.close()

    """

    def __init__(self, host='localhost', port=28015, db='aiogram', table='aiogram', auth_key=None,
                 user=None, password=None, timeout=20, ssl=None, max_conn=10, loop=None):
        self._host = host
        self._port = port
        self._db = db
        self._table = table
        self._auth_key = auth_key
        self._user = user
        self._password = password
        self._timeout = timeout
        self._ssl = ssl or {}

        self._queue = asyncio.Queue(max_conn)
        self._outstanding_connections = weakref.WeakSet()
        self._loop = loop or asyncio.get_event_loop()

    async def get_connection(self):
        """
        Get or create connection.
        """
        try:
            while True:
                conn: r.Connection = self._queue.get_nowait()
                if conn.is_open():
                    break
                try:
                    await conn.close()
                except r.ReqlError:
                    raise ConnectionNotClosed('Exception was caught while closing connection')
        except asyncio.QueueEmpty:
            if len(self._outstanding_connections) < self._queue.maxsize:
                conn = await r.connect(host=self._host, port=self._port, db=self._db,
                                       auth_key=self._auth_key, user=self._user, password=self._password,
                                       timeout=self._timeout, ssl=self._ssl)
            else:
                conn = await self._queue.get()

        self._outstanding_connections.add(conn)
        return conn

    async def put_connection(self, conn):
        """
        Return connection to pool.
        """
        self._queue.put_nowait(conn)
        self._outstanding_connections.remove(conn)

    async def close(self):
        """
        Close all connections.
        """
        while True:
            try:
                conn: r.Connection = self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break

            self._outstanding_connections.add(conn)

        for conn in self._outstanding_connections:
            try:
                await conn.close()
            except r.ReqlError:
                raise ConnectionNotClosed('Exception was caught while closing connection')

    async def wait_closed(self):
        """
        Does nothing
        """
        pass

    async def get_state(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                        default: typing.Optional[str] = None) -> typing.Optional[str]:
        chat, user = map(str, self.check_address(chat=chat, user=user))
        conn = await self.get_connection()
        result = await r.table(self._table).get(chat)[user]['state'].default(default or None).run(conn)
        await self.put_connection(conn)
        return result

    async def get_data(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                       default: typing.Optional[str] = None) -> typing.Dict:
        chat, user = map(str, self.check_address(chat=chat, user=user))
        conn = await self.get_connection()
        result = await r.table(self._table).get(chat)[user]['data'].default(default or {}).run(conn)
        await self.put_connection(conn)
        return result

    async def set_state(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                        state: typing.Optional[typing.AnyStr] = None):
        chat, user = map(str, self.check_address(chat=chat, user=user))
        conn = await self.get_connection()
        if await r.table(self._table).get(chat).run(conn):
            await r.table(self._table).get(chat).update({user: {'state': state}}).run(conn)
        else:
            await r.table(self._table).insert({'id': chat, user: {'state': state}}).run(conn)
        await self.put_connection(conn)

    async def set_data(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                       data: typing.Dict = None):
        chat, user = map(str, self.check_address(chat=chat, user=user))
        conn = await self.get_connection()
        if await r.table(self._table).get(chat).run(conn):
            await r.table(self._table).get(chat).update({user: {'data': r.literal(data)}}).run(conn)
        else:
            await r.table(self._table).insert({'id': chat, user: {'data': data}}).run(conn)
        await self.put_connection(conn)

    async def update_data(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                          data: typing.Dict = None,
                          **kwargs):
        chat, user = map(str, self.check_address(chat=chat, user=user))
        conn = await self.get_connection()
        if await r.table(self._table).get(chat).run(conn):
            await r.table(self._table).get(chat).update({user: {'data': data}}).run(conn)
        else:
            await r.table(self._table).insert({'id': chat, user: {'data': data}}).run(conn)
        await self.put_connection(conn)

    def has_bucket(self):
        return True

    async def get_bucket(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                         default: typing.Optional[dict] = None) -> typing.Dict:
        chat, user = map(str, self.check_address(chat=chat, user=user))
        conn = await self.get_connection()
        result = await r.table(self._table).get(chat)[user]['bucket'].default(default or {}).run(conn)
        await self.put_connection(conn)
        return result

    async def set_bucket(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                         bucket: typing.Dict = None):
        chat, user = map(str, self.check_address(chat=chat, user=user))
        conn = await self.get_connection()
        if await r.table(self._table).get(chat).run(conn):
            await r.table(self._table).get(chat).update({user: {'bucket': r.literal(bucket)}}).run(conn)
        else:
            await r.table(self._table).insert({'id': chat, user: {'bucket': bucket}}).run(conn)
        await self.put_connection(conn)

    async def update_bucket(self, *, chat: typing.Union[str, int, None] = None,
                            user: typing.Union[str, int, None] = None, bucket: typing.Dict = None,
                            **kwargs):
        chat, user = map(str, self.check_address(chat=chat, user=user))
        conn = await self.get_connection()
        if await r.table(self._table).get(chat).run(conn):
            await r.table(self._table).get(chat).update({user: {'bucket': bucket}}).run(conn)
        else:
            await r.table(self._table).insert({'id': chat, user: {'bucket': bucket}}).run(conn)
        await self.put_connection(conn)

    async def get_states_list(self) -> typing.List[typing.Tuple[int, int]]:
        """
        Get list of all stored chat's and user's

        :return: list of tuples where first element is chat id and second is user id
        """
        conn = await self.get_connection()
        result = []

        items = (await r.table(self._table).run(conn)).items

        for item in items:
            chat = int(item.pop('id'))
            for key in item.keys():
                user = int(key)
                result.append((chat, user))

        await self.put_connection(conn)

        return result

    async def reset_all(self):
        """
        Reset states in DB
        """
        conn = await self.get_connection()
        await r.table(self._table).delete().run(conn)
        await self.put_connection(conn)
