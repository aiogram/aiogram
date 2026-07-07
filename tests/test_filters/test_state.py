from copy import copy
from inspect import isclass

import pytest

from aiogram.dispatcher.event.handler import FilterObject
from aiogram.filters import StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Update


class MyGroup(StatesGroup):
    state = State()


class TestStateFilter:
    @pytest.mark.parametrize("state", [None, State("test"), MyGroup, MyGroup(), "state"])
    def test_validator(self, state):
        f = StateFilter(state)
        assert isinstance(f.states, tuple)
        value = f.states[0]
        assert (
            isinstance(value, (State, str, MyGroup))
            or (isclass(value) and issubclass(value, StatesGroup))
            or value is None
        )

    @pytest.mark.parametrize(
        "state,current_state,result",
        [
            [[State("state")], "@:state", True],
            [[MyGroup], "MyGroup:state", True],
            [[MyGroup()], "MyGroup:state", True],
            [["*"], "state", True],
            [[None], None, True],
            [[State("state"), "state"], "state", True],
            [[MyGroup(), State("state")], "@:state", True],
            [[MyGroup, State("state")], "state", False],
        ],
    )
    async def test_filter(self, state, current_state, result):
        f = StateFilter(*state)
        assert bool(await f(obj=Update(update_id=42), raw_state=current_state)) is result

    def test_empty_filter(self):
        with pytest.raises(ValueError):
            StateFilter()

    async def test_create_filter_from_state(self):
        FilterObject(callback=State(state="state"))

    async def test_state_copy(self):
        class SG(StatesGroup):
            state = State()

        assert SG.state == copy(SG.state)

        assert SG.state == "SG:state"
        assert SG.state == "SG:state"

        assert State() == State()
        assert SG.state != 1

        states = {SG.state: "OK"}
        assert states.get(copy(SG.state)) == "OK"

    def test_str(self):
        f = StateFilter("test")
        assert str(f) == "StateFilter('test')"
