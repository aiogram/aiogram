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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    async def get_state(self, default: typing.Optional[str] = None) -> typing.Optional[str]:
        return await self.storage.get_state(chat=self.chat, user=self.user, default=default)

    async def get_data(self, default: typing.Optional[str] = None) -> typing.Dict:
        return await self.storage.get_data(chat=self.chat, user=self.user, default=default)

    async def update_data(self, data: typing.Dict = None, **kwargs):
        await self.storage.update_data(chat=self.chat, user=self.user, data=data, **kwargs)

    async def set_state(self, state: typing.Union[typing.AnyStr, None] = None):
        await self.storage.set_state(chat=self.chat, user=self.user, state=state)

    async def set_data(self, data: typing.Dict = None):
        await self.storage.set_data(chat=self.chat, user=self.user, data=data)

    async def reset_state(self, with_data: typing.Optional[bool] = True):
        await self.storage.reset_state(chat=self.chat, user=self.user, with_data=with_data)

    async def reset_data(self):
        await self.storage.reset_data(chat=self.chat, user=self.user)

    async def finish(self):
        await self.storage.finish(chat=self.chat, user=self.user)


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
