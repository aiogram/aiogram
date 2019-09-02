import pytest

from aiogram.dispatcher.filters.state import State, StatesGroup, any_state, default_state


class MyGroup(StatesGroup):
    state = State()
    state_1 = State()
    state_2 = State()

    class MySubGroup(StatesGroup):
        sub_state = State()
        sub_state_1 = State()
        sub_state_2 = State()

        in_custom_group = State(group_name='custom_group')

        class NewGroup(StatesGroup):
            spam = State()
            renamed_state = State(state='spam_state')


alone_state = State('alone')
alone_in_group = State('alone', group_name='home')


def test_default_state():
    assert default_state.state is None


def test_any_state():
    assert any_state.state == '*'


def test_alone_state():
    assert alone_state.state == '@:alone'
    assert alone_in_group.state == 'home:alone'


def test_group_names():
    assert MyGroup.__group_name__ == 'MyGroup'
    assert MyGroup.__full_group_name__ == 'MyGroup'

    assert MyGroup.MySubGroup.__group_name__ == 'MySubGroup'
    assert MyGroup.MySubGroup.__full_group_name__ == 'MyGroup.MySubGroup'

    assert MyGroup.MySubGroup.NewGroup.__group_name__ == 'NewGroup'
    assert MyGroup.MySubGroup.NewGroup.__full_group_name__ == 'MyGroup.MySubGroup.NewGroup'


def test_custom_group_in_group():
    assert MyGroup.MySubGroup.in_custom_group.state == 'custom_group:in_custom_group'


def test_custom_state_name_in_group():
    assert MyGroup.MySubGroup.NewGroup.renamed_state.state == 'MyGroup.MySubGroup.NewGroup:spam_state'


def test_group_states_names():
    assert len(MyGroup.states) == 3
    assert len(MyGroup.all_states) == 9

    assert MyGroup.states_names == ('MyGroup:state', 'MyGroup:state_1', 'MyGroup:state_2')
    assert MyGroup.MySubGroup.states_names == (
        'MyGroup.MySubGroup:sub_state', 'MyGroup.MySubGroup:sub_state_1', 'MyGroup.MySubGroup:sub_state_2',
        'custom_group:in_custom_group')
    assert MyGroup.MySubGroup.NewGroup.states_names == (
        'MyGroup.MySubGroup.NewGroup:spam', 'MyGroup.MySubGroup.NewGroup:spam_state')

    assert MyGroup.all_states_names == (
        'MyGroup:state', 'MyGroup:state_1', 'MyGroup:state_2',
        'MyGroup.MySubGroup:sub_state',
        'MyGroup.MySubGroup:sub_state_1',
        'MyGroup.MySubGroup:sub_state_2',
        'custom_group:in_custom_group',
        'MyGroup.MySubGroup.NewGroup:spam',
        'MyGroup.MySubGroup.NewGroup:spam_state')

    assert MyGroup.MySubGroup.all_states_names == (
        'MyGroup.MySubGroup:sub_state',
        'MyGroup.MySubGroup:sub_state_1',
        'MyGroup.MySubGroup:sub_state_2',
        'custom_group:in_custom_group',
        'MyGroup.MySubGroup.NewGroup:spam',
        'MyGroup.MySubGroup.NewGroup:spam_state')

    assert MyGroup.MySubGroup.NewGroup.all_states_names == (
        'MyGroup.MySubGroup.NewGroup:spam',
        'MyGroup.MySubGroup.NewGroup:spam_state')


def test_root_element():
    root = MyGroup.MySubGroup.NewGroup.spam.get_root()

    assert issubclass(root, StatesGroup)
    assert root == MyGroup

    assert root == MyGroup.state.get_root()
    assert root == MyGroup.MySubGroup.get_root()

    with pytest.raises(RuntimeError):
        any_state.get_root()
