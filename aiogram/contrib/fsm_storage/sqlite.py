import json
import typing
import sqlite3
from ...dispatcher.storage import BaseStorage


class SqliteStorage(BaseStorage):
    def __init__(self, db_name='aiogram_fsm_storage.db', tbl_name='aiogram_fsm'):
        self._db_name = db_name
        self._tbl_name = tbl_name
        self._conn = sqlite3.connect(db_name)
        self._cur = self._conn.cursor()

        self._cur.execute('SELECT tbl_name FROM sqlite_master WHERE type="table"')
        table_names = tuple(map(lambda row: row[0], self._cur.fetchall()))
        if tbl_name not in table_names:
            self._cur.execute(f'CREATE TABLE {tbl_name}(chat INTEGER, user INTEGER, state VARCHAR(255), data TEXT, bucket TEXT)')
            self._conn.commit()

    def _has_in_db(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None) -> bool:
        self._cur.execute(f'SELECT EXISTS(SELECT * FROM {self._tbl_name} WHERE chat=? AND user=?)', (chat, user))
        return self._cur.fetchone()[0]

    async def close(self):
        self._conn.close()

    async def wait_closed(self):
        return False

    async def get_state(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None, default: typing.Optional[str] = None) -> typing.Optional[str]:
        chat, user = self.check_address(chat=chat, user=user)
        if self._has_in_db(chat=chat, user=user):
            self._cur.execute(f'SELECT state FROM {self._tbl_name} WHERE chat=? AND user=?', (chat, user))
            return self._cur.fetchone()[0]
        else:
            return self.resolve_state(default)

    async def get_data(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None, default: typing.Optional[typing.Dict] = None) -> typing.Dict:
        chat, user = self.check_address(chat=chat, user=user)
        if self._has_in_db(chat=chat, user=user):
            self._cur.execute(f'SELECT data FROM {self._tbl_name} WHERE chat=? AND user=?', (chat, user))
            data = self._cur.fetchone()[0]
            return json.loads(data) if data else default or {}
        else:
            return default or {}

    async def set_state(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None, state: typing.Optional[typing.AnyStr] = None):
        chat, user = self.check_address(chat=chat, user=user)
        if self._has_in_db(chat=chat, user=user):
            self._cur.execute(f'UPDATE {self._tbl_name} SET state=? WHERE chat=? AND user=?', (self.resolve_state(state), chat, user))
        else:
            self._cur.execute(f'INSERT INTO {self._tbl_name}(chat, user, state) VALUES(?, ?, ?)', (chat, user, self.resolve_state(state)))
        self._conn.commit()

    async def set_data(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None, data: typing.Dict = None):
        chat, user = self.check_address(chat=chat, user=user)
        if self._has_in_db(chat=chat, user=user):
            self._cur.execute(f'UPDATE {self._tbl_name} SET data=? WHERE chat=? AND user=?', (json.dumps(data) if data else None, chat, user))
        else:
            self._cur.execute(f'INSERT INTO {self._tbl_name}(chat, user, data) VALUES(?, ?, ?)', (chat, user, json.dumps(data) if data else None))
        self._conn.commit()

    async def update_data(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None, data: typing.Dict, **kwargs):
        chat, user = self.check_address(chat=chat, user=user)
        _data = await self.get_data(chat=chat, user=user)
        _data.update(data, **kwargs)
        await self.set_data(chat=chat, user=user, data=_data)

    def has_bucket(self):
        return True

    async def get_bucket(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None, default: typing.Optional[dict] = None) -> typing.Dict:
        chat, user = self.check_address(chat=chat, user=user)
        if self._has_in_db(chat=chat, user=user):
            self._cur.execute(f'SELECT bucket FROM {self._tbl_name} WHERE chat=? AND user=?', (chat, user))
            bucket = self._cur.fetchone()[0]
            return json.loads(bucket) if bucket else default or {}
        else:
            return default or {}

    async def set_bucket(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None, bucket: typing.Optional[dict] = None):
        chat, user = self.check_address(chat=chat, user=user)
        if self._has_in_db(chat=chat, user=user):
            self._cur.execute(f'UPDATE {self._tbl_name} SET bucket=? WHERE chat=? AND user=?', (json.dumps(bucket) if bucket else None, chat, user))
        else:
            self._cur.execute(f'INSERT INTO {self._tbl_name}(chat, user, bucket) VALUES(?, ?, ?)', (chat, user, json.dumps(bucket) if bucket else None))
        self._conn.commit()

    async def update_bucket(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None, bucket: typing.Optional[dict] = None, **kwargs):
        chat, user = self.check_address(chat=chat, user=user)
        _bucket = await self.get_bucket(chat=chat, user=user)
        _bucket.update(bucket, **kwargs)
        await self.set_bucket(chat=chat, user=user, bucket=_bucket)
