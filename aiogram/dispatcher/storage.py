import copy
import typing

from ..utils.deprecated import warn_deprecated as warn
from ..utils.exceptions import FSMStorageWarning

# Leak bucket
KEY = 'key'
LAST_CALL = 'called_at'
RATE_LIMIT = 'rate_limit'
RESULT = 'result'
EXCEEDED_COUNT = 'exceeded'
DELTA = 'delta'
THROTTLE_MANAGER = '$throttle_manager'


class BaseStorage:
    """
    You are able to save current user's state
    and data for all steps in states-storage
    """

    async def close(self):
        """
        You have to override this method and use when application shutdowns.
        Perhaps you would like to save data and etc.

        :return:
        """
        raise NotImplementedError

    async def wait_closed(self):
        """
        You have to override this method for all asynchronous storages (e.g., Redis).

        :return:
        """
        raise NotImplementedError

    @classmethod
    def check_address(cls, *,
                      chat: typing.Union[str, int, None] = None,
                      user: typing.Union[str, int, None] = None) -> (typing.Union[str, int], typing.Union[str, int]):
        """
        In all storage's methods chat or user is always required.
        If one of them is not provided, you have to set missing value based on the provided one.

        This method performs the check described above.

        :param chat:
        :param user:
        :return:
        """
        if chat is None and user is None:
            raise ValueError('`user` or `chat` parameter is required but no one is provided!')

        if user is None and chat is not None:
            user = chat
        elif user is not None and chat is None:
            chat = user
        return chat, user

    async def get_state(self, *,
                        chat: typing.Union[str, int, None] = None,
                        user: typing.Union[str, int, None] = None,
                        default: typing.Optional[str] = None) -> typing.Optional[str]:
        """
        Get current state of user in chat. Return `default` if no record is found.

        Chat or user is always required. If one of them is not provided,
        you have to set missing value based on the provided one.

        :param chat:
        :param user:
        :param default:
        :return:
        """
        raise NotImplementedError

    async def get_data(self, *,
                       chat: typing.Union[str, int, None] = None,
                       user: typing.Union[str, int, None] = None,
                       default: typing.Optional[typing.Dict] = None) -> typing.Dict:
        """
        Get state-data for user in chat. Return `default` if no data is provided in storage.

        Chat or user is always required. If one of them is not provided,
        you have to set missing value based on the provided one.

        :param chat:
        :param user:
        :param default:
        :return:
        """
        raise NotImplementedError

    async def set_state(self, *,
                        chat: typing.Union[str, int, None] = None,
                        user: typing.Union[str, int, None] = None,
                        state: typing.Optional[typing.AnyStr] = None):
        """
        Set new state for user in chat

        Chat or user is always required. If one of them is not provided,
        you have to set missing value based on the provided one.

        :param chat:
        :param user:
        :param state:
        """
        raise NotImplementedError

    async def set_data(self, *,
                       chat: typing.Union[str, int, None] = None,
                       user: typing.Union[str, int, None] = None,
                       data: typing.Dict = None):
        """
        Set data for user in chat

        Chat or user is always required. If one of them is not provided,
        you have to set missing value based on the provided one.

        :param chat:
        :param user:
        :param data:
        """
        raise NotImplementedError

    async def update_data(self, *,
                          chat: typing.Union[str, int, None] = None,
                          user: typing.Union[str, int, None] = None,
                          data: typing.Dict = None,
                          **kwargs):
        """
        Update data for user in chat

        You can use data parameter or|and kwargs.

        Chat or user is always required. If one of them is not provided,
        you have to set missing value based on the provided one.

        :param data:
        :param chat:
        :param user:
        :param kwargs:
        :return:
        """
        raise NotImplementedError

    async def reset_data(self, *,
                         chat: typing.Union[str, int, None] = None,
                         user: typing.Union[str, int, None] = None):
        """
        Reset data for user in chat.

        Chat or user is always required. If one of them is not provided,
        you have to set missing value based on the provided one.

        :param chat:
        :param user:
        :return:
        """
        await self.set_data(chat=chat, user=user, data={})

    async def reset_state(self, *,
                          chat: typing.Union[str, int, None] = None,
                          user: typing.Union[str, int, None] = None,
                          with_data: typing.Optional[bool] = True):
        """
        Reset state for user in chat.
        You may desire to use this method when finishing conversations.

        Chat or user is always required. If one of this is not presented,
        you have to set missing value based on the provided one.

        :param chat:
        :param user:
        :param with_data:
        :return:
        """
        chat, user = self.check_address(chat=chat, user=user)
        await self.set_state(chat=chat, user=user, state=None)
        if with_data:
            await self.set_data(chat=chat, user=user, data={})

    async def finish(self, *,
                     chat: typing.Union[str, int, None] = None,
                     user: typing.Union[str, int, None] = None):
        """
        Finish conversation for user in chat.

        Chat or user is always required. If one of them is not provided,
        you have to set missing value based on the provided one.

        :param chat:
        :param user:
        :return:
        """
        await self.reset_state(chat=chat, user=user, with_data=True)

    def has_bucket(self):
        return False

    async def get_bucket(self, *,
                         chat: typing.Union[str, int, None] = None,
                         user: typing.Union[str, int, None] = None,
                         default: typing.Optional[dict] = None) -> typing.Dict:
        """
        Get bucket for user in chat. Return `default` if no data is provided in storage.

        Chat or user is always required. If one of them is not provided,
        you have to set missing value based on the provided one.

        :param chat:
        :param user:
        :param default:
        :return:
        """
        raise NotImplementedError

    async def set_bucket(self, *,
                         chat: typing.Union[str, int, None] = None,
                         user: typing.Union[str, int, None] = None,
                         bucket: typing.Dict = None):
        """
        Set bucket for user in chat

        Chat or user is always required. If one of them is not provided,
        you have to set missing value based on the provided one.

        :param chat:
        :param user:
        :param bucket:
        """
        raise NotImplementedError

    async def update_bucket(self, *,
                            chat: typing.Union[str, int, None] = None,
                            user: typing.Union[str, int, None] = None,
                            bucket: typing.Dict = None,
                            **kwargs):
        """
        Update bucket for user in chat

        You can use bucket parameter or|and kwargs.

        Chat or user is always required. If one of them is not provided,
        you have to set missing value based on the provided one.

        :param bucket:
        :param chat:
        :param user:
        :param kwargs:
        :return:
        """
        raise NotImplementedError

    async def reset_bucket(self, *,
                           chat: typing.Union[str, int, None] = None,
                           user: typing.Union[str, int, None] = None):
        """
        Reset bucket dor user in chat.

        Chat or user is always required. If one of them is not provided,
        you have to set missing value based on the provided one.

        :param chat:
        :param user:
        :return:
        """
        await self.set_data(chat=chat, user=user, data={})


class FSMContext:
    def __init__(self, storage, chat, user):
        self.storage: BaseStorage = storage
        self.chat, self.user = self.storage.check_address(chat=chat, user=user)

    def proxy(self):
        return FSMContextProxy(self)

    @staticmethod
    def _resolve_state(value):
        from .filters.state import State

        if value is None:
            return
        elif isinstance(value, str):
            return value
        elif isinstance(value, State):
            return value.state
        return str(value)

    async def get_state(self, default: typing.Optional[str] = None) -> typing.Optional[str]:
        return await self.storage.get_state(chat=self.chat, user=self.user, default=self._resolve_state(default))

    async def get_data(self, default: typing.Optional[str] = None) -> typing.Dict:
        return await self.storage.get_data(chat=self.chat, user=self.user, default=default)

    async def update_data(self, data: typing.Dict = None, **kwargs):
        await self.storage.update_data(chat=self.chat, user=self.user, data=data, **kwargs)

    async def set_state(self, state: typing.Union[typing.AnyStr, None] = None):
        await self.storage.set_state(chat=self.chat, user=self.user, state=self._resolve_state(state))

    async def set_data(self, data: typing.Dict = None):
        await self.storage.set_data(chat=self.chat, user=self.user, data=data)

    async def reset_state(self, with_data: typing.Optional[bool] = True):
        await self.storage.reset_state(chat=self.chat, user=self.user, with_data=with_data)

    async def reset_data(self):
        await self.storage.reset_data(chat=self.chat, user=self.user)

    async def finish(self):
        await self.storage.finish(chat=self.chat, user=self.user)


class FSMContextProxy:
    def __init__(self, fsm_context: FSMContext):
        super(FSMContextProxy, self).__init__()
        self.fsm_context = fsm_context
        self._copy = {}
        self._data = {}
        self._state = None
        self._is_dirty = False

        self._closed = True

    async def __aenter__(self):
        await self.load()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.save()
        self._closed = True

    def _check_closed(self):
        if self._closed:
            raise LookupError('Proxy is closed!')

    @classmethod
    async def create(cls, fsm_context: FSMContext):
        """
        :param fsm_context:
        :return:
        """
        proxy = cls(fsm_context)
        await proxy.load()
        return proxy

    async def load(self):
        self._closed = False

        self.clear()
        self._state = await self.fsm_context.get_state()
        self.update(await self.fsm_context.get_data())
        self._copy = copy.deepcopy(self._data)
        self._is_dirty = False

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._check_closed()

        self._state = value
        self._is_dirty = True

    @state.deleter
    def state(self):
        self._check_closed()

        self._state = None
        self._is_dirty = True

    async def save(self, force=False):
        self._check_closed()

        if self._copy != self._data or force:
            await self.fsm_context.set_data(data=self._data)
        if self._is_dirty or force:
            await self.fsm_context.set_state(self.state)
        self._is_dirty = False
        self._copy = copy.deepcopy(self._data)

    def clear(self):
        del self.state
        return self._data.clear()

    def get(self, value, default=None):
        return self._data.get(value, default)

    def setdefault(self, key, default):
        self._check_closed()

        self._data.setdefault(key, default)

    def update(self, data=None, **kwargs):
        self._check_closed()

        self._data.update(data, **kwargs)

    def pop(self, key, default=None):
        self._check_closed()

        return self._data.pop(key, default)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def as_dict(self):
        return copy.deepcopy(self._data)

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return self._data.__iter__()

    def __getitem__(self, item):
        return self._data[item]

    def __setitem__(self, key, value):
        self._check_closed()

        self._data[key] = value

    def __delitem__(self, key):
        self._check_closed()

        del self._data[key]

    def __contains__(self, item):
        return item in self._data

    def __str__(self):
        readable_state = f"'{self.state}'" if self.state else "<default>"
        result = f"{self.__class__.__name__} state = {readable_state}, data = {self._data}"
        if self._closed:
            result += ', closed = True'
        return result


class DisabledStorage(BaseStorage):
    """
    Empty storage. Use it if you don't want to use Finite-State Machine
    """

    async def close(self):
        pass

    async def wait_closed(self):
        pass

    async def get_state(self, *,
                        chat: typing.Union[str, int, None] = None,
                        user: typing.Union[str, int, None] = None,
                        default: typing.Optional[str] = None) -> typing.Optional[str]:
        return None

    async def get_data(self, *,
                       chat: typing.Union[str, int, None] = None,
                       user: typing.Union[str, int, None] = None,
                       default: typing.Optional[str] = None) -> typing.Dict:
        self._warn()
        return {}

    async def update_data(self, *,
                          chat: typing.Union[str, int, None] = None,
                          user: typing.Union[str, int, None] = None,
                          data: typing.Dict = None, **kwargs):
        self._warn()

    async def set_state(self, *,
                        chat: typing.Union[str, int, None] = None,
                        user: typing.Union[str, int, None] = None,
                        state: typing.Optional[typing.AnyStr] = None):
        self._warn()

    async def set_data(self, *,
                       chat: typing.Union[str, int, None] = None,
                       user: typing.Union[str, int, None] = None,
                       data: typing.Dict = None):
        self._warn()

    @staticmethod
    def _warn():
        warn(f"You haven’t set any storage yet so no states and no data will be saved. \n"
             f"You can connect MemoryStorage for debug purposes or non-essential data.",
             FSMStorageWarning, 5)
