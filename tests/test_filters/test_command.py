import datetime
import logging
import re

import pytest

from aiogram import F
from aiogram.client import bot as bot_module
from aiogram.filters import Command, CommandObject
from aiogram.filters.command import CommandStart
from aiogram.methods import GetChat
from aiogram.types import AcceptedGiftTypes, BotCommand, Chat, ChatFullInfo, Message, User
from tests.mocked_bot import MockedBot


def command_message(text: str) -> Message:
    return Message(
        message_id=0, text=text, chat=Chat(id=-42, type="supergroup"), date=datetime.datetime.now()
    )


def add_bot_chat(bot: MockedBot, active_usernames: list[str]) -> None:
    bot.add_result_for(
        GetChat,
        ok=True,
        result=ChatFullInfo(
            id=bot.id,
            type="private",
            accent_color_id=0,
            max_reaction_count=0,
            accepted_gift_types=AcceptedGiftTypes(
                unlimited_gifts=False,
                limited_gifts=False,
                unique_gifts=False,
                premium_subscription=False,
                gifts_from_channels=False,
            ),
            active_usernames=active_usernames,
        ),
    )


class TestCommandFilter:
    def test_commands_not_iterable(self):
        with pytest.raises(ValueError):
            Command(commands=1)

    def test_bad_type(self):
        with pytest.raises(ValueError):
            Command(1)

    def test_without_args(self):
        with pytest.raises(ValueError):
            Command()

    def test_resolve_bot_command(self):
        command = Command(BotCommand(command="test", description="Test"))
        assert isinstance(command.commands[0], str)
        assert command.commands[0] == "test"

    def test_convert_to_list(self):
        cmd = Command(commands="start")
        assert cmd.commands
        assert isinstance(cmd.commands, tuple)
        assert cmd.commands[0] == "start"
        # assert cmd == Command(commands=["start"])

    @pytest.mark.parametrize(
        "commands,checklist",
        [
            [("Test1", "tEst2", "teSt3"), ("test1", "test2", "test3")],
            [("12TeSt", "3t4Est", "5TE6sT"), ("12test", "3t4est", "5te6st")],
            [[BotCommand(command="Test", description="Test1")], ("test",)],
            [[BotCommand(command="tEsT", description="Test2")], ("test",)],
            [(re.compile(r"test(\d+)"), "TeSt"), (re.compile(r"test(\d+)"), "test")],
        ],
    )
    def test_init_casefold(self, commands, checklist):
        command = Command(*commands, ignore_case=True)
        assert command.commands == checklist

        command = Command(*commands, ignore_case=False)
        assert command.commands != checklist

    @pytest.mark.parametrize(
        "text,command,result",
        [
            ["/test@tbot", Command(commands=["test"], prefix="/"), True],
            ["/test@tbot", Command("test", prefix="/"), True],
            [
                "/test@tbot",
                Command(BotCommand(command="test", description="description"), prefix="/"),
                True,
            ],
            ["!test", Command(commands=["test"], prefix="/"), False],
            ["/tests", Command(commands=["test"], prefix="/"), False],
            ["/", Command(commands=["test"], prefix="/"), False],
            ["/ test", Command(commands=["test"], prefix="/"), False],
            ["", Command(commands=["test"], prefix="/"), False],
            [" ", Command(commands=["test"], prefix="/"), False],
            ["test", Command(commands=["test"], prefix="/"), False],
            [" test", Command(commands=["test"], prefix="/"), False],
            ["a", Command(commands=["test"], prefix="/"), False],
            ["/test@tbot some args", Command(commands=["test"]), True],
            ["/test42@tbot some args", Command(commands=[re.compile(r"test(\d+)")]), True],
            [
                "/test42@tbot some args",
                Command(commands=[re.compile(r"test(\d+)")], magic=F.args == "some args"),
                True,
            ],
            [
                "/test42@tbot some args",
                Command(commands=[re.compile(r"test(\d+)")], magic=F.args == "test"),
                False,
            ],
            ["/start test", CommandStart(), True],
            ["/start", CommandStart(), True],
            ["/start", CommandStart(deep_link=False), True],
            ["/start test", CommandStart(deep_link=False), False],
            ["/start", CommandStart(deep_link=True), False],
            ["/start test", CommandStart(deep_link=True), True],
            ["/start test", CommandStart(deep_link=True, deep_link_encoded=True), False],
            ["/start dGVzdA", CommandStart(deep_link=True, deep_link_encoded=True), True],
            ["/start a", CommandStart(deep_link=True, deep_link_encoded=True), False],
            ["/start abcde", CommandStart(deep_link=True, deep_link_encoded=True), False],
            ["/TeSt", Command("test", ignore_case=True), True],
            ["/TeSt", Command("TeSt", ignore_case=True), True],
            ["/test", Command("TeSt", ignore_case=True), True],
            ["/TeSt", Command("test", ignore_case=False), False],
            ["/test", Command("TeSt", ignore_case=False), False],
            ["/TeSt", Command("TeSt", ignore_case=False), True],
        ],
    )
    async def test_parse_command(self, bot: MockedBot, text: str, result: bool, command: Command):
        # TODO: test ignore mention

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
            [None, False],
        ],
    )
    async def test_call(self, message: Message, result: bool, bot: MockedBot):
        command = Command(commands=["test"])
        assert bool(await command(message=message, bot=bot)) is result

    async def test_command_magic_result(self, bot: MockedBot):
        message = Message(
            message_id=0,
            text="/test 42",
            chat=Chat(id=42, type="private"),
            date=datetime.datetime.now(),
        )
        command = Command(commands=["test"], magic=(F.args.as_("args")))
        result = await command(message=message, bot=bot)
        assert "args" in result
        assert result["args"] == "42"

    async def test_empty_mention_is_none(self, bot: MockedBot):
        # Fixed https://github.com/aiogram/aiogram/issues/1013:
        #   Empty mention should be None instead of empty string.

        message = Message(
            message_id=0,
            text="/test",
            chat=Chat(id=42, type="private"),
            date=datetime.datetime.now(),
        )
        command = Command("test")
        result = await command(message=message, bot=bot)

        assert "command" in result
        command_obj: CommandObject = result["command"]
        assert command_obj.mention is None

    def test_str(self):
        cmd = Command(commands=["start"])
        assert str(cmd) == "Command('start', prefix='/', ignore_case=False, ignore_mention=False)"


class TestCommandMention:
    async def test_no_mention_makes_no_request(self, bot: MockedBot):
        assert await Command("test")(command_message("/test"), bot)
        assert not bot.session.requests

    @pytest.mark.parametrize("text", ["/test@tbot", "/test@TBot"])
    async def test_own_username_makes_no_request(self, bot: MockedBot, text: str):
        assert await Command("test")(command_message(text), bot)
        assert not bot.session.requests

    async def test_secondary_username_is_fetched_once(self, bot: MockedBot):
        add_bot_chat(bot, ["tbot", "tbot_ai"])

        assert await Command("test")(command_message("/test@TBot_AI"), bot)
        assert isinstance(bot.get_request(), GetChat)
        assert not bot.session.requests

        assert await Command("test")(command_message("/test@tbot_ai"), bot)
        assert not bot.session.requests

    @pytest.mark.parametrize("text", ["/test@mention", "/test@other_bot"])
    async def test_foreign_username_is_rejected(self, bot: MockedBot, text: str):
        add_bot_chat(bot, ["tbot", "tbot_ai"])

        assert not await Command("test")(command_message(text), bot)
        assert isinstance(bot.get_request(), GetChat)

    async def test_get_chat_failure_rejects_mention_and_retries_later(
        self, bot: MockedBot, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
    ):
        now = 1000.0
        monkeypatch.setattr(bot_module, "monotonic", lambda: now)
        command = Command("test")
        bot.add_result_for(GetChat, ok=False, error_code=400, description="Bad Request")

        with caplog.at_level(logging.WARNING, logger="aiogram.client.bot"):
            assert not await command(command_message("/test@tbot_ai"), bot)
            assert isinstance(bot.get_request(), GetChat)

            # Within the retry window: no request and no second warning.
            assert not await command(command_message("/test@tbot_ai"), bot)
            assert not bot.session.requests
            # The getMe username still works without getChat.
            assert await command(command_message("/test@tbot"), bot)
        assert len(caplog.records) == 1

        now += bot_module.USERNAMES_RETRY_AFTER
        add_bot_chat(bot, ["tbot", "tbot_ai"])
        assert await command(command_message("/test@tbot_ai"), bot)
        assert isinstance(bot.get_request(), GetChat)


class TestCommandStart:
    def test_str(self):
        cmd = CommandStart()
        assert (
            str(cmd)
            == "CommandStart(ignore_case=False, ignore_mention=False, deep_link_encoded=False)"
        )


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

    def test_update_handler_flags(self):
        cmd = Command(commands=["start"])
        flags = {}
        cmd.update_handler_flags(flags)

        assert "commands" in flags
        assert isinstance(flags["commands"], list)
        assert len(flags["commands"]) == 1
        assert flags["commands"][0] is cmd

        cmd.update_handler_flags(flags)
        assert len(flags["commands"]) == 2
