import json
import logging
import os

from .handler import SkipHandler

log = logging.getLogger('aiogram.StateMachine')


class BaseStorage:
    """
    Skeleton for states storage
    """

    @staticmethod
    def _prepare_state_name(value):
        if callable(value):
            if hasattr(value, '__name__'):
                return value.__name__
            else:
                return value.__class__.__name__
        return value

    def set_state(self, chat, user, state):
        """
        Set state
        
        :param chat: chat_id 
        :param user: user_id
        :param state: value
        """
        raise NotImplementedError

    def get_state(self, chat, user):
        """
        Get user state from 
        
        :param chat: 
        :param user: 
        :return: 
        """
        raise NotImplementedError

    def del_state(self, chat, user):
        """
        Clear user state
        :param chat: cha
        :param user: 
        :return: 
        """
        raise NotImplementedError

    def all_states(self, chat=None, user=None, state=None):
        """
        Yield all states (Can use filters)
        
        :param chat: 
        :param user: 
        :param state: 
        :return: 
        """
        raise NotImplementedError

    def set_value(self, chat, user, key, value):
        """
        Set value for user in storage
        
        :param chat: 
        :param user: 
        :param key: 
        :param value: 
        :return: 
        """
        raise NotImplementedError

    def get_value(self, chat, user, key, default=None):
        """
        Get value from storage
        
        By default, this method calls `self.get_data(chat, user).get(key, default)`
        :param chat: 
        :param user: 
        :param key: 
        :param default: 
        :return: 
        """
        return self.get_data(chat, user).get(key, default)

    def del_value(self, chat, user, key):
        """
        Delete value from storage
        
        :param chat: 
        :param user: 
        :param key: 
        """
        raise NotImplementedError

    def get_data(self, chat, user):
        """
        Get all stored data for user

        :param chat: 
        :param user: 
        :return: dict
        """
        raise NotImplementedError

    def update_data(self, chat, user, data):
        """
        Update data in storage

        :param chat: 
        :param user: 
        :param data: 
        :return: 
        """
        raise NotImplementedError

    def clear_data(self, chat, user, key):
        """
        Clear data in storage

        :param chat: 
        :param user: 
        :param key: 
        :return: 
        """
        raise NotImplementedError


class BaseAsyncStorage(BaseStorage):
    async def set_state(self, chat, user, state):
        """
        Set state

        :param chat: chat_id 
        :param user: user_id
        :param state: value
        """
        raise NotImplementedError

    async def get_state(self, chat, user):
        """
        Get user state from 

        :param chat: 
        :param user: 
        :return: 
        """
        raise NotImplementedError

    async def del_state(self, chat, user):
        """
        Clear user state
        :param chat: cha
        :param user: 
        :return: 
        """
        raise NotImplementedError

    async def all_states(self, chat=None, user=None, state=None):
        """
        Yield all states (Can use filters)

        :param chat: 
        :param user: 
        :param state: 
        :return: 
        """
        raise NotImplementedError

    async def set_value(self, chat, user, key, value):
        """
        Set value for user in storage

        :param chat: 
        :param user: 
        :param key: 
        :param value: 
        :return: 
        """
        raise NotImplementedError

    async def get_value(self, chat, user, key, default=None):
        """
        Get value from storage

        By default, this method calls `(await self.get_data(chat, user)).get(key, default)`
        :param chat: 
        :param user: 
        :param key: 
        :param default: 
        :return: 
        """
        return (await self.get_data(chat, user)).get(key, default)

    async def del_value(self, chat, user, key):
        """
        Delete value from storage

        :param chat: 
        :param user: 
        :param key: 
        """
        raise NotImplementedError

    async def get_data(self, chat, user):
        """
        Get all stored data for user

        :param chat: 
        :param user: 
        :return: dict
        """
        raise NotImplementedError

    async def update_data(self, chat, user, data):
        """
        Update data in storage

        :param chat: 
        :param user: 
        :param data: 
        :return: 
        """
        raise NotImplementedError

    async def clear_data(self, chat, user, key):
        """
        Clear data in storage

        :param chat: 
        :param user: 
        :param key: 
        :return: 
        """
        raise NotImplementedError


class MemoryStorage(BaseStorage):
    """
    Simple in-memory state storage
    Based on builtin dict
    """

    def __init__(self, data=None):
        if data is None:
            data = {}
        self.data = data

    def _prepare(self, chat, user):
        """
        Add chat and user to storage if they are not exist
        :param chat: 
        :param user: 
        :return: 
        """
        result = False

        chat = str(chat)
        user = str(user)

        if chat not in self.data:
            self.data[chat] = {}
            result = True

        if user not in self.data[chat]:
            self.data[chat][user] = {'state': None, 'data': {}}
            result = True

        return result

    def set_state(self, chat, user, state):
        chat = str(chat)
        user = str(user)

        self._prepare(chat, user)
        self.data[chat][user]['state'] = self._prepare_state_name(state)

    def get_state(self, chat, user):
        chat = str(chat)
        user = str(user)

        self._prepare(chat, user)
        return self.data[chat][user]['state']

    def del_state(self, chat, user):
        chat = str(chat)
        user = str(user)

        self._prepare(chat, user)
        self.data[chat][user] = {'state': None, 'data': {}}

    def all_states(self, chat=None, user=None, state=None):
        for chat_id, chat in self.data.items():
            if chat is not None and chat != chat_id:
                continue
            for user_id, user_state in chat.items():
                if user is not None and user != user_id:
                    continue
                if state is not None and user_state == state:
                    continue
                yield chat_id, user_id, user_state

    def set_value(self, chat, user, key, value):
        chat = str(chat)
        user = str(user)

        self._prepare(chat, user)
        self.data[chat][user]['data'][key] = value

    def del_value(self, chat, user, key):
        chat = str(chat)
        user = str(user)

        self._prepare(chat, user)
        del self.data[chat][user]['data'][key]

    def get_data(self, chat, user):
        chat = str(chat)
        user = str(user)

        self._prepare(chat, user)
        return self.data[chat][user]['data']

    def update_data(self, chat, user, data):
        chat = str(chat)
        user = str(user)

        self._prepare(chat, user)
        self.data[chat][user]['data'].update(data)

    def clear_data(self, chat, user, key):
        chat = str(chat)
        user = str(user)

        self._prepare(chat, user)
        self.data[chat][user]['data'].clear()


class FileStorage(MemoryStorage):
    """
    File-like storage for states.
    """

    def __init__(self, filename):
        self.filename = filename
        super(FileStorage, self).__init__(self.load(filename))

    @staticmethod
    def load(filename):
        """
        Load data from file

        :param filename: 
        :return: dict
        """
        if os.path.isfile(filename):
            with open(filename, 'r') as file:
                return json.load(file)
        return {}

    def save(self):
        """
        Write states to file

        :return: 
        """
        with open(self.filename, 'w') as file:
            json.dump(self.data, file, indent=2)

    def set_state(self, chat, user, state):
        super(FileStorage, self).set_state(chat, user, state)
        self.save()

    def del_state(self, chat, user):
        super(FileStorage, self).del_state(chat, user)
        self.save()

    def set_value(self, chat, user, key, value):
        super(FileStorage, self).set_value(chat, user, key, value)
        self.save()

    def del_value(self, chat, user, key):
        super(FileStorage, self).del_value(chat, user, key)
        self.save()

    def update_data(self, chat, user, data):
        super(FileStorage, self).update_data(chat, user, data)
        self.save()

    def clear_data(self, chat, user, key):
        super(FileStorage, self).clear_data(chat, user, key)
        self.save()


class Controller:
    """
    Storage controller
    
    Make easy access from callback's
    """

    def __init__(self, state_machine, chat, user, state):
        self._state_machine = state_machine
        self._chat = chat
        self._user = user
        self._state = state

    def set_state(self, value):
        """
        Set state

        :param value: 
        :return: 
        """
        self._state_machine.set_state(self._chat, self._user, value)

    def get_state(self):
        """
        Get current state

        :return: 
        """
        return self._state_machine.get_state(self._chat, self._user)

    def clear(self):
        """
        Reset state

        :return: 
        """
        self._state_machine.del_state(self._chat, self._user)

    def get(self, key, default=None):
        """
        Get value from storage

        :param key: 
        :param default: 
        :return: 
        """
        return self._state_machine.storage.get_value(self._chat, self._user, key, default)

    def pop(self, key, default=None):
        """
        Pop item from storage

        :param key: 
        :param default: 
        :return: 
        """
        result = self.get(key, default)
        self.delete(key)
        return result

    def set(self, key, value):
        """
        Set new value in user storage

        :param key: 
        :param value: 
        :return: 
        """
        self._state_machine.storage.set_value(self._chat, self._user, key, value)

    def delete(self, key):
        """
        Delete key from user storage

        :param key: 
        :return: 
        """
        self._state_machine.storage.del_value(self._chat, self._user, key)

    def update(self, data):
        """
        Update user storage

        :param data: 
        :return: 
        """
        self._state_machine.storage.update_data(self._chat, self._user, data)

    @property
    def data(self):
        """
        User data
        :return: 
        """
        return self._state_machine.storage.get_value

    def __setitem__(self, key, value):
        self.set(key, value)

    def __getitem__(self, item):
        return self.get(item)

    def __delitem__(self, key):
        self.delete(key)

    def __str__(self):
        return f"{self._chat}:{self._user} - {self._state}"


class AsyncController:
    """
    Storage controller

    Make easy access from callback's
    """

    def __init__(self, state_machine, chat, user, state):
        self._state_machine = state_machine
        self._chat = chat
        self._user = user
        self._state = state

    async def set_state(self, value):
        """
        Set state

        :param value: 
        :return: 
        """
        await self._state_machine.set_state(self._chat, self._user, value)

    async def get_state(self):
        """
        Get current state

        :return: 
        """
        return await self._state_machine.get_state(self._chat, self._user)

    async def clear(self):
        """
        Reset state

        :return: 
        """
        await self._state_machine.del_state(self._chat, self._user)

    async def get(self, key, default=None):
        """
        Get value from storage

        :param key: 
        :param default: 
        :return: 
        """
        return await self._state_machine.storage.get_value(self._chat, self._user, key, default)

    async def pop(self, key, default=None):
        """
        Pop item from storage

        :param key: 
        :param default: 
        :return: 
        """
        result = await self.get(key, default)
        await self.delete(key)
        return result

    async def set(self, key, value):
        """
        Set new value in user storage

        :param key: 
        :param value: 
        :return: 
        """
        await self._state_machine.storage.set_value(self._chat, self._user, key, value)

    async def delete(self, key):
        """
        Delete key from user storage

        :param key: 
        :return: 
        """
        await self._state_machine.storage.del_value(self._chat, self._user, key)

    async def update(self, data):
        """
        Update user storage

        :param data: 
        :return: 
        """
        await self._state_machine.storage.update_data(self._chat, self._user, data)

    @property
    async def data(self):
        """
        User data

        :return: 
        """
        return await self._state_machine.storage.get_data(self._chat, self._user)

    def __setitem__(self, key, value):
        raise RuntimeError("Item assignment not allowed with async storage")

    def __getitem__(self, item):
        raise RuntimeError("Item assignment not allowed with async storage")

    def __delitem__(self, key):
        raise RuntimeError("Item assignment not allowed with async storage")

    def __str__(self):
        return f"{self._chat}:{self._user} - {self._state}"


class StateMachine:
    """
    Manage state
    """

    def __init__(self, dispatcher, states, storage=None):
        if storage is None:
            storage = MemoryStorage()

        self.steps = self._prepare_states(states)
        self.storage = storage

        dispatcher.message_handlers.register(self.process_message, index=0)

    @staticmethod
    def _prepare_states(states):
        if isinstance(states, dict):
            return states
        elif isinstance(states, (list, tuple, set)):
            prepared_states = {}
            for state in states:
                if not callable(state):
                    raise TypeError('State must be an callable')
                state_name = state.__name__
                prepared_states[state_name] = state
            return prepared_states
        raise TypeError('States must be an dict or list!')

    def set_state(self, chat, user, state):
        """
        Save state to storage
        :param chat: 
        :param user: 
        :param state: 
        :return: 
        """
        log.debug(f"Set state for {chat}:{user} to '{state}'")
        self.storage.set_state(chat, user, state)

    def get_state(self, chat, user):
        """
        Get state from storage
        :param chat: 
        :param user: 
        :return: 
        """
        return self.storage.get_state(chat, user)

    def del_state(self, chat, user):
        """
        Clear user state
        :param chat: 
        :param user: 
        :return: 
        """
        log.debug(f"Reset state for {chat}:{user}")
        self.storage.del_state(chat, user)

    async def process_message(self, message):
        """
        Read message and process it
        :param message: 
        :return: 
        """
        chat_id = message.chat.id
        from_user_id = message.from_user.id

        state = self.get_state(chat_id, from_user_id)
        if state is None:
            raise SkipHandler()

        if state not in self.steps:
            log.warning(f"Found unknown state '{state}' for {chat_id}:{from_user_id}. Condition will be reset.")
            self.del_state(chat_id, from_user_id)
            raise SkipHandler()

        log.debug(f"Process state for {chat_id}:{from_user_id} - '{state}'")
        callback = self.steps[state]
        controller = Controller(self, chat_id, from_user_id, state)
        await callback(message, controller)


class AsyncStateMachine:
    """
    Manage state
    """

    def __init__(self, dispatcher, states, storage=None):
        assert isinstance(storage, BaseAsyncStorage)

        self.steps = self._prepare_states(states)
        self.storage = storage

        dispatcher.message_handlers.register(self.process_message, index=0)

    @staticmethod
    def _prepare_states(states):
        if isinstance(states, dict):
            return states
        elif isinstance(states, (list, tuple, set)):
            prepared_states = {}
            for state in states:
                if not callable(state):
                    raise TypeError('State must be an callable')
                state_name = state.__name__
                prepared_states[state_name] = state
            return prepared_states
        raise TypeError('States must be an dict or list!')

    async def set_state(self, chat, user, state):
        """
        Save state to storage
        :param chat: 
        :param user: 
        :param state: 
        :return: 
        """
        log.debug(f"Set state for {chat}:{user} to '{state}'")
        await self.storage.set_state(chat, user, state)

    async def get_state(self, chat, user):
        """
        Get state from storage
        :param chat: 
        :param user: 
        :return: 
        """
        return await self.storage.get_state(chat, user)

    async def del_state(self, chat, user):
        """
        Clear user state
        :param chat: 
        :param user: 
        :return: 
        """
        log.debug(f"Reset state for {chat}:{user}")
        await self.storage.del_state(chat, user)

    async def process_message(self, message):
        """
        Read message and process it
        :param message: 
        :return: 
        """
        chat_id = message.chat.id
        from_user_id = message.from_user.id

        state = await self.get_state(chat_id, from_user_id)
        if state is None:
            raise SkipHandler()

        if state not in self.steps:
            log.warning(f"Found unknown state '{state}' for {chat_id}:{from_user_id}. Condition will be reset.")
            await self.del_state(chat_id, from_user_id)
            raise SkipHandler()

        log.debug(f"Process state for {chat_id}:{from_user_id} - '{state}'")
        callback = self.steps[state]
        controller = AsyncController(self, chat_id, from_user_id, state)
        await callback(message, controller)
