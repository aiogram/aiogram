import datetime
import re

import pytest

from aiogram import F
from aiogram.filters import Command, CommandObject
from aiogram.filters.command import BotCommandMeta, CommandStart
from aiogram.types import BotCommand, BotCommandScopeDefault, Chat, Message, User
from tests.mocked_bot import MockedBot


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

    @pytest.mark.parametrize("bot_command_cls", [BotCommand, BotCommandMeta])
    def test_resolve_bot_command(self, bot_command_cls: type[BotCommand]):
        bot_command = bot_command_cls(command="test", description="Test")
        command = Command(bot_command)
        assert isinstance(command.commands[0], str)
        assert command.commands[0] == "test"
        assert isinstance(command.bot_commands, tuple)
        assert command.bot_commands[0] is bot_command

    def test_convert_to_list(self):
        cmd = Command(commands="start")
        assert cmd.commands
        assert isinstance(cmd.commands, tuple)
        assert cmd.commands[0] == "start"
        # assert cmd == Command(commands=["start"])

    def test_empty_bot_commands(self):
        command = Command(re.compile(r"test(\d+)"), "test")
        assert len(command.bot_commands) == 0

    def test_bot_command_meta_fields_preserved(self):
        meta = BotCommandMeta(
            command="test", description="Test", scope=BotCommandScopeDefault(), language_code="en"
        )
        command = Command(meta)
        assert isinstance(command.bot_commands[0], BotCommandMeta)
        assert command.bot_commands[0].scope == meta.scope
        assert command.bot_commands[0].language_code == "en"

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
            [
                "/test@tbot",
                Command(
                    BotCommandMeta(
                        command="test",
                        description="description",
                        scope=BotCommandScopeDefault(),
                        language_code="en",
                    ),
                    prefix="/",
                ),
                True,
            ],
            ["!test", Command(commands=["test"], prefix="/"), False],
            ["/test@mention", Command(commands=["test"], prefix="/"), False],
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
