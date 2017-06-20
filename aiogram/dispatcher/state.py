import logging

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

    def __setitem__(self, key, value):
        """
        Here you can use key or slice-key
        
        >>> storage[chat:user] = "new state"
        or
        >>> storage[chat] = "new state"
        :param key: key or slice
        :param value: new state
        """
        if isinstance(key, slice):
            self.set_state(key.start, key.stop, value)
        else:
            self.set_state(key, key, value)

    def __getitem__(self, key):
        """
        Here you can use key or slice-key
        
        >>> storage[chat:user]
        or
        >>> storage[chat]
        :param key: key or slice
        :return: state
        """
        if isinstance(key, slice):
            return self.get_state(key.start, key.stop)
        return self.get_state(key, key)

    def __delitem__(self, key):
        """
        Reset state for user
        :param key: 
        :return: 
        """
        if isinstance(key, slice):
            self.del_state(key.start, key.stop)
        else:
            self.del_state(key, key)

    def __iter__(self):
        yield from self.all_states()


class StateStorage(BaseStorage):
    """
    Simple in-memory state storage
    Based on builtin dict
    """

    def __init__(self):
        self.storage = {}

    def _prepare(self, chat, user):
        """
        Add chat and user to storage if they are not exist
        :param chat: 
        :param user: 
        :return: 
        """
        result = False

        if chat not in self.storage:
            self.storage[chat] = {}
            result = True

        if user not in self.storage[chat]:
            self.storage[chat][user] = {'state': None, 'data': {}}
            result = True

        return result

    def set_state(self, chat, user, state):
        self._prepare(chat, user)
        self.storage[chat][user]['state'] = self._prepare_state_name(state)

    def get_state(self, chat, user):
        self._prepare(chat, user)
        return self.storage[chat][user]['state']

    def del_state(self, chat, user):
        self._prepare(chat, user)
        if self[chat:user] is not None:
            self.storage[chat][user]['state'] = {'state': None, 'data': {}}

    def all_states(self, chat=None, user=None, state=None):
        for chat_id, chat in self.storage.items():
            if chat is not None and chat != chat_id:
                continue
            for user_id, user_state in chat.items():
                if user is not None and user != user_id:
                    continue
                if state is not None and user_state == state:
                    continue
                yield chat_id, user_id, user_state

    def set_value(self, chat, user, key, value):
        self._prepare(chat, user)
        self.storage[chat][user]['data'][key] = value

    def del_value(self, chat, user, key):
        self._prepare(chat, user)
        del self.storage[chat][user]['data'][key]

    def get_data(self, chat, user):
        self._prepare(chat, user)
        return self.storage[chat][user]['data']

    def update_data(self, chat, user, data):
        self._prepare(chat, user)
        self.storage[chat][user]['data'].update(data)

    def clear_data(self, chat, user, key):
        self._prepare(chat, user)
        self.storage[chat][user]['data'].clear()


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
        self._state_machine[self._chat:self._user] = value

    def get_state(self):
        """
        Get current state

        :return: 
        """
        return self._state_machine[self._chat:self._user]

    def clear(self):
        """
        Reset state

        :return: 
        """
        del self._state_machine[self._chat:self._user]

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


class StateMachine:
    """
    Manage state
    """

    def __init__(self, dispatcher, states, storage=None):
        if storage is None:
            storage = StateStorage()

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
        self.storage[chat:user] = state

    def get_state(self, chat, user):
        """
        Get state from storage
        :param chat: 
        :param user: 
        :return: 
        """
        return self.storage[chat:user]

    def del_state(self, chat, user):
        """
        Clear user state
        :param chat: 
        :param user: 
        :return: 
        """
        log.debug(f"Reset state for {chat}:{user}")
        del self.storage[chat:user]

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

    def __setitem__(self, key, value):
        """
        Here you can use key or slice-key

        >>> state[chat:user] = "new state"
        or
        >>> state[chat] = "new state"
        :param key: key or slice
        :param value: new state
        """
        if isinstance(key, slice):
            self.set_state(key.start, key.stop, value)
        else:
            self.set_state(key, key, value)

    def __getitem__(self, key):
        """
        Here you can use key or slice-key

        >>> state[chat:user]
        or
        >>> state[chat]
        :param key: key or slice
        :return: state
        """
        if isinstance(key, slice):
            return self.get_state(key.start, key.stop)
        return self.get_state(key, key)

    def __delitem__(self, key):
        """
        Reset user state
        :param key: 
        :return: 
        """
        if isinstance(key, slice):
            self.del_state(key.start, key.stop)
        else:
            self.del_state(key, key)
