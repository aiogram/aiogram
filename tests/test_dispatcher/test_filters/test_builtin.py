from typing import Set, Union, Iterable
from datetime import datetime

import pytest

from aiogram.dispatcher.filters.builtin import (
    Text,
    extract_chat_ids,
    ChatIDArgumentType, ForwardedMessageFilter, IDFilter, Command,
)
from aiogram.types import Message, BotCommand
from tests.types.dataset import MESSAGE, MESSAGE_FROM_CHANNEL


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


class TestForwardedMessageFilter:

    @pytest.mark.asyncio
    async def test_filter_forwarded_messages(self):
        filter = ForwardedMessageFilter(is_forwarded=True)
        
        forwarded_message = Message(forward_date=round(datetime(2020, 5, 21, 5, 1).timestamp()), **MESSAGE)
        
        not_forwarded_message = Message(**MESSAGE)
        
        assert await filter.check(forwarded_message)
        assert not await filter.check(not_forwarded_message)

    @pytest.mark.asyncio
    async def test_filter_not_forwarded_messages(self):
        filter = ForwardedMessageFilter(is_forwarded=False)

        forwarded_message = Message(forward_date=round(datetime(2020, 5, 21, 5, 1).timestamp()), **MESSAGE)

        not_forwarded_message = Message(**MESSAGE)

        assert await filter.check(not_forwarded_message)
        assert not await filter.check(forwarded_message)


class TestIDFilter:

    @pytest.mark.asyncio
    async def test_chat_id_for_channels(self):
        message_from_channel = Message(**MESSAGE_FROM_CHANNEL)

        filter = IDFilter(chat_id=message_from_channel.chat.id)

        assert await filter.check(message_from_channel)


@pytest.mark.parametrize("command", [
    "/start",
    "/start some args",
])
@pytest.mark.parametrize("cmd_filter", [
    "start",
    ("start",),
    BotCommand(command="start", description="my desc"),
    (BotCommand(command="start", description="bar"),),
    (BotCommand(command="start", description="foo"), "help"),
])
@pytest.mark.asyncio
async def test_commands_filter(command: str, cmd_filter: Union[Iterable[Union[str, BotCommand]], str, BotCommand]):
    message_with_command = Message(**MESSAGE)
    message_with_command.text = command

    start_filter = Command(commands=cmd_filter)

    assert await start_filter.check(message_with_command)


@pytest.mark.asyncio
async def test_commands_filter_not_checked():
    message_with_command = Message(**MESSAGE)
    message_with_command.text = "/start"

    start_filter = Command(commands=["help", BotCommand("about", "my desc")])

    assert not await start_filter.check(message_with_command)


def test_commands_filter_raises_error():
    with pytest.raises(ValueError):
        start_filter = Command(commands=42)  # noqa
    with pytest.raises(ValueError):
        start_filter = Command(commands=[42])  # noqa

