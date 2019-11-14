from typing import Optional, TypeVar, Callable

from aiohttp import ClientSession, FormData

from .base import PRODUCTION, BaseSession, TelegramAPIServer
from ..methods import Request, TelegramMethod

T = TypeVar("T")


class AiohttpSession(BaseSession):
    def __init__(
        self,
        api: TelegramAPIServer = PRODUCTION,
        json_loads: Optional[Callable] = None,
        json_dumps: Optional[Callable] = None,
    ):
        super(AiohttpSession, self).__init__(api=api, json_loads=json_loads, json_dumps=json_dumps)
        self._session: Optional[ClientSession] = None

    async def create_session(self):
        if self._session is None or self._session.closed:
            self._session = ClientSession()

    async def close(self):
        if self._session is not None and not self._session.closed:
            await self._session.close()

    def build_form_data(self, request: Request):
        form = FormData(quote_fields=False)
        for key, value in request.data.items():
            if value is None:
                continue
            form.add_field(key, self.prepare_value(value))
        if request.files:
            for key, value in request.files.items():
                form.add_field(key, value, filename=value.filename or key)
        return form

    async def make_request(self, token: str, call: TelegramMethod[T]) -> T:
        await self.create_session()

        request = call.build_request()
        url = self.api.api_url(token=token, method=request.method)
        form = self.build_form_data(request)

        async with self._session.post(url, data=form) as response:
            raw_result = await response.json(loads=self.json_loads)

        response = call.build_response(raw_result)
        self.raise_for_status(response)
        return response.result
