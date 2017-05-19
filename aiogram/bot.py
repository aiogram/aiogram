import asyncio
import signal

import aiohttp

from . import api
from .api import ApiMethods
from .types.chat import Chat
from .types.user import User


class AIOGramBot:
    def __init__(self, token, loop=None, connections_limit=10):
        """
        :param token: 
        :param loop: 
        :param connections_limit: 
        """
        api.check_token(token)
        self.__token = token

        if loop is None:
            loop = asyncio.get_event_loop()

        self.loop = loop
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=connections_limit),
            loop=self.loop)

        self.loop.add_signal_handler(signal.SIGINT, self._on_exit)

    def _on_exit(self):
        self.session.close()

    def _prepare_object(self, obj):
        obj.bot = self
        return obj

    @property
    async def me(self) -> User:
        if not hasattr(self, '_me'):
            setattr(self, '_me', await self.get_me())
        return getattr(self, '_me')

    async def request(self, method, data=None):
        return await api.request(self.session, self.__token, method, data)

    async def get_me(self) -> User:
        raw = await self.request(ApiMethods.GET_ME)
        return self._prepare_object(User.de_json(raw))

    async def get_chat(self, chat_id) -> Chat:
        payload = {'chat_id': chat_id}
        raw = await self.request(ApiMethods.GET_CHAT, payload)
        return self._prepare_object(Chat.de_json(raw))
