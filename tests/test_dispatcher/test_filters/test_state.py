from copy import copy
from inspect import isclass

import pytest

from aiogram.dispatcher.event.handler import FilterObject
from aiogram.dispatcher.filters import StateFilter
from aiogram.dispatcher.fsm.state import State, StatesGroup
from aiogram.types import Update

pytestmark = pytest.mark.asyncio


class MyGroup(StatesGroup):
    state = State()


class TestStateFilter:
    @pytest.mark.parametrize(
        "state", [None, State("test"), MyGroup, MyGroup(), "state", ["state"]]
    )
    def test_validator(self, state):
        f = StateFilter(state=state)
        assert isinstance(f.state, list)
        value = f.state[0]
        assert (
            isinstance(value, (State, str, MyGroup))
            or (isclass(value) and issubclass(value, StatesGroup))
            or value is None
        )

    @pytest.mark.parametrize(
        "state,current_state,result",
        [
            [State("state"), "@:state", True],
            [[State("state")], "@:state", True],
            [MyGroup, "MyGroup:state", True],
            [[MyGroup], "MyGroup:state", True],
            [MyGroup(), "MyGroup:state", True],
            [[MyGroup()], "MyGroup:state", True],
            ["*", "state", True],
            [None, None, True],
            [[None], None, True],
            [None, "state", False],
            [[], "state", False],
            [[State("state"), "state"], "state", True],
            [[MyGroup(), State("state")], "@:state", True],
            [[MyGroup, State("state")], "state", False],
        ],
    )
    @pytestmark
    async def test_filter(self, state, current_state, result):
        f = StateFilter(state=state)
        assert bool(await f(obj=Update(update_id=42), raw_state=current_state)) is result

    @pytestmark
    async def test_create_filter_from_state(self):
        FilterObject(callback=State(state="state"))

    @pytestmark
    async def test_state_copy(self):
        class SG(StatesGroup):
            state = State()

        assert SG.state == copy(SG.state)

        assert SG.state == "SG:state"
        assert "SG:state" == SG.state

        assert State() == State()
        assert SG.state != 1

        states = {SG.state: "OK"}
        assert states.get(copy(SG.state)) == "OK"
