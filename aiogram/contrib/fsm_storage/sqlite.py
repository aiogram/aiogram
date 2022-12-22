import typing
import pickle
import aiosqlite
from ...dispatcher.storage import BaseStorage


class SqliteStorage(BaseStorage):
    def __init__(self, db_name: str = 'aiogram_fsm_storage.db', tbl_name: str = 'aiogram_fsm'):
        self._db_name = db_name
        self._tbl_name = tbl_name
        self._conn = None
        
    async def _get_connect(self) -> aiosqlite.Connection:
        if self._conn:
            return self._conn
        self._conn = await aiosqlite.connect(self._db_name)
        await self._conn.execute(f'CREATE TABLE IF NOT EXISTS {self._tbl_name}(chat INTEGER, user INTEGER, state VARCHAR(255), data BLOB, bucket BLOB)')
        await self._conn.commit()
        return self._conn

    async def _has_in_db(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None) -> bool:
        conn = self._conn or await self._get_connect()
        cursor = await conn.execute(f'SELECT EXISTS(SELECT * FROM {self._tbl_name} WHERE chat=? AND user=?)', (chat, user))
        return (await cursor.fetchone())[0]

    async def close(self):
        if self._conn:
            await self._conn.close()

    async def wait_closed(self):
        pass

    async def get_state(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None, default: typing.Optional[str] = None) -> typing.Optional[str]:
        chat, user = self.check_address(chat=chat, user=user)
        conn = self._conn or await self._get_connect()
        cursor = await conn.execute(f'SELECT state FROM {self._tbl_name} WHERE chat=? AND user=?', (chat, user))
        state = (await cursor.fetchone() or [None])[0]
        return state if state else self.resolve_state(default)

    async def get_data(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None, default: typing.Optional[typing.Dict] = None) -> typing.Dict:
        chat, user = self.check_address(chat=chat, user=user)
        conn = self._conn or await self._get_connect()
        cursor = await conn.execute(f'SELECT data FROM {self._tbl_name} WHERE chat=? AND user=?', (chat, user))
        data = (await cursor.fetchone() or [None])[0]
        return pickle.loads(data) if data else default or {}

    async def set_state(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None, state: typing.Optional[typing.AnyStr] = None):
        chat, user = self.check_address(chat=chat, user=user)
        conn = self._conn or await self._get_connect()
        if await self._has_in_db(chat=chat, user=user):
            await conn.execute(f'UPDATE {self._tbl_name} SET state=? WHERE chat=? AND user=?', (self.resolve_state(state), chat, user))
        else:
            await conn.execute(f'INSERT INTO {self._tbl_name}(chat, user, state) VALUES(?, ?, ?)', (chat, user, self.resolve_state(state)))
        await conn.commit()

    async def set_data(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None, data: typing.Dict = None):
        chat, user = self.check_address(chat=chat, user=user)
        conn = self._conn or await self._get_connect()
        if await self._has_in_db(chat=chat, user=user):
            await conn.execute(f'UPDATE {self._tbl_name} SET data=? WHERE chat=? AND user=?', (pickle.dumps(data) if data else None, chat, user))
        else:
            await conn.execute(f'INSERT INTO {self._tbl_name}(chat, user, data) VALUES(?, ?, ?)', (chat, user, pickle.dumps(data) if data else None))
        await conn.commit()

    async def update_data(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None, data: typing.Dict, **kwargs):
        chat, user = self.check_address(chat=chat, user=user)
        _data = await self.get_data(chat=chat, user=user)
        if data: _data.update(data)
        _data.update(kwargs)
        await self.set_data(chat=chat, user=user, data=_data)

    def has_bucket(self):
        return True

    async def get_bucket(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None, default: typing.Optional[dict] = None) -> typing.Dict:
        chat, user = self.check_address(chat=chat, user=user)
        conn = self._conn or await self._get_connect()
        cursor = await conn.execute(f'SELECT bucket FROM {self._tbl_name} WHERE chat=? AND user=?', (chat, user))
        bucket = (await cursor.fetchone() or [None])[0]
        return pickle.loads(bucket) if bucket else default or {}

    async def set_bucket(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None, bucket: typing.Optional[dict] = None):
        chat, user = self.check_address(chat=chat, user=user)
        conn = self._conn or await self._get_connect()
        if await self._has_in_db(chat=chat, user=user):
            await conn.execute(f'UPDATE {self._tbl_name} SET bucket=? WHERE chat=? AND user=?', (pickle.dumps(bucket) if bucket else None, chat, user))
        else:
            await conn.execute(f'INSERT INTO {self._tbl_name}(chat, user, bucket) VALUES(?, ?, ?)', (chat, user, pickle.dumps(bucket) if bucket else None))
        await conn.commit()

    async def update_bucket(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None, bucket: typing.Optional[dict] = None, **kwargs):
        chat, user = self.check_address(chat=chat, user=user)
        _bucket = await self.get_bucket(chat=chat, user=user)
        if bucket: _bucket.update(bucket)
        _bucket.update(kwargs)
        await self.set_bucket(chat=chat, user=user, bucket=_bucket)
