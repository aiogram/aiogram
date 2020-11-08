import pytest

from aiogram.dispatcher.filters.state import (State, StatesGroup, any_state,
                                              default_state)


class MyGroup(StatesGroup):
    state = State()
    state_1 = State()
    state_2 = State()

    class MySubGroup(StatesGroup):
        sub_state = State()
        sub_state_1 = State()
        sub_state_2 = State()

        in_custom_group = State(group_name="custom_group")

        class NewGroup(StatesGroup):
            spam = State()
            renamed_state = State(state="spam_state")


alone_state = State("alone")
alone_in_group = State("alone", group_name="home")


def test_default_state():
    if default_state.state is not None:
        raise AssertionError


def test_any_state():
    if any_state.state != "*":
        raise AssertionError


def test_alone_state():
    if alone_state.state != "@:alone":
        raise AssertionError
    if alone_in_group.state != "home:alone":
        raise AssertionError


def test_group_names():
    if MyGroup.__group_name__ != "MyGroup":
        raise AssertionError
    if MyGroup.__full_group_name__ != "MyGroup":
        raise AssertionError

    if MyGroup.MySubGroup.__group_name__ != "MySubGroup":
        raise AssertionError
    if MyGroup.MySubGroup.__full_group_name__ != "MyGroup.MySubGroup":
        raise AssertionError

    if MyGroup.MySubGroup.NewGroup.__group_name__ != "NewGroup":
        raise AssertionError
    if MyGroup.MySubGroup.NewGroup.__full_group_name__ != "MyGroup.MySubGroup.NewGroup":
        raise AssertionError


def test_custom_group_in_group():
    if MyGroup.MySubGroup.in_custom_group.state != "custom_group:in_custom_group":
        raise AssertionError


def test_custom_state_name_in_group():
    if (
        MyGroup.MySubGroup.NewGroup.renamed_state.state
        != "MyGroup.MySubGroup.NewGroup:spam_state"
    ):
        raise AssertionError


def test_group_states_names():
    if len(MyGroup.states) != 3:
        raise AssertionError
    if len(MyGroup.all_states) != 9:
        raise AssertionError

    if MyGroup.states_names != ("MyGroup:state", "MyGroup:state_1", "MyGroup:state_2"):
        raise AssertionError
    if MyGroup.MySubGroup.states_names != (
        "MyGroup.MySubGroup:sub_state",
        "MyGroup.MySubGroup:sub_state_1",
        "MyGroup.MySubGroup:sub_state_2",
        "custom_group:in_custom_group",
    ):
        raise AssertionError
    if MyGroup.MySubGroup.NewGroup.states_names != (
        "MyGroup.MySubGroup.NewGroup:spam",
        "MyGroup.MySubGroup.NewGroup:spam_state",
    ):
        raise AssertionError

    if MyGroup.all_states_names != (
        "MyGroup:state",
        "MyGroup:state_1",
        "MyGroup:state_2",
        "MyGroup.MySubGroup:sub_state",
        "MyGroup.MySubGroup:sub_state_1",
        "MyGroup.MySubGroup:sub_state_2",
        "custom_group:in_custom_group",
        "MyGroup.MySubGroup.NewGroup:spam",
        "MyGroup.MySubGroup.NewGroup:spam_state",
    ):
        raise AssertionError

    if MyGroup.MySubGroup.all_states_names != (
        "MyGroup.MySubGroup:sub_state",
        "MyGroup.MySubGroup:sub_state_1",
        "MyGroup.MySubGroup:sub_state_2",
        "custom_group:in_custom_group",
        "MyGroup.MySubGroup.NewGroup:spam",
        "MyGroup.MySubGroup.NewGroup:spam_state",
    ):
        raise AssertionError

    if MyGroup.MySubGroup.NewGroup.all_states_names != (
        "MyGroup.MySubGroup.NewGroup:spam",
        "MyGroup.MySubGroup.NewGroup:spam_state",
    ):
        raise AssertionError


def test_root_element():
    root = MyGroup.MySubGroup.NewGroup.spam.get_root()

    if not issubclass(root, StatesGroup):
        raise AssertionError
    if root != MyGroup:
        raise AssertionError

    if root != MyGroup.state.get_root():
        raise AssertionError
    if root != MyGroup.MySubGroup.get_root():
        raise AssertionError

    with pytest.raises(RuntimeError):
        any_state.get_root()
