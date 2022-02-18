import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, AsyncGenerator, Dict, Optional

from aiogram import Bot
from aiogram.dispatcher.fsm.state import State
from aiogram.dispatcher.fsm.storage.base import DEFAULT_DESTINY, BaseStorage, StateType, StorageKey
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase  # type: ignore
from pymongo.errors import InvalidOperation, DuplicateKeyError
from pymongo.results import UpdateResult

STATE = "aiogram_state"
DATA = "aiogram_data"
LOCK = "aiogram_lock"
COLLECTIONS = (STATE, DATA, LOCK)

DEFAULT_MONGO_LOCK = 60


class MongoStorage(BaseStorage):
    """
    Mongo storage required :code:`motor` package installed (:code:`pip install motor`)
    """

    def __init__(
            self,
            mongo: AsyncIOMotorClient,
            db: AsyncIOMotorDatabase,
            with_bot_id: bool = True,
            with_destiny: bool = True,
            state_ttl: Optional[int] = None,
            data_ttl: Optional[int] = None,
            lock_ttl: Optional[int] = None,
    ) -> None:
        self._mongo = mongo
        self._db = db
        self._with_bot_id = with_bot_id
        self._with_destiny = with_destiny
        self.state_ttl = state_ttl
        self.data_ttl = data_ttl
        self.lock_ttl = lock_ttl

    @classmethod
    async def from_url(
            cls,
            url: str,
            db_name: str = "aiogram_fsm",
            with_bot_id: bool = True,
            with_destiny: bool = True,
            state_ttl: Optional[int] = None,
            data_ttl: Optional[int] = None,
            lock_ttl: Optional[int] = DEFAULT_MONGO_LOCK,
    ) -> "MongoStorage":
        mongo = AsyncIOMotorClient(url)
        db = mongo.get_database(db_name)
        await MongoStorage._apply_indexes(db)
        return cls(
            mongo=AsyncIOMotorClient(url),
            db=db,
            with_bot_id=with_bot_id,
            with_destiny=with_destiny,
            state_ttl=state_ttl,
            data_ttl=data_ttl,
            lock_ttl=lock_ttl,
        )

    @staticmethod
    async def _apply_indexes(db: AsyncIOMotorDatabase) -> None:
        for collection in COLLECTIONS:
            await db[collection].create_index(
                keys=[('chat', 1), ('user', 1), ('bot_id', 1)],
                name="chat_user_bot_idx",
                unique=True,
                background=True,
            )
            await db[collection].create_index(
                keys=[("expireAt", 1)],
                name="lock_idx",
                expireAfterSeconds=0,
                background=True,
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

    def close(self) -> None:
        self._mongo.close()

    @asynccontextmanager
    async def lock(
            self,
            bot: Bot,
            key: StorageKey,
    ) -> AsyncGenerator[None, None]:
        async with DefaultMongoLock(self._db, LOCK, self._get_db_filter(key)):
            yield None

    async def set_state(
            self,
            bot: Bot,
            key: StorageKey,
            state: StateType = None,
    ) -> None:
        expiration = datetime.utcnow() + timedelta(seconds=self.state_ttl) if self.state_ttl else None

        query_data = {"state": state.state if isinstance(state, State) else state, "expireAt": expiration}

        if state is None:
            await self._db[STATE].delete_one(filter=self._get_db_filter(key))
        else:
            await self._db[STATE].update_one(
                filter=self._get_db_filter(key),
                update={"$set": query_data},
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
        expiration = datetime.utcnow() + timedelta(seconds=self.data_ttl) if self.data_ttl else None

        await self._db[DATA].update_one(
            filter=self._get_db_filter(key),
            update={"$set": {"data": data, "expireAt": expiration}},
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


class MongoLockException(Exception):
    pass


class DefaultMongoLock:

    def __init__(self,
                 db: AsyncIOMotorDatabase,
                 collection: str,
                 key: Dict[str, Any],
                 sleep: float = 0.1,
                 timeout: float = DEFAULT_MONGO_LOCK):
        self.sleep = sleep
        self.key = key
        self.collection = db[collection]
        self.timeout = timeout

    async def __aenter__(self):
        if await self.acquire():
            return self
        raise MongoLockException("Unable to acquire lock within the time specified")

    async def __aexit__(self, exc_t, exc_v, exc_tb):
        await self.release()

    async def acquire(self) -> bool:
        if await self.do_acquire():
            return True

        while True:
            if await self.do_acquire():
                return True

            await asyncio.sleep(self.sleep)

    async def do_acquire(self) -> bool:
        try:
            lock_dict = {
                'expireAt': datetime.utcnow() + timedelta(seconds=DEFAULT_MONGO_LOCK),
            }
            lock_dict.update(self.key)
            await self.collection.insert_one(lock_dict)
            return True
        except DuplicateKeyError:
            return False

    async def release(self) -> Optional[UpdateResult]:
        try:
            return await self.collection.delete_one(filter=self.key)
        except InvalidOperation:
            return None

    async def touch(self, timeout: float = DEFAULT_MONGO_LOCK) -> None:
        """Renew lock to avoid expiration. """
        lock = await self.collection.find_one(filter=self.key)
        if not lock:
            raise MongoLockException(u'Can\'t find lock for {key}'.format(key=self.key))
        if not lock['expireAt']:
            return
        expire = datetime.utcnow() + timedelta(seconds=timeout)
        await self.collection.update_one(
            filter=self.key,
            update={'$set': {'expireAt': expire}}
        )
