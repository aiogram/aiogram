import inspect
from typing import Any, Iterator, Optional, Tuple, Type, no_type_check

from ...types import TelegramObject


class State:
    """
    State object
    """

    def __init__(self, state: Optional[str] = None, group_name: Optional[str] = None) -> None:
        self._state = state
        self._group_name = group_name
        self._group: Optional[Type[StatesGroup]] = None

    @property
    def group(self) -> "Type[StatesGroup]":
        if not self._group:
            raise RuntimeError("This state is not in any group.")
        return self._group

    @property
    def state(self) -> Optional[str]:
        if self._state is None or self._state == "*":
            return self._state

        if self._group_name is None and self._group:
            group = self._group.__full_group_name__
        elif self._group_name:
            group = self._group_name
        else:
            group = "@"

        return f"{group}:{self._state}"

    def set_parent(self, group: "Type[StatesGroup]") -> None:
        if not issubclass(group, StatesGroup):
            raise ValueError("Group must be subclass of StatesGroup")
        self._group = group

    def __set_name__(self, owner: "Type[StatesGroup]", name: str) -> None:
        if self._state is None:
            self._state = name
        self.set_parent(owner)

    def __str__(self) -> str:
        return f"<State '{self.state or ''}'>"

    __repr__ = __str__

    def __call__(self, event: TelegramObject, raw_state: Optional[str] = None) -> bool:
        if self.state == "*":
            return True
        return raw_state == self.state


class StatesGroupMeta(type):
    __parent__: "Optional[Type[StatesGroup]]"
    __childs__: "Tuple[Type[StatesGroup], ...]"
    __states__: Tuple[State, ...]
    __state_names__: Tuple[str, ...]

    @no_type_check
    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super(StatesGroupMeta, mcs).__new__(mcs, name, bases, namespace)

        states = []
        childs = []

        for name, arg in namespace.items():
            if isinstance(arg, State):
                states.append(arg)
            elif inspect.isclass(arg) and issubclass(arg, StatesGroup):
                childs.append(arg)
                arg.__parent__ = cls

        cls.__parent__ = None
        cls.__childs__ = tuple(childs)
        cls.__states__ = tuple(states)
        cls.__state_names__ = tuple(state.state for state in states)

        return cls

    @property
    def __full_group_name__(cls) -> str:
        if cls.__parent__:
            return ".".join((cls.__parent__.__full_group_name__, cls.__name__))
        return cls.__name__

    @property
    def __all_childs__(cls) -> Tuple[Type["StatesGroup"], ...]:
        result = cls.__childs__
        for child in cls.__childs__:
            result += child.__childs__
        return result

    @property
    def __all_states__(cls) -> Tuple[State, ...]:
        result = cls.__states__
        for group in cls.__childs__:
            result += group.__all_states__
        return result

    @property
    def __all_states_names__(cls) -> Tuple[str, ...]:
        return tuple(state.state for state in cls.__all_states__ if state.state)

    def __contains__(cls, item: Any) -> bool:
        if isinstance(item, str):
            return item in cls.__all_states_names__
        if isinstance(item, State):
            return item in cls.__all_states__
        if isinstance(item, StatesGroupMeta):
            return item in cls.__all_childs__
        return False

    def __str__(self) -> str:
        return f"<StatesGroup '{self.__full_group_name__}'>"

    def __iter__(self) -> Iterator[State]:
        return iter(self.__all_states__)


class StatesGroup(metaclass=StatesGroupMeta):
    @classmethod
    def get_root(cls) -> Type["StatesGroup"]:
        if cls.__parent__ is None:
            return cls
        return cls.__parent__.get_root()

    def __call__(self, event: TelegramObject, raw_state: Optional[str] = None) -> bool:
        return raw_state in type(self).__all_states_names__

    def __str__(self) -> str:
        return f"StatesGroup {type(self).__full_group_name__}"


default_state = State()
any_state = State(state="*")
