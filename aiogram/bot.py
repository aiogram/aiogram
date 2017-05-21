import asyncio

import aiohttp

from . import api
from .api import ApiMethods
from .types.chat import Chat
from .types.update import Update
from .types.user import User
from .utils.payload import generate_payload


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

    def __del__(self):
        self.session.close()

    @property
    async def me(self) -> User:
        if not hasattr(self, '_me'):
            setattr(self, '_me', await self.get_me())
        return getattr(self, '_me')

    async def request(self, method, data=None):
        return await api.request(self.session, self.__token, method, data)

    async def get_me(self) -> User:
        raw = await self.request(ApiMethods.GET_ME)
        return User.de_json(raw)

    async def get_chat(self, chat_id) -> Chat:
        payload = generate_payload(**locals())
        raw = await self.request(ApiMethods.GET_CHAT, payload)
        return Chat.de_json(raw)

    async def get_updates(self, offset=None, limit=None, timeout=None, allowed_updates=None):
        """
        offset	Integer	Optional	Identifier of the first update to be returned. Must be greater by one than the highest among the identifiers of previously received updates. By default, updates starting with the earliest unconfirmed update are returned. An update is considered confirmed as soon as getUpdates is called with an offset higher than its update_id. The negative offset can be specified to retrieve updates starting from -offset update from the end of the updates queue. All previous updates will forgotten.
        limit	Integer	Optional	Limits the number of updates to be retrieved. Values between 1—100 are accepted. Defaults to 100.
        timeout	Integer	Optional	Timeout in seconds for long polling. Defaults to 0, i.e. usual short polling. Should be positive, short polling should be used for testing purposes only.
        allowed_updates	Array of String	Optional	List the types of updates you want your bot to receive. For example, specify [“message”, “edited_channel_post”, “callback_query”] to only receive updates of these types. See Update for a complete list of available update types. Specify an empty list to receive all updates regardless of type (default). If not specified, the previous setting will be used.
        
        Please note that this parameter doesn't affect updates created before the call to the getUpdates, so unwanted updates may be received for a short period of time.
        :return: 
        """
        payload = generate_payload(**locals())
        raw = await self.request(ApiMethods.GET_UPDATES, payload)
        return [Update.de_json(raw_update) for raw_update in raw]
