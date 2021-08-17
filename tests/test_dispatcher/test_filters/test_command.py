import datetime
import re

import pytest

from aiogram import F
from aiogram.dispatcher.filters import Command, CommandObject
from aiogram.dispatcher.filters.command import CommandStart
from aiogram.methods import GetMe
from aiogram.types import Chat, Message, User
from tests.mocked_bot import MockedBot

pytestmark = pytest.mark.asyncio


class TestCommandFilter:
    def test_convert_to_list(self):
        cmd = Command(commands="start")
        assert cmd.commands
        assert isinstance(cmd.commands, list)
        assert cmd.commands[0] == "start"
        assert cmd == Command(commands=["start"])

    @pytest.mark.parametrize(
        "text,command,result",
        [
            ["/test@tbot", Command(commands=["test"], commands_prefix="/"), True],
            ["!test", Command(commands=["test"], commands_prefix="/"), False],
            ["/test@mention", Command(commands=["test"], commands_prefix="/"), False],
            ["/tests", Command(commands=["test"], commands_prefix="/"), False],
            ["/", Command(commands=["test"], commands_prefix="/"), False],
            ["/ test", Command(commands=["test"], commands_prefix="/"), False],
            ["", Command(commands=["test"], commands_prefix="/"), False],
            [" ", Command(commands=["test"], commands_prefix="/"), False],
            ["test", Command(commands=["test"], commands_prefix="/"), False],
            [" test", Command(commands=["test"], commands_prefix="/"), False],
            ["a", Command(commands=["test"], commands_prefix="/"), False],
            ["/test@tbot some args", Command(commands=["test"]), True],
            ["/test42@tbot some args", Command(commands=[re.compile(r"test(\d+)")]), True],
            [
                "/test42@tbot some args",
                Command(commands=[re.compile(r"test(\d+)")], command_magic=F.args == "some args"),
                True,
            ],
            [
                "/test42@tbot some args",
                Command(commands=[re.compile(r"test(\d+)")], command_magic=F.args == "test"),
                False,
            ],
            ["/start test", CommandStart(), True],
            ["/start", CommandStart(deep_link=True), False],
            ["/start test", CommandStart(deep_link=True), True],
            ["/start test", CommandStart(deep_link=True, deep_link_encoded=True), False],
            ["/start dGVzdA", CommandStart(deep_link=True, deep_link_encoded=True), True],
        ],
    )
    async def test_parse_command(self, bot: MockedBot, text: str, result: bool, command: Command):
        # TODO: test ignore case
        # TODO: test ignore mention

        bot.add_result_for(
            GetMe, ok=True, result=User(id=42, is_bot=True, first_name="The bot", username="tbot")
        )

        message = Message(
            message_id=0, text=text, chat=Chat(id=42, type="private"), date=datetime.datetime.now()
        )

        response = await command(message, bot)
        assert bool(response) is result

    @pytest.mark.parametrize(
        "message,result",
        [
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
                ),
                False,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    text="/test",
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
                ),
                True,
            ],
        ],
    )
    async def test_call(self, message: Message, result: bool, bot: MockedBot):
        command = Command(commands=["test"])
        assert bool(await command(message=message, bot=bot)) is result


class TestCommandObject:
    @pytest.mark.parametrize(
        "obj,result",
        [
            [CommandObject(prefix="/", command="command", mention="mention", args="args"), True],
            [CommandObject(prefix="/", command="command", args="args"), False],
        ],
    )
    def test_mentioned(self, obj: CommandObject, result: bool):
        assert isinstance(obj.mentioned, bool)
        assert obj.mentioned is result

    @pytest.mark.parametrize(
        "obj,result",
        [
            [
                CommandObject(prefix="/", command="command", mention="mention", args="args"),
                "/command@mention args",
            ],
            [
                CommandObject(prefix="/", command="command", mention="mention", args=None),
                "/command@mention",
            ],
            [
                CommandObject(prefix="/", command="command", mention=None, args="args"),
                "/command args",
            ],
            [CommandObject(prefix="/", command="command", mention=None, args=None), "/command"],
            [CommandObject(prefix="!", command="command", mention=None, args=None), "!command"],
        ],
    )
    def test_text(self, obj: CommandObject, result: str):
        assert obj.text == result
