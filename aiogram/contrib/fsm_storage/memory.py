import typing

from ...dispatcher import BaseStorage


class MemoryStorage(BaseStorage):
    """
    In-memory based states storage.

    This type of storage is not recommended for usage in bots, because you will lost all states after restarting.
    """

    async def wait_closed(self):
        pass

    async def close(self):
        self.data.clear()

    def __init__(self):
        self.data = {}

    def _get_chat(self, chat_id):
        chat_id = str(chat_id)
        if chat_id not in self.data:
            self.data[chat_id] = {}
        return self.data[chat_id]

    def _get_user(self, chat_id, user_id):
        chat = self._get_chat(chat_id)
        chat_id = str(chat_id)
        user_id = str(user_id)
        if user_id not in self.data[chat_id]:
            self.data[chat_id][user_id] = {'state': None, 'data': {}}
        return self.data[chat_id][user_id]

    async def get_state(self, *,
                        chat: typing.Union[str, int, None] = None,
                        user: typing.Union[str, int, None] = None,
                        default: typing.Optional[str] = None) -> typing.Optional[str]:
        chat, user = self.check_address(chat=chat, user=user)
        user = self._get_user(chat, user)
        return user['state']

    async def get_data(self, *,
                       chat: typing.Union[str, int, None] = None,
                       user: typing.Union[str, int, None] = None,
                       default: typing.Optional[str] = None) -> typing.Dict:
        chat, user = self.check_address(chat=chat, user=user)
        user = self._get_user(chat, user)
        return user['data']

    async def update_data(self, *,
                          chat: typing.Union[str, int, None] = None,
                          user: typing.Union[str, int, None] = None,
                          data: typing.Dict = None, **kwargs):
        chat, user = self.check_address(chat=chat, user=user)
        user = self._get_user(chat, user)
        if data is None:
            data = []
        user['data'].update(data, **kwargs)

    async def set_state(self, *,
                        chat: typing.Union[str, int, None] = None,
                        user: typing.Union[str, int, None] = None,
                        state: typing.AnyStr = None):
        chat, user = self.check_address(chat=chat, user=user)
        user = self._get_user(chat, user)
        user['state'] = state

    async def set_data(self, *,
                       chat: typing.Union[str, int, None] = None,
                       user: typing.Union[str, int, None] = None,
                       data: typing.Dict = None):
        chat, user = self.check_address(chat=chat, user=user)
        user = self._get_user(chat, user)
        user['data'] = data

    async def reset_state(self, *,
                          chat: typing.Union[str, int, None] = None,
                          user: typing.Union[str, int, None] = None,
                          with_data: typing.Optional[bool] = True):
        await self.set_state(chat=chat, user=user, state=None)
        if with_data:
            await self.set_data(chat=chat, user=user, data={})
