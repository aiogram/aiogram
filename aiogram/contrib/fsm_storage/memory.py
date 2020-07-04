import copy
import typing

from ...dispatcher.storage import BaseStorage


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

    def resolve_address(self, chat_id, user_id):
        chat_id, user_id = map(str, self.check_address(chat_id=chat_id, user_id=user_id))

        if chat_id not in self.data:
            self.data[chat_id] = {}
        if user_id not in self.data[chat_id]:
            self.data[chat_id][user_id] = {'state': None, 'data': {}, 'bucket': {}}

        return chat_id, user_id

    async def get_state(self, *,
                        chat_id: typing.Union[str, int, None] = None,
                        user_id: typing.Union[str, int, None] = None,
                        default: typing.Optional[str] = None) -> typing.Optional[str]:
        chat_id, user_id = self.resolve_address(chat_id=chat_id, user_id=user_id)
        return self.data[chat_id][user_id]['state']

    async def get_data(self, *,
                       chat_id: typing.Union[str, int, None] = None,
                       user_id: typing.Union[str, int, None] = None,
                       default: typing.Optional[str] = None) -> typing.Dict:
        chat_id, user_id = self.resolve_address(chat_id=chat_id, user_id=user_id)
        return copy.deepcopy(self.data[chat_id][user_id]['data'])

    async def update_data(self, *,
                          chat_id: typing.Union[str, int, None] = None,
                          user_id: typing.Union[str, int, None] = None,
                          data: typing.Dict = None, **kwargs):
        if data is None:
            data = {}
        chat_id, user_id = self.resolve_address(chat_id=chat_id, user_id=user_id)
        self.data[chat_id][user_id]['data'].update(data, **kwargs)

    async def set_state(self, *,
                        chat_id: typing.Union[str, int, None] = None,
                        user_id: typing.Union[str, int, None] = None,
                        state: typing.AnyStr = None):
        chat_id, user_id = self.resolve_address(chat_id=chat_id, user_id=user_id)
        self.data[chat_id][user_id]['state'] = state

    async def set_data(self, *,
                       chat_id: typing.Union[str, int, None] = None,
                       user_id: typing.Union[str, int, None] = None,
                       data: typing.Dict = None):
        chat_id, user_id = self.resolve_address(chat_id=chat_id, user_id=user_id)
        self.data[chat_id][user_id]['data'] = copy.deepcopy(data)

    async def reset_state(self, *,
                          chat_id: typing.Union[str, int, None] = None,
                          user_id: typing.Union[str, int, None] = None,
                          with_data: typing.Optional[bool] = True):
        await self.set_state(chat_id=chat_id, user_id=user_id, state=None)
        if with_data:
            await self.set_data(chat_id=chat_id, user_id=user_id, data={})

    def has_bucket(self):
        return True

    async def get_bucket(self, *,
                         chat_id: typing.Union[str, int, None] = None,
                         user_id: typing.Union[str, int, None] = None,
                         default: typing.Optional[dict] = None) -> typing.Dict:
        chat_id, user_id = self.resolve_address(chat_id=chat_id, user_id=user_id)
        return copy.deepcopy(self.data[chat_id][user_id]['bucket'])

    async def set_bucket(self, *,
                         chat_id: typing.Union[str, int, None] = None,
                         user_id: typing.Union[str, int, None] = None,
                         bucket: typing.Dict = None):
        chat_id, user_id = self.resolve_address(chat_id=chat_id, user_id=user_id)
        self.data[chat_id][user_id]['bucket'] = copy.deepcopy(bucket)

    async def update_bucket(self, *,
                            chat_id: typing.Union[str, int, None] = None,
                            user_id: typing.Union[str, int, None] = None,
                            bucket: typing.Dict = None, **kwargs):
        if bucket is None:
            bucket = {}
        chat_id, user_id = self.resolve_address(chat_id=chat_id, user_id=user_id)
        self.data[chat_id][user_id]['bucket'].update(bucket, **kwargs)
