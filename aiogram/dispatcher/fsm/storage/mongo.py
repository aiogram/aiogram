from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, Optional

try:
    import motor
    from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
except ModuleNotFoundError as e:
    import warnings
    warnings.warn("Install motor with `pip install motor`")
    raise e

from aiogram import Bot
from aiogram.dispatcher.fsm.state import State
from aiogram.dispatcher.fsm.storage.base import BaseStorage, StateType, StorageKey

STATE = 'aiogram_state'
DATA = 'aiogram_data'
BUCKET = 'aiogram_bucket'
COLLECTIONS = (STATE, DATA, BUCKET)


class MongoStorage(BaseStorage):
    """
    Mongo storage required :code:`motor` package installed (:code:`pip install motor`)
    """

    def __init__(
        self,
        mongo: AsyncIOMotorClient,
        db_name: str = 'aiogram_fsm'
    ) -> None:
        """
        :param mongo: Instance of mongo connection

        """
        self._mongo = mongo
        self._db = mongo.get_database(db_name)

    @classmethod
    def from_url(
        cls, url: str, db_name: str = 'aiogram_fsm'
    ) -> "MongoStorage":
        """
        Create an instance of :class:`MongoStorage` with specifying the connection string

        :param url: for example :code:`mongodb://user:password@host:port`
        :param db_name: name of database to store aiogram data`

        """

        return cls(mongo=AsyncIOMotorClient(url), db_name=db_name)

    async def close(self) -> None:
        await self._mongo.close()

    @asynccontextmanager
    async def lock(
        self,
        bot: Bot,
        key: StorageKey,
    ) -> AsyncGenerator[None, None]:
        yield None

    async def set_state(
        self,
        bot: Bot,
        key: StorageKey,
        state: StateType = None,
    ) -> None:
        if state is None:
            await self._db[STATE].delete_one(filter={'chat': key.chat_id, 'user': key.user_id, 'bot_id': key.bot_id, 'destiny': key.destiny})
        else:
            await self._db[STATE].update_one(
                filter={'chat': key.chat_id, 'user': key.user_id, 'bot_id': key.bot_id, 'destiny': key.destiny},
                update={'$set': {'state': state.state if isinstance(state, State) else state}},
                upsert=True,
            )

    async def get_state(
        self,
        bot: Bot,
        key: StorageKey,
    ) -> Optional[str]:
        result = await self._db[STATE].find_one(filter={'chat': key.chat_id, 'user': key.user_id, 'bot_id': key.bot_id, 'destiny': key.destiny})
        return result.get('state') if result else None

    async def set_data(
        self,
        bot: Bot,
        key: StorageKey,
        data: Dict[str, Any],
    ) -> None:
        await self._db[DATA].insert_one(
            {'chat': key.chat_id, 'user': key.user_id, 'bot_id': key.bot_id, 'data': data, 'destiny': key.destiny}
        )

    async def get_data(
        self,
        bot: Bot,
        key: StorageKey,
    ) -> Dict[str, Any]:
        result = await self._db[DATA].find_one(filter={'chat': key.chat_id, 'user': key.user_id, 'bot_id': key.bot_id, 'destiny': key.destiny})

        return result.get('data') if result else {}
