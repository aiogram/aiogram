from inspect import isclass
from typing import Any, Dict, Optional, Sequence, Type, Union, cast, no_type_check

from pydantic import Field, validator

from aiogram.filters import BaseFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import TelegramObject

StateType = Union[str, None, State, StatesGroup, Type[StatesGroup]]


class StateFilter(BaseFilter):
    """
    State filter
    """

    state: Union[StateType, Sequence[StateType]] = Field(...)

    class Config:
        arbitrary_types_allowed = True

    @validator("state")
    @no_type_check  # issubclass breaks things
    def _validate_state(cls, v: Union[StateType, Sequence[StateType]]) -> Sequence[StateType]:
        if (
            isinstance(v, (str, State, StatesGroup))
            or (isclass(v) and issubclass(v, StatesGroup))
            or v is None
        ):
            return [v]
        return v

    async def __call__(
        self, obj: Union[TelegramObject], raw_state: Optional[str] = None
    ) -> Union[bool, Dict[str, Any]]:
        allowed_states = cast(Sequence[StateType], self.state)
        for allowed_state in allowed_states:
            if isinstance(allowed_state, str) or allowed_state is None:
                if allowed_state == "*" or raw_state == allowed_state:
                    return True
            elif isinstance(allowed_state, (State, StatesGroup)):
                if allowed_state(event=obj, raw_state=raw_state):
                    return True
            elif isclass(allowed_state) and issubclass(allowed_state, StatesGroup):
                if allowed_state()(event=obj, raw_state=raw_state):
                    return True
        return False
