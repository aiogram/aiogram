from typing import Any, Dict, Optional

from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.storage.base import StateType
from aiogram.fsm.storage.base import StorageKey

try:
    from motor.motor_asyncio import AsyncIOMotorClient
    from motor.motor_asyncio import AsyncIOMotorDatabase
    from motor.motor_asyncio import AsyncIOMotorCollection
except ImportError:
    raise ModuleNotFoundError(
        "You do not have the `motor` module installed to work with MongoDB. Install it with `pip install aiogram[mongo]`"
    )


AIOGRAM_DATABASE_NAME: str = "aiogram-storage"
MONGODB_STATES_COLLECTION: str = "states"
MONGODB_DATA_COLLECTION: str = "data"


class MongoStorage(BaseStorage):
    """
    MongoDB storage for aiogram Finite State Machine (FSM).
    """

    _client: AsyncIOMotorClient
    _database: AsyncIOMotorDatabase
    _states_collection: AsyncIOMotorCollection
    _data_collection: AsyncIOMotorCollection

    def __init__(
        self,
        client: AsyncIOMotorClient,
        *,
        database_name: Optional[str] = None,
        state_collection_name: Optional[str] = None,
        data_collection_name: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        Initialize MongoStorage.

        :param client: AsyncIOMotorClient instance.
        :param database_name: Name of the MongoDB database.
        :param state_collection_name: Name of the collection for storing FSM states.
        :param data_collection_name: Name of the collection for storing additional data.
        :param kwargs: Additional parameters.
        """

        self._client: AsyncIOMotorClient = client
        self._database: AsyncIOMotorDatabase = self._client[database_name or AIOGRAM_DATABASE_NAME]
        self._states_collection: AsyncIOMotorCollection = self._database[
            state_collection_name or MONGODB_STATES_COLLECTION
        ]
        self._data_collection: AsyncIOMotorCollection = self._database[
            data_collection_name or MONGODB_DATA_COLLECTION
        ]

    @classmethod
    def from_url(
        cls,
        mongo_uri: str,
        *,
        database_name: Optional[str] = None,
        state_collection_name: Optional[str] = None,
        data_collection_name: Optional[str] = None,
        **kwargs,
    ) -> "MongoStorage":
        """
        Create MongoStorage instance from a MongoDB connection URI.

        :param mongo_uri: MongoDB connection URI.
        :param database_name: Name of the MongoDB database.
        :param state_collection_name: Name of the collection for storing FSM states.
        :param data_collection_name: Name of the collection for storing additional data.
        :param kwargs: Additional parameters.
        :return: MongoStorage instance.
        """

        client = AsyncIOMotorClient(mongo_uri)
        return cls(
            client=client,
            database_name=database_name,
            state_collection_name=state_collection_name,
            data_collection_name=data_collection_name,
            **kwargs,
        )

    @staticmethod
    def resolve_state(value) -> None | str:
        """
        Resolve the state value.

        :param value: State value to be resolved.
        :return: Resolved state value.
        """

        if value is None:
            return
        if isinstance(value, str):
            return value
        if isinstance(value, State):
            return value.state

    async def close(self) -> None:
        """
        Close the MongoDB client.
        """

        if self._client:
            self._client.close()

    async def wait_closed(self) -> bool:
        """
        Wait for the MongoDB client to be closed.

        :return: True if closed, False otherwise.
        """

        return True

    async def set_state(self, key: StorageKey, state: Optional[StateType] = None) -> None:
        """
        Set the FSM state for the specified key.

        :param key: StorageKey instance.
        :param state: FSM state to be set.
        """

        if state is None:
            await self._states_collection.delete_one(
                filter={"chat": key.chat_id, "user": key.user_id}
            )
        else:
            await self._states_collection.update_one(
                filter={"chat": key.chat_id, "user": key.user_id},
                update={"$set": {"state": self.resolve_state(state)}},
                upsert=True,
            )

    async def get_state(
        self, key: StorageKey, *, default: Optional[StateType] = None
    ) -> Optional[str]:
        """
        Get the FSM state for the specified key.

        :param key: StorageKey instance.
        :param default: Default state value if not found.
        :return: FSM state value.
        """

        state: dict = await self._states_collection.find_one(
            filter={"chat": key.chat_id, "user": key.user_id}
        )
        return state.get("state") if state else self.resolve_state(default)

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        """
        Set additional data for the specified key.

        :param key: StorageKey instance.
        :param data: Additional data to be set.
        """

        if not data:
            await self._data_collection.delete_one(
                filter={"chat": key.chat_id, "user": key.user_id}
            )
        else:
            await self._data_collection.update_one(
                filter={"chat": key.chat_id, "user": key.user_id},
                update={"$set": {"data": data}},
                upsert=True,
            )

    async def get_data(
        self, key: StorageKey, *, default: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get additional data for the specified key.

        :param key: StorageKey instance.
        :param default: Default data if not found.
        :return: Additional data.
        """

        data: dict = await self._data_collection.find_one(
            filter={"chat": key.chat_id, "user": key.user_id}
        )
        return data.get("data") if data else default or {}

    async def update_data(self, key: StorageKey, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update additional data for the specified key.

        :param key: StorageKey instance.
        :param data: Data to be updated.
        :return: Updated data.
        """

        updated_data: dict = await self.get_data(key)
        updated_data.update(data)
        await self.set_data(key, updated_data)
        return updated_data.copy()
