import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorClient  # type: ignore

from aiogram import Bot
from aiogram.dispatcher.fsm.state import State
from aiogram.dispatcher.fsm.storage.base import DEFAULT_DESTINY, BaseStorage, StateType, StorageKey

STATE = "aiogram_state"
DATA = "aiogram_data"
BUCKET = "aiogram_bucket"
COLLECTIONS = (STATE, DATA, BUCKET)


class MongoStorage(BaseStorage):
    """
    Mongo storage required :code:`motor` package installed (:code:`pip install motor`)
    """

    def __init__(
        self,
        mongo: AsyncIOMotorClient,
        db_name: str = "aiogram_fsm",
        with_bot_id: bool = True,
        with_destiny: bool = True,
    ) -> None:
        """
        :param mongo: Instance of mongo connection
        :param with_bot_id: include Bot id in the database
        :param with_destiny: include destiny in the database

        """
        self._mongo = mongo
        self._db = mongo.get_database(db_name)
        self._with_bot_id = with_bot_id
        self._with_destiny = with_destiny
        self._lock = asyncio.Lock()

    @classmethod
    def from_url(
        cls,
        url: str,
        db_name: str = "aiogram_fsm",
        with_bot_id: bool = True,
        with_destiny: bool = True,
    ) -> "MongoStorage":
        """
        Create an instance of :class:`MongoStorage` with specifying the connection string

        :param url: for example :code:`mongodb://user:password@host:port`
        :param db_name: name of database to store aiogram data`
        :param with_bot_id: include Bot id in the database
        :param with_destiny: include destiny in the database

        """

        return cls(
            mongo=AsyncIOMotorClient(url),
            db_name=db_name,
            with_bot_id=with_bot_id,
            with_destiny=with_destiny,
        )

    def _get_db_filter(self, key: StorageKey) -> Dict[str, Any]:
        db_filter: Dict[str, Any] = {"chat": key.chat_id, "user": key.user_id}
        if self._with_bot_id:
            db_filter["bot_id"] = key.bot_id

        if self._with_destiny:
            db_filter["destiny"] = key.destiny

        elif key.destiny != DEFAULT_DESTINY:
            raise ValueError(
                "Mongo storage is not configured to use key destiny other the default.\n"
                "\n"
                "Probably, you should set `with_destiny=True` in for MongoStorage.\n"
                "E.g: `MongoStorage(mongo_client, ..., with_destiny=True)`"
            )

        return db_filter

    async def close(self) -> None:
        await self._mongo.close()

    @asynccontextmanager
    async def lock(
        self,
        bot: Bot,
        key: StorageKey,
    ) -> AsyncGenerator[None, None]:
        async with self._lock:
            yield None

    async def set_state(
        self,
        bot: Bot,
        key: StorageKey,
        state: StateType = None,
    ) -> None:

        if state is None:
            await self._db[STATE].delete_one(filter=self._get_db_filter(key))
        else:
            await self._db[STATE].update_one(
                filter=self._get_db_filter(key),
                update={"$set": {"state": state.state if isinstance(state, State) else state}},
                upsert=True,
            )

    async def get_state(
        self,
        bot: Bot,
        key: StorageKey,
    ) -> Optional[str]:
        result = await self._db[STATE].find_one(filter=self._get_db_filter(key))
        return result.get("state") if result else None

    async def set_data(
        self,
        bot: Bot,
        key: StorageKey,
        data: Dict[str, Any],
    ) -> None:
        await self._db[DATA].update_one(
            filter=self._get_db_filter(key),
            update={"$set": {"data": data}},
            upsert=True,
        )

    async def get_data(
        self,
        bot: Bot,
        key: StorageKey,
    ) -> Dict[str, Any]:
        result: Optional[Dict[str, Dict[str, Any]]] = await self._db[DATA].find_one(
            filter=self._get_db_filter(key)
        )

        return result.get("data") or {} if result else {}
