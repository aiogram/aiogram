from typing import Set

import pytest

from aiogram.dispatcher.filters.builtin import (
    Text,
    extract_chat_ids,
    ChatIDArgumentType,
)


class TestText:

    @pytest.mark.parametrize('param, key', [
        ('text', 'equals'),
        ('text_contains', 'contains'),
        ('text_startswith', 'startswith'),
        ('text_endswith', 'endswith'),
    ])
    def test_validate(self, param, key):
        value = 'spam and eggs'
        config = {param: value}
        res = Text.validate(config)
        assert res == {key: value}


@pytest.mark.parametrize(
    ('chat_id', 'expected'),
    (
        pytest.param('-64856280', {-64856280,}, id='single negative int as string'),
        pytest.param('64856280', {64856280,}, id='single positive int as string'),
        pytest.param(-64856280, {-64856280,}, id='single negative int'),
        pytest.param(64856280, {64856280,}, id='single positive negative int'),
        pytest.param(
            ['-64856280'], {-64856280,}, id='list of single negative int as string'
        ),
        pytest.param([-64856280], {-64856280,}, id='list of single negative int'),
        pytest.param(
            ['-64856280', '-64856280'],
            {-64856280,},
            id='list of two duplicated negative ints as strings',
        ),
        pytest.param(
            ['-64856280', -64856280],
            {-64856280,},
            id='list of one negative int as string and one negative int',
        ),
        pytest.param(
            [-64856280, -64856280],
            {-64856280,},
            id='list of two duplicated negative ints',
        ),
        pytest.param(
            iter(['-64856280']),
            {-64856280,},
            id='iterator from a list of single negative int as string',
        ),
        pytest.param(
            [10000000, 20000000, 30000000],
            {10000000, 20000000, 30000000},
            id='list of several positive ints',
        ),
        pytest.param(
            [10000000, '20000000', -30000000],
            {10000000, 20000000, -30000000},
            id='list of positive int, positive int as string, negative int',
        ),
    ),
)
def test_extract_chat_ids(chat_id: ChatIDArgumentType, expected: Set[int]):
    assert extract_chat_ids(chat_id) == expected
