from inspect import isclass
from typing import Any

from aiogram.filters.base import Filter
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import TelegramObject

StateType = str | State | StatesGroup | type[StatesGroup] | None


class StateFilter(Filter):
    """
    State filter

    The states are resolved when the filter is created: state names are taken from the groups as
    they are at that moment, and exact states and :code:`"*"` are checked before custom states
    (a :class:`State` or :class:`StatesGroup` with an overridden :code:`__call__`), whatever the
    argument order.
    """

    __slots__ = ("_any", "_custom", "_exact", "_states")

    def __init__(self, *states: StateType) -> None:
        if not states:
            msg = "At least one state is required"
            raise ValueError(msg)

        self._states = states
        exact: set[str | None] = set()
        custom: list[Any] = []
        self._any = False
        for state in states:
            group = state if isclass(state) else type(state)
            if isinstance(state, str) or state is None:
                value = state
            elif isinstance(state, State) and group.__call__ is State.__call__:
                value = state.state
            elif issubclass(group, StatesGroup) and group.__call__ is StatesGroup.__call__:
                # A group matches its state names literally, "*" included
                exact.update(group.__all_states_names__)
                continue
            else:
                custom.append(state)
                continue
            if value == "*":
                self._any = True
            else:
                exact.add(value)
        self._exact = frozenset(exact)
        self._custom = tuple(custom)

    @property
    def states(self) -> tuple[StateType, ...]:
        """The states the filter was created with (read-only)."""
        return self._states

    @property
    def exact_states(self) -> frozenset[str | None] | None:
        """
        The exact :code:`raw_state` values this filter accepts, or :code:`None` when it also
        accepts something that is not an exact value (:code:`"*"`, a custom state, an unknown
        object).
        """
        if self._any or self._custom:
            return None
        return self._exact

    def __str__(self) -> str:
        return self._signature_to_string(
            *self._states,
        )

    async def __call__(
        self,
        obj: TelegramObject,
        raw_state: str | None = None,
    ) -> bool | dict[str, Any]:
        if self._any or raw_state in self._exact:
            return True
        for allowed_state in self._custom:
            if isinstance(allowed_state, (State, StatesGroup)):
                if allowed_state(event=obj, raw_state=raw_state):
                    return True
            elif (
                isclass(allowed_state)
                and issubclass(allowed_state, StatesGroup)
                and allowed_state()(event=obj, raw_state=raw_state)
            ):
                return True
        return False
