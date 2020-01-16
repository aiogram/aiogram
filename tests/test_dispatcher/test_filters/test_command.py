import datetime
import re
from typing import Match

import pytest

from aiogram.api.methods import GetMe
from aiogram.api.types import Chat, Message, User
from aiogram.dispatcher.filters import Command, CommandObject
from tests.mocked_bot import MockedBot


class TestCommandFilter:
    def test_convert_to_list(self):
        cmd = Command(commands="start")
        assert cmd.commands
        assert isinstance(cmd.commands, list)
        assert cmd.commands[0] == "start"
        assert cmd == Command(commands=["start"])

    @pytest.mark.asyncio
    async def test_parse_command(self, bot: MockedBot):
        # TODO: parametrize
        # TODO: test ignore case
        # TODO: test ignore mention

        bot.add_result_for(
            GetMe, ok=True, result=User(id=42, is_bot=True, first_name="The bot", username="tbot")
        )
        command = Command(commands=["test", re.compile(r"test(\d+)")], commands_prefix="/")

        assert not await command.parse_command("!test", bot)
        assert not await command.parse_command("/test@mention", bot)
        assert await command.parse_command("/test@tbot", bot)
        assert not await command.parse_command("/tests", bot)

        result = await command.parse_command("/test@tbot some args", bot)
        assert isinstance(result, dict)
        assert "command" in result
        assert isinstance(result["command"], CommandObject)
        assert result["command"].command == "test"
        assert result["command"].mention == "tbot"
        assert result["command"].args == "some args"

        result = await command.parse_command("/test42@tbot some args", bot)
        assert isinstance(result, dict)
        assert "command" in result
        assert isinstance(result["command"], CommandObject)
        assert result["command"].command == "test42"
        assert result["command"].mention == "tbot"
        assert result["command"].args == "some args"
        assert isinstance(result["command"].match, Match)

    @pytest.mark.asyncio
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
