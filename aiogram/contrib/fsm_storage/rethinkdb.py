# -*- coding:utf-8; -*-
__all__ = ['RethinkDBStorage']

import asyncio
import typing

import rethinkdb as r

from ...dispatcher import BaseStorage


r.set_loop_type('asyncio')


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
                 user=None, password=None, timeout=20, ssl=None, loop=None):
        self._host = host
        self._port = port
        self._db = db
        self._table = table
        self._auth_key = auth_key
        self._user = user
        self._password = password
        self._timeout = timeout
        self._ssl = ssl or {}

        self._connection: r.Connection = None
        self._loop = loop or asyncio.get_event_loop()
        self._lock = asyncio.Lock(loop=self._loop)
    
    async def connection(self):
        """
        Get or create connection.
        """
        async with self._lock:  # thread-safe
            if not self._connection:
                self._connection = await r.connect(host=self._host, port=self._port, db=self._db, auth_key=self._auth_key, user=self._user,
                                                   password=self._password, timeout=self._timeout, ssl=self._ssl, io_loop=self._loop)
        return self._connection

    async def close(self):
        """
        Close connection.
        """
        if self._connection and self._connection.is_open():
            await self._connection.close()
            self._connection = None

    def wait_closed(self):
        """
        Checks if connection is closed.
        """
        if self._connection:
            raise ConnectionNotClosed
        return True

    async def get_state(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                        default: typing.Optional[str] = None) -> typing.Optional[str]:
        chat, user = map(str, self.check_address(chat=chat, user=user))
        conn = await self.connection()
        return await r.table(self._table).get(chat)[user]['state'].default(default or '').run(conn)

    async def get_data(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                       default: typing.Optional[str] = None) -> typing.Dict:
        chat, user = map(str, self.check_address(chat=chat, user=user))
        conn = await self.connection()
        return await r.table(self._table).get(chat)[user]['data'].default(default or {}).run(conn)

    async def set_state(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                        state: typing.Optional[typing.AnyStr] = None):
        chat, user = map(str, self.check_address(chat=chat, user=user))
        conn = await self.connection()
        # https://stackoverflow.com/questions/24306933/how-to-make-a-rethinkdb-atomic-update-if-document-exists-insert-otherwise
        await r.table(self._table).insert(
                {'id': chat, user: {'state': state}},
                conflict='update').run(conn)

    async def set_data(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None, data: typing.Dict = None):
        chat, user = map(str, self.check_address(chat=chat, user=user))
        conn = await self.connection()
        if await r.table(self._table).get(chat).run(conn):
            await r.table(self._table).get(chat).update({user: {'data': r.literal(data)}}).run(conn)
        else:
            await r.table(self._table).insert({'id': chat, user: {'data': data}}).run(conn)

    async def update_data(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None, data: typing.Dict = None,
                          **kwargs):
        chat, user = map(str, self.check_address(chat=chat, user=user))
        conn = await self.connection()
        await r.table(self._table).insert(
                {'id': chat, user: {'data': data}},
                conflict='update').run(conn)

    def has_bucket(self):
        return True

    async def get_bucket(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                         default: typing.Optional[dict] = None) -> typing.Dict:
        chat, user = map(str, self.check_address(chat=chat, user=user))
        conn = await self.connection()
        return await r.table(self._table).get(chat)[user]['bucket'].default(default or {}).run(conn)

    async def set_bucket(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None, bucket: typing.Dict = None):
        chat, user = map(str, self.check_address(chat=chat, user=user))
        conn = await self.connection()
        if await r.table(self._table).get(chat).run(conn):
            await r.table(self._table).get(chat).update({user: {'bucket': r.literal(bucket)}}).run(conn)
        else:
            await r.table(self._table).insert({'id': chat, user: {'bucket': bucket}}).run(conn)

    async def update_bucket(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None, bucket: typing.Dict = None,
                            **kwargs):
        chat, user = map(str, self.check_address(chat=chat, user=user))
        conn = await self.connection()
        await r.table(self._table).insert(
                {'id': chat, user: {'bucket': bucket}},
                conflict='update').run(conn)

    async def get_states_list(self) -> typing.List[typing.Tuple[int]]:
        """
        Get list of all stored chat's and user's

        :return: list of tuples where first element is chat id and second is user id
        """
        conn = await self.connection()
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
        conn = await self.connection()
        await r.table(self._table).delete().run(conn)
