import asyncio
import signal

import aiohttp

from . import api
from .api import ApiMethods
from .types.chat import Chat
from .types.update import Update
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

    async def get_updates(self, offset=None, limit=None, timeout=None, allowed_updates=None):
        """
        offset	Integer	Optional	Identifier of the first update to be returned. Must be greater by one than the highest among the identifiers of previously received updates. By default, updates starting with the earliest unconfirmed update are returned. An update is considered confirmed as soon as getUpdates is called with an offset higher than its update_id. The negative offset can be specified to retrieve updates starting from -offset update from the end of the updates queue. All previous updates will forgotten.
        limit	Integer	Optional	Limits the number of updates to be retrieved. Values between 1—100 are accepted. Defaults to 100.
        timeout	Integer	Optional	Timeout in seconds for long polling. Defaults to 0, i.e. usual short polling. Should be positive, short polling should be used for testing purposes only.
        allowed_updates	Array of String	Optional	List the types of updates you want your bot to receive. For example, specify [“message”, “edited_channel_post”, “callback_query”] to only receive updates of these types. See Update for a complete list of available update types. Specify an empty list to receive all updates regardless of type (default). If not specified, the previous setting will be used.
        
        Please note that this parameter doesn't affect updates created before the call to the getUpdates, so unwanted updates may be received for a short period of time.
        :return: 
        """
        payload = {}

        if offset:
            payload['offset'] = offset
        if limit:
            payload['limit'] = limit
        if timeout:
            payload['timeout'] = timeout
        if allowed_updates:
            payload['allowed_updates'] = allowed_updates

        raw = await self.request(ApiMethods.GET_UPDATES, payload)
        return [Update.de_json(raw_update) for raw_update in raw]
