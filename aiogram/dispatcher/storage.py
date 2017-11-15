import typing


class BaseStorage:
    """
    In states-storage you can save current user state and data for all steps
    """

    async def close(self):
        """
        Need override this method and use when application is shutdowns.
        You can save data or etc.

        :return:
        """
        raise NotImplementedError

    async def wait_closed(self):
        """
        You need override this method for all asynchronously storage's like Redis.

        :return:
        """
        raise NotImplementedError

    @classmethod
    def check_address(cls, *,
                      chat: typing.Union[str, int, None] = None,
                      user: typing.Union[str, int, None] = None) -> (typing.Union[str, int], typing.Union[str, int]):
        """
        In all methods of storage chat or user is always required.
        If one of this is not presented, need set the missing value based on the presented.

        This method performs the above action.

        :param chat:
        :param user:
        :return:
        """
        if chat is not None and user is not None:
            return chat, user
        elif user is None and chat is not None:
            user = chat
            return chat, user
        elif user is not None and chat is None:
            chat = user
            return chat, user
        raise ValueError('User or chat parameters is required but anyone is not presented!')

    async def get_state(self, *,
                        chat: typing.Union[str, int, None] = None,
                        user: typing.Union[str, int, None] = None,
                        default: typing.Optional[str] = None) -> typing.Optional[str]:
        """
        Get current state of user in chat. Return value stored in `default` parameter if record is not found.

        Chat or user is always required. If one of this is not presented,
        need set the missing value based on the presented

        :param chat:
        :param user:
        :param default:
        :return:
        """
        raise NotImplementedError

    async def get_data(self, *,
                       chat: typing.Union[str, int, None] = None,
                       user: typing.Union[str, int, None] = None,
                       default: typing.Optional[str] = None) -> typing.Dict:
        """
        Get state-data for user in chat. Return `default` if data is not presented in storage.

        Chat or user is always required. If one of this is not presented,
        need set the missing value based on the presented

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
        Setup new state for user in chat

        Chat or user is always required. If one of this is not presented,
        need set the missing value based on the presented

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

        Chat or user is always required. If one of this is not presented,
        need set the missing value based on the presented

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

        Chat or user is always required. If one of this is not presented,
        need set the missing value based on the presented

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
        Reset data dor user in chat.

        Chat or user is always required. If one of this is not presented,
        need set the missing value based on the presented

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
        Reset state for user in chat. You can use this method for finish conversations.

        Chat or user is always required. If one of this is not presented,
        need set the missing value based on the presented

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

        Chat or user is always required. If one of this is not presented,
        need set the missing value based on the presented

        :param chat:
        :param user:
        :return:
        """
        await self.reset_state(chat=chat, user=user, with_data=True)


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

    async def set_state(self, state: typing.Union[typing.AnyStr, None]):
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
        return {}

    async def update_data(self, *,
                          chat: typing.Union[str, int, None] = None,
                          user: typing.Union[str, int, None] = None,
                          data: typing.Dict = None, **kwargs):
        pass

    async def set_state(self, *,
                        chat: typing.Union[str, int, None] = None,
                        user: typing.Union[str, int, None] = None,
                        state: typing.Optional[typing.AnyStr] = None):
        pass

    async def set_data(self, *,
                       chat: typing.Union[str, int, None] = None,
                       user: typing.Union[str, int, None] = None,
                       data: typing.Dict = None):
        pass
