from typing import Any, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

from aiogram.fsm.state import State
from aiogram.fsm.storage.base import (
    BaseStorage,
    DefaultKeyBuilder,
    KeyBuilder,
    StateType,
    StorageKey,
)


class MongoStorage(BaseStorage):
    """
    MongoDB storage required :code:`motor` package installed (:code:`pip install motor`)
    """

    def __init__(
        self,
        client: AsyncIOMotorClient,
        key_builder: Optional[KeyBuilder] = None,
        db_name: str = "aiogram_fsm",
        states_collection_name: str = "states",
        data_collection_name: str = "data",
    ) -> None:
        """
        :param client: Instance of AsyncIOMotorClient
        :param key_builder: builder that helps to convert contextual key to string
        :param db_name: name of the MongoDB database for FSM
        :param states_collection_name: name of the collection for storing FSM states.
        :param data_collection_name: name of the collection for storing additional data.
        """
        if key_builder is None:
            key_builder = DefaultKeyBuilder()
        self._client = client
        self._db_name = db_name
        self._states_collection: AsyncIOMotorCollection = self._client[db_name][
            states_collection_name
        ]
        self._data_collection: AsyncIOMotorCollection = self._client[db_name][data_collection_name]
        self._key_builder = key_builder

    @classmethod
    def from_url(
        cls, url: str, connection_kwargs: Dict[str, Any] = {}, **kwargs: Any
    ) -> "MongoStorage":
        """
        Create an instance of :class:`MongoStorage` with specifying the connection string

        :param url: for example :code:`mongodb://user:password@host:port`
        :param connection_kwargs: see :code:`motor` docs
        :param kwargs: arguments to be passed to :class:`MongoStorage`
        :return: an instance of :class:`MongoStorage`
        """
        client = AsyncIOMotorClient(url, **connection_kwargs)
        return cls(client=client, **kwargs)

    async def close(self) -> None:
        """Cleanup client resources and disconnect from MongoDB."""
        self._client.close()

    def resolve_state(self, value: StateType) -> Optional[str]:
        if value is None:
            return None
        elif isinstance(value, State):
            return value.state
        return str(value)

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        document_id = self._key_builder.build(key, "state")
        if state is None:
            await self._states_collection.delete_one({"_id": document_id})
        else:
            await self._states_collection.update_one(
                {"_id": document_id},
                {"$set": {"state": self.resolve_state(state)}},
                upsert=True,
            )

    async def get_state(self, key: StorageKey) -> Optional[str]:
        document_id = self._key_builder.build(key, "state")
        document = await self._states_collection.find_one({"_id": document_id})
        if document is None or document["state"] is None:
            return None
        else:
            return str(document["state"])

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        document_id = self._key_builder.build(key, "data")
        if not data:
            await self._data_collection.delete_one({"_id": document_id})
        else:
            await self._data_collection.update_one(
                {"_id": document_id},
                {"$set": data},
                upsert=True,
            )

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        document_id = self._key_builder.build(key, "data")
        document = await self._data_collection.find_one({"_id": document_id}, {"_id": 0})
        if not document:
            return {}
        else:
            return document  # type: ignore

    async def update_data(self, key: StorageKey, data: Dict[str, Any]) -> Dict[str, Any]:
        document_id = self._key_builder.build(key, "data")
        update_result = await self._data_collection.find_one_and_update(
            {"_id": document_id},
            {"$set": data},
            upsert=True,
            return_document=True,
            projection={"_id": 0},
        )
        if not update_result:
            await self._data_collection.delete_one({"_id": document_id})
        return update_result  # type: ignore
