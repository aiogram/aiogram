from typing import Optional, TypeVar

from aiohttp import ClientSession, FormData
from pydantic import BaseModel

from .base import BaseSession, TelegramAPIServer, PRODUCTION
from ..methods import TelegramMethod, Request

T = TypeVar('T')


class AiohttpSession(BaseSession):
    def __init__(self, api: TelegramAPIServer = PRODUCTION):
        super(AiohttpSession, self).__init__(api=api)
        self._session: Optional[ClientSession] = None

    async def create_session(self):
        if self._session is None or self._session.closed:
            self._session = ClientSession()

    async def close(self):
        if self._session is not None and not self._session.closed:
            await self._session.close()

    def build_form_data(self, request: Request):
        form = FormData()
        for key, value in request.data.items():
            if value is None:
                continue
            if isinstance(value, bool):
                print("elif isinstance(value, bool):", key, value)
                form.add_field(key, value)
            else:
                print("else:", key, value)
                form.add_field(key, str(value))
        return form

    async def make_request(self, token: str, call: TelegramMethod[T]) -> T:
        await self.create_session()

        request = call.build_request()
        url = self.api.api_url(token=token, method=request.method)
        form = self.build_form_data(request)

        async with self._session.post(url, data=form) as response:
            raw_result = await response.json()

        response = call.build_response(raw_result)
        if not response.ok:
            self.raise_for_status(response)
        return response.result
