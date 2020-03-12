from __future__ import annotations

import warnings
from typing import Any, AsyncGenerator, Callable, Dict, Optional, Tuple, TypeVar, Union, cast

from httpx import AsyncClient

from aiogram.api.client.session.base import BaseSession
from aiogram.api.client.telegram import PRODUCTION, TelegramAPIServer
from aiogram.api.methods import Request, TelegramMethod
from aiogram.api.types import InputFile
from aiogram.utils.warnings import CodeHasNoEffect

T = TypeVar("T")


class HttpxSession(BaseSession):
    def __init__(
        self,
        api: TelegramAPIServer = PRODUCTION,
        json_loads: Optional[Callable] = None,
        json_dumps: Optional[Callable] = None,
    ):
        super(HttpxSession, self).__init__(
            api=api, json_loads=json_loads, json_dumps=json_dumps,
        )
        self._client: Optional[AsyncClient] = None

    async def create_session(self) -> AsyncClient:
        if self._client is None:
            self._client = AsyncClient()

        return self._client

    async def close(self):
        if self._client is not None:
            await self._client.aclose()

    def build_form_data(self, request: Request):
        form_data: Dict[str, Union[str, int, bool]] = {}
        files: Dict[str, Tuple[InputFile, str]] = {}

        for key, value in request.data.items():
            if value is None:
                continue
            form_data[key] = self.prepare_value(value)

        if request.files:
            for key, input_file in request.files.items():
                filename = input_file.filename or key
                files[key] = (input_file, filename)

        return form_data, files

    async def make_request(self, token: str, call: TelegramMethod[T]) -> T:
        session = await self.create_session()

        request = call.build_request()
        url = self.api.api_url(token=token, method=request.method)
        form_data, files = self.build_form_data(request)
        resp = await session.post(url=url, data=form_data, files=files)
        raw_result = resp.json()
        # we need cast because JSON can return list, but not in our Telegram API case
        raw_result = cast(Dict[str, Any], raw_result)

        response = call.build_response(raw_result)
        self.raise_for_status(response)
        return cast(T, response.result)

    async def stream_content(
        self, url: str, timeout: int, chunk_size: int
    ) -> AsyncGenerator[bytes, None]:
        warnings.warn("httpx doesn't support `chunk_size` yet", CodeHasNoEffect)
        session = await self.create_session()

        async with session.stream(method="GET", url=url, timeout=timeout) as resp:
            async for chunk in resp.aiter_bytes():
                yield chunk

    async def __aenter__(self) -> HttpxSession:
        await self.create_session()
        return self
