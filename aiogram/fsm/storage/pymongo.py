from typing import Any, Dict, Mapping, Optional, cast

from pymongo import AsyncMongoClient

from aiogram.exceptions import DataNotDictLikeError
from aiogram.fsm.state import State
from aiogram.fsm.storage.base import (
    BaseStorage,
    DefaultKeyBuilder,
    KeyBuilder,
    StateType,
    StorageKey,
)


class PyMongoStorage(BaseStorage):
    """
    MongoDB storage required :code:`pymongo` package installed (:code:`pip install pymongo`).
    """

    def __init__(
        self,
        client: AsyncMongoClient,
        key_builder: Optional[KeyBuilder] = None,
        db_name: str = "aiogram_fsm",
        collection_name: str = "states_and_data",
    ) -> None:
        """
        :param client: Instance of AsyncMongoClient
        :param key_builder: builder that helps to convert contextual key to string
        :param db_name: name of the MongoDB database for FSM
        :param collection_name: name of the collection for storing FSM states and data
        """
        if key_builder is None:
            key_builder = DefaultKeyBuilder()
        self._client = client
        self._database = self._client[db_name]
        self._collection = self._database[collection_name]
        self._key_builder = key_builder

    @classmethod
    def from_url(
        cls, url: str, connection_kwargs: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> "PyMongoStorage":
        """
        Create an instance of :class:`PyMongoStorage` with specifying the connection string

        :param url: for example :code:`mongodb://user:password@host:port`
        :param connection_kwargs: see :code:`pymongo` docs
        :param kwargs: arguments to be passed to :class:`PyMongoStorage`
        :return: an instance of :class:`PyMongoStorage`
        """
        if connection_kwargs is None:
            connection_kwargs = {}
        client = AsyncMongoClient(url, **connection_kwargs)
        return cls(client=client, **kwargs)

    async def close(self) -> None:
        """Cleanup client resources and disconnect from MongoDB."""
        return await self._client.close()

    def resolve_state(self, value: StateType) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, State):
            return value.state
        return str(value)

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        document_id = self._key_builder.build(key)
        if state is None:
            updated = await self._collection.find_one_and_update(
                filter={"_id": document_id},
                update={"$unset": {"state": 1}},
                projection={"_id": 0},
                return_document=True,
            )
            if updated == {}:
                await self._collection.delete_one({"_id": document_id})
        else:
            await self._collection.update_one(
                filter={"_id": document_id},
                update={"$set": {"state": self.resolve_state(state)}},
                upsert=True,
            )

    async def get_state(self, key: StorageKey) -> Optional[str]:
        document_id = self._key_builder.build(key)
        document = await self._collection.find_one({"_id": document_id})
        if document is None:
            return None
        return document.get("state")

    async def set_data(self, key: StorageKey, data: Mapping[str, Any]) -> None:
        if not isinstance(data, dict):
            raise DataNotDictLikeError(
                f"Data must be a dict or dict-like object, got {type(data).__name__}"
            )

        document_id = self._key_builder.build(key)
        if not data:
            updated = await self._collection.find_one_and_update(
                filter={"_id": document_id},
                update={"$unset": {"data": 1}},
                projection={"_id": 0},
                return_document=True,
            )
            if updated == {}:
                await self._collection.delete_one({"_id": document_id})
        else:
            await self._collection.update_one(
                filter={"_id": document_id},
                update={"$set": {"data": data}},
                upsert=True,
            )

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        document_id = self._key_builder.build(key)
        document = await self._collection.find_one({"_id": document_id})
        if document is None or not document.get("data"):
            return {}
        return cast(Dict[str, Any], document["data"])

    async def update_data(self, key: StorageKey, data: Mapping[str, Any]) -> Dict[str, Any]:
        document_id = self._key_builder.build(key)
        update_with = {f"data.{key}": value for key, value in data.items()}
        update_result = await self._collection.find_one_and_update(
            filter={"_id": document_id},
            update={"$set": update_with},
            upsert=True,
            return_document=True,
            projection={"_id": 0},
        )
        if not update_result:
            await self._collection.delete_one({"_id": document_id})
        return update_result.get("data", {})
