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

    def test_states_is_read_only(self):
        f = StateFilter("test")
        assert f.states == ("test",)
        with pytest.raises(AttributeError):
            f.states = ("other",)


class CustomState(State):
    def __call__(self, event, raw_state=None):
        return raw_state == "custom"


class CustomGroup(StatesGroup):
    state = State()

    def __call__(self, event, raw_state=None):
        return raw_state == "custom-group"


class StarGroup(StatesGroup):
    star = State("*")


def legacy_check(states, raw_state):
    """The 3.x StateFilter loop, kept as the parity oracle."""
    for allowed_state in states:
        if isinstance(allowed_state, str) or allowed_state is None:
            if allowed_state in {"*", raw_state}:
                return True
        elif isinstance(allowed_state, (State, StatesGroup)):
            if allowed_state(event=None, raw_state=raw_state):
                return True
        elif (
            isclass(allowed_state)
            and issubclass(allowed_state, StatesGroup)
            and allowed_state()(event=None, raw_state=raw_state)
        ):
            return True
    return False


PARITY_STATES = [
    [None],
    ["state"],
    ["*"],
    [State("state")],
    [State("*")],
    [MyGroup],
    [MyGroup()],
    [MyGroup.state, "other"],
    [CustomState("x")],
    [CustomGroup],
    [CustomGroup()],
    [StarGroup],
    [object()],
    [State],
    [CustomState("x"), MyGroup, None],
]
PARITY_RAW = [None, "state", "@:state", "MyGroup:state", "custom", "custom-group", "*", "x"]


class TestStateFilterPrecomputed:
    @pytest.mark.parametrize("states", PARITY_STATES)
    @pytest.mark.parametrize("raw_state", PARITY_RAW)
    async def test_parity(self, states, raw_state):
        f = StateFilter(*states)
        assert await f(obj=None, raw_state=raw_state) is legacy_check(states, raw_state)

    @pytest.mark.parametrize(
        "states,expected",
        [
            [[None], frozenset({None})],
            [["a", None], frozenset({"a", None})],
            [[State("a")], frozenset({"@:a"})],
            [[MyGroup], frozenset({"MyGroup:state"})],
            [[MyGroup()], frozenset({"MyGroup:state"})],
            [[MyGroup.state, "b"], frozenset({"MyGroup:state", "b"})],
            [[StarGroup], frozenset({"*"})],
            [["*"], None],
            [[State("*")], None],
            [["a", "*"], None],
            [[CustomState("x")], None],
            [[CustomGroup], None],
            [[CustomGroup()], None],
            [[object()], None],
        ],
    )
    def test_exact_states(self, states, expected):
        assert StateFilter(*states).exact_states == expected
