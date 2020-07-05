import copy
import typing

from ...dispatcher.storage import BaseStorage
from aiogram.utils.deprecated import renamed_argument


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

    @renamed_argument(old_name='user', new_name='user_id', until_version='3.0', stacklevel=3)
    @renamed_argument(old_name='chat', new_name='chat_id', until_version='3.0', stacklevel=4)
    def resolve_address(self, chat_id, user_id):
        chat_id, user_id = map(str, self.check_address(chat_id=chat_id, user_id=user_id))

        if chat_id not in self.data:
            self.data[chat_id] = {}
        if user_id not in self.data[chat_id]:
            self.data[chat_id][user_id] = {'state': None, 'data': {}, 'bucket': {}}

        return chat_id, user_id

    @renamed_argument(old_name='user', new_name='user_id', until_version='3.0', stacklevel=3)
    @renamed_argument(old_name='chat', new_name='chat_id', until_version='3.0', stacklevel=4)
    async def get_state(self, *,
                        chat_id: typing.Union[str, int, None] = None,
                        user_id: typing.Union[str, int, None] = None,
                        default: typing.Optional[str] = None) -> typing.Optional[str]:
        chat_id, user_id = self.resolve_address(chat_id=chat_id, user_id=user_id)
        return self.data[chat_id][user_id]['state']

    @renamed_argument(old_name='user', new_name='user_id', until_version='3.0', stacklevel=3)
    @renamed_argument(old_name='chat', new_name='chat_id', until_version='3.0', stacklevel=4)
    async def get_data(self, *,
                       chat_id: typing.Union[str, int, None] = None,
                       user_id: typing.Union[str, int, None] = None,
                       default: typing.Optional[str] = None) -> typing.Dict:
        chat_id, user_id = self.resolve_address(chat_id=chat_id, user_id=user_id)
        return copy.deepcopy(self.data[chat_id][user_id]['data'])

    @renamed_argument(old_name='user', new_name='user_id', until_version='3.0', stacklevel=3)
    @renamed_argument(old_name='chat', new_name='chat_id', until_version='3.0', stacklevel=4)
    async def update_data(self, *,
                          chat_id: typing.Union[str, int, None] = None,
                          user_id: typing.Union[str, int, None] = None,
                          data: typing.Dict = None, **kwargs):
        if data is None:
            data = {}
        chat_id, user_id = self.resolve_address(chat_id=chat_id, user_id=user_id)
        self.data[chat_id][user_id]['data'].update(data, **kwargs)

    @renamed_argument(old_name='user', new_name='user_id', until_version='3.0', stacklevel=3)
    @renamed_argument(old_name='chat', new_name='chat_id', until_version='3.0', stacklevel=4)
    async def set_state(self, *,
                        chat_id: typing.Union[str, int, None] = None,
                        user_id: typing.Union[str, int, None] = None,
                        state: typing.AnyStr = None):
        chat_id, user_id = self.resolve_address(chat_id=chat_id, user_id=user_id)
        self.data[chat_id][user_id]['state'] = state

    @renamed_argument(old_name='user', new_name='user_id', until_version='3.0', stacklevel=3)
    @renamed_argument(old_name='chat', new_name='chat_id', until_version='3.0', stacklevel=4)
    async def set_data(self, *,
                       chat_id: typing.Union[str, int, None] = None,
                       user_id: typing.Union[str, int, None] = None,
                       data: typing.Dict = None):
        chat_id, user_id = self.resolve_address(chat_id=chat_id, user_id=user_id)
        self.data[chat_id][user_id]['data'] = copy.deepcopy(data)

    @renamed_argument(old_name='user', new_name='user_id', until_version='3.0', stacklevel=3)
    @renamed_argument(old_name='chat', new_name='chat_id', until_version='3.0', stacklevel=4)
    async def reset_state(self, *,
                          chat_id: typing.Union[str, int, None] = None,
                          user_id: typing.Union[str, int, None] = None,
                          with_data: typing.Optional[bool] = True):
        await self.set_state(chat_id=chat_id, user_id=user_id, state=None)
        if with_data:
            await self.set_data(chat_id=chat_id, user_id=user_id, data={})

    def has_bucket(self):
        return True

    @renamed_argument(old_name='user', new_name='user_id', until_version='3.0', stacklevel=3)
    @renamed_argument(old_name='chat', new_name='chat_id', until_version='3.0', stacklevel=4)
    async def get_bucket(self, *,
                         chat_id: typing.Union[str, int, None] = None,
                         user_id: typing.Union[str, int, None] = None,
                         default: typing.Optional[dict] = None) -> typing.Dict:
        chat_id, user_id = self.resolve_address(chat_id=chat_id, user_id=user_id)
        return copy.deepcopy(self.data[chat_id][user_id]['bucket'])

    @renamed_argument(old_name='user', new_name='user_id', until_version='3.0', stacklevel=3)
    @renamed_argument(old_name='chat', new_name='chat_id', until_version='3.0', stacklevel=4)
    async def set_bucket(self, *,
                         chat_id: typing.Union[str, int, None] = None,
                         user_id: typing.Union[str, int, None] = None,
                         bucket: typing.Dict = None):
        chat_id, user_id = self.resolve_address(chat_id=chat_id, user_id=user_id)
        self.data[chat_id][user_id]['bucket'] = copy.deepcopy(bucket)

    @renamed_argument(old_name='user', new_name='user_id', until_version='3.0', stacklevel=3)
    @renamed_argument(old_name='chat', new_name='chat_id', until_version='3.0', stacklevel=4)
    async def update_bucket(self, *,
                            chat_id: typing.Union[str, int, None] = None,
                            user_id: typing.Union[str, int, None] = None,
                            bucket: typing.Dict = None, **kwargs):
        if bucket is None:
            bucket = {}
        chat_id, user_id = self.resolve_address(chat_id=chat_id, user_id=user_id)
        self.data[chat_id][user_id]['bucket'].update(bucket, **kwargs)
