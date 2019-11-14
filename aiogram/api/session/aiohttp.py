from typing import Optional, TypeVar

from aiohttp import ClientSession, FormData

from ..methods import Request, TelegramMethod
from .base import PRODUCTION, BaseSession, TelegramAPIServer

T = TypeVar("T")


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
                form.add_field(key, value)
            else:
                form.add_field(key, str(value))
        for key, value in request.files.items():
            form.add_field(key, value, filename=value.filename or key)
        return form

    async def make_request(self, token: str, call: TelegramMethod[T]) -> T:
        await self.create_session()

        request = call.build_request()
        url = self.api.api_url(token=token, method=request.method)
        form = self.build_form_data(request)

        async with self._session.post(url, data=form) as response:
            raw_result = await response.json()

        response = call.build_response(raw_result)
        self.raise_for_status(response)
        return response.result
