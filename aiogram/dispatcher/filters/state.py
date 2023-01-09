import inspect
from typing import Optional, Callable, List

from ..dispatcher import Dispatcher
from ..storage import FSMContext


class State:
    """
    State object
    """

    def __init__(self, state: Optional[str] = None, group_name: Optional[str] = None, dispatcher = Dispatcher):
        self._state = state
        self._group_name = group_name
        self._group = None
        self._dispatcher = dispatcher
        self._pre_set_handlers: List[Callable] = []
        self._post_set_handlers: List[Callable] = []

    @property
    def group(self):
        if not self._group:
            raise RuntimeError('This state is not in any group.')
        return self._group

    def get_root(self):
        return self.group.get_root()

    @property
    def state(self):
        if self._state is None or self._state == '*':
            return self._state

        if self._group_name is None and self._group:
            group = self._group.__full_group_name__
        elif self._group_name:
            group = self._group_name
        else:
            group = '@'

        return f'{group}:{self._state}'

    def set_parent(self, group):
        if not issubclass(group, StatesGroup):
            raise ValueError('Group must be subclass of StatesGroup')
        self._group = group
        self._dispatcher = group._dispatcher

    def __set_name__(self, owner, name):
        if self._state is None:
            self._state = name
        self.set_parent(owner)

    def __str__(self):
        return f"<State '{self.state or ''}'>"

    __repr__ = __str__

    def pre_set(self, func_to_call):
        self._pre_set_handlers.append(func_to_call)
    
    def post_set(self, func_to_call):
        self._post_set_handlers.append(func_to_call)

    async def set(self, *args, trigger=True, **kwargs):
        context = self._dispatcher.get_current().current_state()
        old_state = await context.get_state()

        if trigger is True:
            for func in self._pre_set_handlers:
                await func(context, old_state, self.state)
        
        await context.set_state(self.state)

        if trigger is True:
            for func in self._post_set_handlers:
                await func(context, old_state, self.state)


class StatesGroupMeta(type):
    def __new__(mcs, name, bases, namespace, dispatcher=Dispatcher, **kwargs):
        cls = super(StatesGroupMeta, mcs).__new__(mcs, name, bases, namespace)

        states = []
        childs = []

        cls._group_name = name
        cls._dispatcher = dispatcher

        for name, prop in namespace.items():
            if isinstance(prop, State):
                states.append(prop)
                prop.set_parent(cls)

            elif inspect.isclass(prop) and issubclass(prop, StatesGroup):
                childs.append(prop)
                prop._parent = cls
                prop._dispatcher = dispatcher

        cls._parent = None
        cls._childs = tuple(childs)
        cls._states = tuple(states)
        cls._state_names = tuple(state.state for state in states)

        return cls

    @property
    def __group_name__(cls) -> str:
        return cls._group_name

    @property
    def __full_group_name__(cls) -> str:
        if cls._parent:
            return '.'.join((cls._parent.__full_group_name__, cls._group_name))
        return cls._group_name

    @property
    def states(cls) -> tuple:
        return cls._states

    @property
    def childs(cls) -> tuple:
        return cls._childs

    @property
    def all_childs(cls):
        result = cls.childs
        for child in cls.childs:
            result += child.childs
        return result

    @property
    def all_states(cls):
        result = cls.states
        for group in cls.childs:
            result += group.all_states
        return result

    @property
    def all_states_names(cls):
        return tuple(state.state for state in cls.all_states)

    @property
    def states_names(cls) -> tuple:
        return tuple(state.state for state in cls.states)

    def get_root(cls):
        if cls._parent is None:
            return cls
        return cls._parent.get_root()

    def __contains__(cls, item):
        if isinstance(item, str):
            return item in cls.all_states_names
        if isinstance(item, State):
            return item in cls.all_states
        if isinstance(item, StatesGroup):
            return item in cls.all_childs
        return False

    def __str__(self):
        return f"<StatesGroup '{self.__full_group_name__}'>"


class StatesGroup(metaclass=StatesGroupMeta):
    @classmethod
    async def next(cls, *args, trigger=True, **kwargs) -> str:
        state = cls._dispatcher.get_current().current_state()
        state_name = await state.get_state()

        try:
            next_step = cls.states_names.index(state_name) + 1
        except ValueError:
            next_step = 0

        try:
            next_state = cls.states[next_step]
            next_state_name = next_state.state
            await next_state.set(trigger=trigger)

        except IndexError:
            next_state_name = None
            await state.set_state(next_state_name)

        return next_state_name


    @classmethod
    async def previous(cls, *args, trigger=True, **kwargs) -> str:
        state = cls._dispatcher.get_current().current_state()
        state_name = await state.get_state()

        try:
            previous_step = cls.states_names.index(state_name) - 1
        except ValueError:
            previous_step = 0

        if previous_step < 0:
            previous_state_name = None
            await state.set_state(previous_state_name)

        else:
            previous_state = cls.states[previous_step]
            previous_state_name = previous_state.state
            await previous_state.set(trigger=trigger)

        return previous_state_name

    @classmethod
    async def first(cls, *args, trigger=True, **kwargs) -> str:
        state = cls._dispatcher.get_current().current_state()
        first_step = cls.states[0]

        await first_step.set(trigger=trigger)
        return first_step.state

    @classmethod
    async def last(cls, *args, trigger=True, **kwargs) -> str:
        state = cls._dispatcher.get_current().current_state()
        last_step = cls.states[-1]

        await last_step.set(trigger=trigger)
        return last_step.state

    @classmethod
    def pre_finish(cls, func_to_call) -> str:
        FSMContext.set_pre_finish_hanlder(cls._group_name, func_to_call)
    
    @classmethod
    def post_finish(cls, func_to_call) -> str:
        FSMContext.set_post_finish_hanlder(cls._group_name, func_to_call)


default_state = State()
any_state = State(state='*')
