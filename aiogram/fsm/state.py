import inspect
from collections.abc import Iterator
from typing import Any, no_type_check

from aiogram.types import TelegramObject


class State:
    """
    State object
    """

    def __init__(self, state: str | None = None, group_name: str | None = None) -> None:
        self._state = state
        self._group_name = group_name
        self._group: type[StatesGroup] | None = None
        # Full state name, computed on first access; reset when the group or its parents change
        self._full_state: tuple[str | None] | None = None

    @property
    def group(self) -> "type[StatesGroup]":
        if not self._group:
            msg = "This state is not in any group."
            raise RuntimeError(msg)
        return self._group

    @property
    def state(self) -> str | None:
        full_state = self._full_state
        if full_state is None:
            full_state = self._full_state = (self._resolve_state(),)
        return full_state[0]

    def _resolve_state(self) -> str | None:
        if self._state is None or self._state == "*":
            return self._state

        if self._group_name is None and self._group:
            group = self._group.__full_group_name__
        elif self._group_name:
            group = self._group_name
        else:
            group = "@"

        return f"{group}:{self._state}"

    def set_parent(self, group: "type[StatesGroup]") -> None:
        if not issubclass(group, StatesGroup):
            msg = "Group must be subclass of StatesGroup"
            raise ValueError(msg)
        self._group = group
        self._full_state = None

    def __set_name__(self, owner: "type[StatesGroup]", name: str) -> None:
        if self._state is None:
            self._state = name
        self.set_parent(owner)

    def __str__(self) -> str:
        return f"<State '{self.state or ''}'>"

    __repr__ = __str__

    def __call__(self, event: TelegramObject, raw_state: str | None = None) -> bool:
        if self.state == "*":
            return True
        return raw_state == self.state

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.state == other.state
        if isinstance(other, str):
            return self.state == other
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.state)


class StatesGroupMeta(type):
    __parent__: type["StatesGroup"] | None
    __childs__: tuple[type["StatesGroup"], ...]
    __states__: tuple[State, ...]
    __state_names__: tuple[str, ...]
    __all_childs__: tuple[type["StatesGroup"], ...]
    __all_states__: tuple[State, ...]
    __all_states_names__: tuple[str, ...]

    @no_type_check
    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace)
        # Set before the children are prepared, so their full names never see an inherited parent
        cls.__parent__ = None

        states = []
        childs = []

        for arg in namespace.values():
            if isinstance(arg, State):
                states.append(arg)
            elif inspect.isclass(arg) and issubclass(arg, StatesGroup):
                child = cls._prepare_child(arg)
                childs.append(child)

        cls.__childs__ = tuple(childs)
        cls.__states__ = tuple(states)
        cls.__state_names__ = tuple(state.state for state in states)

        cls.__all_childs__ = cls._get_all_childs()
        cls.__all_states__ = cls._get_all_states()

        # In order to ensure performance, we calculate this parameter
        # in advance already during the production of the class.
        # Depending on the relationship, it should be recalculated
        cls.__all_states_names__ = cls._get_all_states_names()

        return cls

    @property
    def __full_group_name__(cls) -> str:
        if cls.__parent__:
            return f"{cls.__parent__.__full_group_name__}.{cls.__name__}"
        return cls.__name__

    def __setattr__(cls, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        # A new parent changes the full name of every state below this group. During class
        # creation (no own __all_states__ yet) nothing is cached for this class.
        if name == "__parent__" and "__all_states__" in vars(cls):
            for state in cls.__all_states__:
                state._full_state = None
            groups: tuple[StatesGroupMeta, ...] = (cls, *cls.__all_childs__)
            for group in groups:
                group.__all_states_names__ = group._get_all_states_names()

    def _prepare_child(cls, child: type["StatesGroup"]) -> type["StatesGroup"]:
        """Prepare child.

        The child class is created before its parent, so its state names were computed without
        the parent's name; assigning ``__parent__`` refreshes them (see ``__setattr__``).
        """
        child.__parent__ = cls  # type: ignore[assignment]
        return child

    def _get_all_childs(cls) -> tuple[type["StatesGroup"], ...]:
        result = cls.__childs__
        for child in cls.__childs__:
            result += child.__all_childs__
        return result

    def _get_all_states(cls) -> tuple[State, ...]:
        result = cls.__states__
        for group in cls.__childs__:
            result += group.__all_states__
        return result

    def _get_all_states_names(cls) -> tuple[str, ...]:
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
    def get_root(cls) -> type["StatesGroup"]:
        if cls.__parent__ is None:
            return cls
        return cls.__parent__.get_root()

    def __call__(self, event: TelegramObject, raw_state: str | None = None) -> bool:
        return raw_state in type(self).__all_states_names__

    def __str__(self) -> str:
        return f"StatesGroup {type(self).__full_group_name__}"


default_state = State()
any_state = State(state="*")
