from typing import Any, Dict, Mapping, Optional, cast

from aiosqlite import Connection, connect

from aiogram.fsm.state import State
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
        self._connection = connection

    @classmethod
    async def connect(cls, db_filename: str = SQLITE_FILENAME) -> "SqliteStorage":
        """
        Create an instance of :class:`SqliteStorage` with specifying the DB filename

        :param db_filename: for example :code:`aiogram_fsm.sqlite`
        :param connection_kwargs: see :code:`motor` docs
        :param kwargs: arguments to be passed to :class:`MongoStorage`
        :return: an instance of :class:`MongoStorage`
        """
        connection = await connect(db_filename)
        await connection.execute(
            f"""CREATE TABLE IF NOT EXISTS aiogram_fsm (
                    id TEXT PRIMARY KEY,
                    state TEXT,
                    data BLOB)"""
        )
        await connection.commit()
        return cls(connection=connection)

    async def close(self) -> None:
        await self._connection.close()

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        id = self._key_builder.build(key)
        state = cast(str, state.state if isinstance(state, State) else state)

        await self._connection.execute(
            f"""INSERT INTO aiogram_fsm (id, state)
                VALUES (?, ?)
                ON CONFLICT (id)
                DO UPDATE SET state = ?""",
            (id, state, state),
        )

        await self._connection.commit()

    async def get_state(self, key: StorageKey) -> Optional[str]:
        pass

    async def set_data(self, key: StorageKey, data: Mapping[str, Any]) -> None:
        pass

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        pass
