"""
This module has dynamodb storage for finite-state machine
    based on `aiodynamo <https://github.com/HENNGE/aiodynamo>`_ driver
"""

from typing import Any, AnyStr, Dict, Optional, Tuple, Union

from aiohttp import ClientSession

try:
    from aiodynamo.client import Client, Table, URL
    from aiodynamo.credentials import Credentials
    from aiodynamo.errors import ItemNotFound
    from aiodynamo.http.aiohttp import AIOHTTP
    from aiodynamo.models import (
        KeySchema,
        KeySpec,
        KeyType,
        PayPerRequest,
        RetryConfig,
        Throughput,
    )
    from aiodynamo.types import NumericTypeConverter
except ModuleNotFoundError as e:
    import warnings

    warnings.warn("Install aiodynamo with `pip install aiodynamo`")
    raise e

from ...dispatcher.storage import BaseStorage

TABLE_PREFIX = "aiogram_fsm"
STATE = "state"
DATA = "data"
BUCKET = "bucket"


class DynamoDBStorage(BaseStorage):
    def __init__(
        self,
        *,
        credentials: Optional[Credentials] = None,
        region: str,
        endpoint: Union[URL, str, None] = None,
        numeric_type: NumericTypeConverter = float,
        throttle_config: RetryConfig = RetryConfig.default(),
        table_prefix: str = TABLE_PREFIX,
        table_throughput: Union[Throughput, PayPerRequest, None] = None,
    ):
        if not credentials:
            credentials = Credentials.auto()
        if isinstance(endpoint, str):
            endpoint = URL(endpoint)
        if not table_throughput:
            table_throughput = Throughput(read=5, write=5)

        self._client_session = ClientSession()
        self._dynamo = Client(
            AIOHTTP(self._client_session),
            credentials,
            region,
            endpoint,
            numeric_type,
            throttle_config,
        )
        self._table_prefix = table_prefix
        self._table_throughput = table_throughput

    def resolve_address(
        self, *, chat: Union[str, int, None], user: Union[str, int, None]
    ) -> Tuple[str, str]:
        chat, user = map(str, self.check_address(chat=chat, user=user))
        return chat, user

    async def get_table(self, name: str) -> Table:
        table = self._dynamo.table("_".join([self._table_prefix, name]))
        if not await table.exists():
            await table.create(
                self._table_throughput,
                KeySchema(
                    KeySpec("chat", KeyType.string),
                    KeySpec("user", KeyType.string),
                ),
            )
        return table

    @staticmethod
    async def get_item(table: Table, key: Dict[str, str]) -> Optional[Dict[str, Any]]:
        try:
            return await table.get_item(key)
        except ItemNotFound:
            pass

    async def close(self):
        await self._client_session.close()

    async def wait_closed(self):
        pass

    async def set_state(
        self,
        *,
        chat: Union[str, int, None] = None,
        user: Union[str, int, None] = None,
        state: Optional[AnyStr] = None,
    ):
        chat, user = self.resolve_address(chat=chat, user=user)
        table = await self.get_table(STATE)

        if state is None:
            await table.delete_item({"chat": chat, "user": user})
        else:
            await table.put_item(
                {
                    "chat": chat,
                    "user": user,
                    "state": self.resolve_state(state),
                },
            )

    async def get_state(
        self,
        *,
        chat: Union[str, int, None] = None,
        user: Union[str, int, None] = None,
        default: Optional[str] = None,
    ) -> Optional[str]:
        chat, user = self.resolve_address(chat=chat, user=user)
        table = await self.get_table(STATE)
        result = await self.get_item(table, {"chat": chat, "user": user})

        return result.get("state") if result else self.resolve_state(default)

    async def set_data(
        self,
        *,
        chat: Union[str, int, None] = None,
        user: Union[str, int, None] = None,
        data: Dict = None,
    ):
        chat, user = self.resolve_address(chat=chat, user=user)
        table = await self.get_table(DATA)
        if not data:
            await table.delete_item({"chat": chat, "user": user})
        else:
            await table.put_item({"chat": chat, "user": user, "data": data})

    async def get_data(
        self,
        *,
        chat: Union[str, int, None] = None,
        user: Union[str, int, None] = None,
        default: Optional[dict] = None,
    ) -> Dict:
        chat, user = self.resolve_address(chat=chat, user=user)
        table = await self.get_table(DATA)
        result = await self.get_item(table, {"chat": chat, "user": user})
        return (result.get("data") if result else default) or {}

    async def update_data(
        self,
        *,
        chat: Union[str, int, None] = None,
        user: Union[str, int, None] = None,
        data: Dict = None,
        **kwargs,
    ):
        if data is None:
            data = {}
        temp_data = await self.get_data(chat=chat, user=user, default={})
        temp_data.update(data, **kwargs)
        await self.set_data(chat=chat, user=user, data=temp_data)

    def has_bucket(self):
        return True

    async def get_bucket(
        self,
        *,
        chat: Union[str, int, None] = None,
        user: Union[str, int, None] = None,
        default: Optional[dict] = None,
    ) -> Dict:
        chat, user = self.resolve_address(chat=chat, user=user)
        table = await self.get_table(BUCKET)
        result = await self.get_item(table, {"chat": chat, "user": user})
        return (result.get("bucket") if result else default) or {}

    async def set_bucket(
        self,
        *,
        chat: Union[str, int, None] = None,
        user: Union[str, int, None] = None,
        bucket: Dict = None,
    ):
        chat, user = self.resolve_address(chat=chat, user=user)
        table = await self.get_table(BUCKET)

        await table.put_item({"chat": chat, "user": user, "bucket": bucket})

    async def update_bucket(
        self,
        *,
        chat: Union[str, int, None] = None,
        user: Union[str, int, None] = None,
        bucket: Dict = None,
        **kwargs,
    ):
        if bucket is None:
            bucket = {}
        temp_bucket = await self.get_bucket(chat=chat, user=user)
        temp_bucket.update(bucket, **kwargs)
        await self.set_bucket(chat=chat, user=user, bucket=temp_bucket)
