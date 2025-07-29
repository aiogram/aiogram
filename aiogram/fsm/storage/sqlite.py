from aiosqlite import connect, Connection
from typing import Any, Dict, Mapping, Optional, cast

from aiogram.fsm.storage.base import (
    BaseEventIsolation,
    BaseStorage,
    DefaultKeyBuilder,
    KeyBuilder,
    StateType,
    StorageKey,
)

SQLITE_FILENAME = "aiogram_fsm.sqlite"


class SqliteStorage(BaseStorage):
    """
    SQLite storage required :code:`aiosqlite` package installed (:code:`pip install aiosqlite`)
    """

    def __init__(
        self,
        connection: Connection,
        key_builder: Optional[KeyBuilder] = None,
    ) -> None:
        """
        Create an instance of :class:`SqliteStorage` with provided SQLite connection

        :param key_builder: builder that helps to convert contextual key to string
        :param db_filename: name of the SQLite database file for FSM
        """
        if key_builder is None:
            key_builder = DefaultKeyBuilder()
        self._key_builder = key_builder
        self.connection = connection

    @classmethod
    async def connect(cls, db_filename: str = SQLITE_FILENAME) -> Connection:
        """
        Create an instance of :class:`SqliteStorage` with specifying the DB filename

        :param db_filename: for example :code:`aiogram_fsm.sqlite`
        :param connection_kwargs: see :code:`motor` docs
        :param kwargs: arguments to be passed to :class:`MongoStorage`
        :return: an instance of :class:`MongoStorage`
        """
        connection = await connect(db_filename)
        await connection.execute(f'''CREATE TABLE IF NOT EXISTS aiogram_fsm (
                                    id TEXT PRIMARY KEY,
                                    state BLOB,
                                    data BLOB)''')
        await connection.commit()
        return cls(connection=connection)

    async def close(self) -> None:
        await self.connection.close()

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        pass

    async def get_state(self, key: StorageKey) -> Optional[str]:
        pass

    async def set_data(self, key: StorageKey, data: Mapping[str, Any]) -> None:
        pass

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        pass



