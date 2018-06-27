from ..dispatcher import Dispatcher


class State:
    def __init__(self, state=None):
        self.state = state

    def __set_name__(self, owner, name):
        if self.state is None:
            self.state = owner.__name__ + ':' + name

    def __str__(self):
        return f"<State '{self.state}>'"

    __repr__ = __str__

    async def set(self):
        state = Dispatcher.current().current_state()
        await state.set_state(self.state)


class MetaStatesGroup(type):
    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super(MetaStatesGroup, mcs).__new__(mcs, name, bases, namespace)

        states = []
        for name, prop in ((name, prop) for name, prop in namespace.items() if isinstance(prop, State)):
            states.append(prop)

        cls._states = tuple(states)
        cls._state_names = tuple(state.state for state in states)

        return cls

    @property
    def states(cls) -> tuple:
        return cls._states

    @property
    def state_names(cls) -> tuple:
        return cls._state_names


class StatesGroup(metaclass=MetaStatesGroup):
    @classmethod
    async def next(cls) -> str:
        state = Dispatcher.current().current_state()
        state_name = await state.get_state()

        try:
            next_step = cls.state_names.index(state_name) + 1
        except ValueError:
            next_step = 0

        try:
            next_state_name = cls.states[next_step].state
        except IndexError:
            next_state_name = None

        await state.set_state(next_state_name)
        return next_state_name

    @classmethod
    async def previous(cls) -> str:
        state = Dispatcher.current().current_state()
        state_name = await state.get_state()

        try:
            previous_step = cls.state_names.index(state_name) - 1
        except ValueError:
            previous_step = 0

        if previous_step < 0:
            previous_state_name = None
        else:
            previous_state_name = cls.states[previous_step].state

        await state.set_state(previous_state_name)
        return previous_state_name

    @classmethod
    async def first(cls) -> str:
        state = Dispatcher.current().current_state()
        first_step_name = cls.states[0].state

        await state.set_state(first_step_name)
        return first_step_name

    @classmethod
    async def last(cls) -> str:
        state = Dispatcher.current().current_state()
        last_step_name = cls.states[-1].state

        await state.set_state(last_step_name)
        return last_step_name
