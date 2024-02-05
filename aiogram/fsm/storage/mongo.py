from typing import Any, Dict, Optional

from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.storage.base import StateType
from aiogram.fsm.storage.base import StorageKey

from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorDatabase
from motor.motor_asyncio import AsyncIOMotorCollection


AIOGRAM_DATABASE_NAME: str = "aiogram-storage"
MONGODB_STATES_COLLECTION: str = "states"
MONGODB_DATA_COLLECTION: str = "data"


class MongoStorage(BaseStorage):

    _client: AsyncIOMotorClient
    _database: AsyncIOMotorDatabase
    _state_collection: AsyncIOMotorCollection
    _data_collection: AsyncIOMotorCollection

    def __init__(self, client: AsyncIOMotorClient, *, database_name: Optional[str] = None, state_collection_name: Optional[str] = None, data_collection_name: Optional[str] = None, **kwargs) -> None:

        self._client: AsyncIOMotorClient = client
        self._database: AsyncIOMotorDatabase = self._client[database_name or AIOGRAM_DATABASE_NAME]
        self._states_collection: AsyncIOMotorCollection = self._database[state_collection_name or MONGODB_STATES_COLLECTION]
        self._data_collection: AsyncIOMotorCollection = self._database[data_collection_name or MONGODB_DATA_COLLECTION]

    @classmethod
    def from_url(cls, mongo_uri: str, *, database_name: Optional[str] = None, state_collection_name: Optional[str] = None, data_collection_name: Optional[str] = None, **kwargs) -> "MongoStorage":

        client = AsyncIOMotorClient(mongo_uri)
        return cls(client=client, database_name=database_name, state_collection_name=state_collection_name, data_collection_name=data_collection_name, **kwargs)

    @staticmethod
    def resolve_state(value) -> None | str:
        if value is None:
            return
        if isinstance(value, str):
            return value
        if isinstance(value, State):
            return value.state

    async def close(self) -> None:
        if self._client:
            self._client.close()

    async def wait_closed(self) -> bool:
        return True

    async def set_state(self, key: StorageKey, state: Optional[StateType] = None) -> None:

        if state is None:
            await self._states_collection.delete_one(filter={"chat": key.chat_id, "user": key.user_id})
        else:
            await self._states_collection.update_one(
                filter={"chat": key.chat_id, "user": key.user_id},
                update={"$set": {"state": self.resolve_state(state)}},
                upsert=True
            )

    async def get_state(self, key: StorageKey, *, default: Optional[StateType] = None) -> Optional[str]:

        state: dict = await self._states_collection.find_one(filter={"chat": key.chat_id, "user": key.user_id})
        return state.get("state") if state else self.resolve_state(default)

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:

        if not data:
            await self._data_collection.delete_one(filter={"chat": key.chat_id, "user": key.user_id})
        else:
            await self._data_collection.update_one(
                filter={"chat": key.chat_id, "user": key.user_id},
                update={"$set": {"data": data}},
                upsert=True
            )

    async def get_data(self, key: StorageKey, *, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:

        data: dict = await self._data_collection.find_one(filter={"chat": key.chat_id, "user": key.user_id})
        return data.get("data") if data else default or {}

    async def update_data(self, key: StorageKey, data: Dict[str, Any]) -> Dict[str, Any]:

        updated_data: dict = await self.get_data(key)
        updated_data.update(data)
        await self.set_data(key, updated_data)
        return updated_data.copy()
