from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field, replace
from re import Match, Pattern
from typing import TYPE_CHECKING, Any, Generic, TypeVar, cast

from pydantic import BaseModel

from aiogram.filters.base import Filter
from aiogram.filters.command.data.codecs import PositionalCodec
from aiogram.types import BotCommand, Message
from aiogram.utils.deep_linking import decode_payload

if TYPE_CHECKING:
    from magic_filter import MagicFilter

    from aiogram import Bot
    from aiogram.filters.command.data.codecs import ArgsCodec

CommandPatternType = str | re.Pattern[str] | BotCommand

T = TypeVar("T", bound=BaseModel)


class CommandException(Exception):
    pass


class Command(Filter, Generic[T]):
    """
    This filter can be helpful for handling commands from the text messages.

    Works only with :class:`aiogram.types.message.Message` events which have the :code:`text`.
    """

    __slots__ = (
        "codec",
        "commands",
        "data",
        "ignore_case",
        "ignore_mention",
        "magic",
        "prefix",
    )

    if TYPE_CHECKING:
        data: type[T] | None
        codec: ArgsCodec | None

    def __init__(
        self,
        *values: CommandPatternType,
        commands: Sequence[CommandPatternType] | CommandPatternType | None = None,
        data: type[T] | None = None,
        codec: ArgsCodec | None = None,
        prefix: str = "/",
        ignore_case: bool = False,
        ignore_mention: bool = False,
        magic: MagicFilter | None = None,
    ):
        """
        List of commands (string or compiled regexp patterns)

        :param prefix: Prefix for command.
            Prefix is always a single char but here you can pass all of allowed prefixes,
            for example: :code:`"/!"` will work with commands prefixed
            by :code:`"/"` or :code:`"!"`.
        :param ignore_case: Ignore case (Does not work with regexp, use flags instead)
        :param ignore_mention: Ignore bot mention. By default,
            bot can not handle commands intended for other bots
        :param magic: Validate command object via Magic filter after all checks done
        """
        if codec is not None and data is None:
            raise ValueError("codec= requires data= to be set")

        if commands is None:
            commands = []
        if isinstance(commands, (str, re.Pattern, BotCommand)):
            commands = [commands]

        if not isinstance(commands, Iterable):
            raise ValueError(
                "Command filter only supports str, re.Pattern, BotCommand object or their Iterable"
            )

        items = []
        for command in (*values, *commands):
            if isinstance(command, BotCommand):
                command = command.command
            if not isinstance(command, (str, re.Pattern)):
                raise ValueError(
                    "Command filter only supports str, re.Pattern, BotCommand object"
                    " or their Iterable"
                )
            if ignore_case and isinstance(command, str):
                command = command.casefold()
            items.append(command)

        if not items:
            raise ValueError("At least one command should be specified")

        self.commands = tuple(items)
        self.data = data
        self.codec = (codec or PositionalCodec(sep=" ")) if data else None
        self.prefix = prefix
        self.ignore_case = ignore_case
        self.ignore_mention = ignore_mention
        self.magic = magic

    def __str__(self) -> str:
        return self._signature_to_string(
            *self.commands,
            data=self.data,
            prefix=self.prefix,
            ignore_case=self.ignore_case,
            ignore_mention=self.ignore_mention,
            magic=self.magic,
        )

    def update_handler_flags(self, flags: dict[str, Any]) -> None:
        commands = flags.setdefault("commands", [])
        commands.append(self)

    async def __call__(self, message: Message, bot: Bot) -> bool | dict[str, Any]:
        if not isinstance(message, Message):
            return False

        text = message.text or message.caption
        if not text:
            return False

        try:
            command = await self.parse_command(text=text, bot=bot)
        except CommandException:
            return False
        result = {"command": command}
        if command.magic_result and isinstance(command.magic_result, dict):
            result.update(command.magic_result)
        return result

    @classmethod
    def extract_command(cls, text: str) -> CommandObject[T]:
        # First step: separate command with arguments
        # "/command@mention arg1 arg2" -> "/command@mention", ["arg1 arg2"]
        try:
            full_command, *args = text.split(maxsplit=1)
        except ValueError as e:
            raise CommandException("not enough values to unpack") from e

        # Separate command into valuable parts
        # "/command@mention" -> "/", ("command", "@", "mention")
        prefix, (command, _, mention) = full_command[0], full_command[1:].partition("@")
        return CommandObject(
            prefix=prefix,
            command=command,
            mention=mention or None,
            args=args[0] if args else None,
        )

    def validate_prefix(self, command: CommandObject[T]) -> None:
        if command.prefix not in self.prefix:
            raise CommandException("Invalid command prefix")

    async def validate_mention(self, bot: Bot, command: CommandObject[T]) -> None:
        if command.mention and not self.ignore_mention:
            me = await bot.me()
            if me.username and command.mention.lower() != me.username.lower():
                raise CommandException("Mention did not match")

    def validate_command(self, command: CommandObject[T]) -> CommandObject[T]:
        for allowed_command in cast(Sequence[CommandPatternType], self.commands):
            # Command can be presented as regexp pattern or raw string
            # then need to validate that in different ways
            if isinstance(allowed_command, Pattern):  # Regexp
                result = allowed_command.match(command.command)
                if result:
                    return replace(command, regexp_match=result)

            command_name = command.command
            if self.ignore_case:
                command_name = command_name.casefold()

            if command_name == allowed_command:  # String
                return command
        raise CommandException("Command did not match pattern")

    def _has_data(self) -> bool:
        return self.data is not None and self.codec is not None

    def _parse_args(self, args: str) -> Any:
        return self.codec.decode(args, self.data)  # type: ignore[union-attr, arg-type]

    def do_magic(self, command: CommandObject[T]) -> CommandObject[T]:
        if self._has_data():
            try:
                parsed = self._parse_args(command.args or "")
            except Exception as e:
                raise CommandException(f"Failed to parse command args: {e}") from e
            command = replace(command, parsed=parsed)

        if self.magic is None:
            return command
        result = self.magic.resolve(command)
        if not result:
            raise CommandException("Rejected via magic filter")
        return replace(command, magic_result=result)

    async def parse_command(self, text: str, bot: Bot) -> CommandObject[T]:
        """
        Extract command from the text and validate

        :param text:
        :param bot:
        :return:
        """
        command = self.extract_command(text)
        self.validate_prefix(command=command)
        await self.validate_mention(bot=bot, command=command)
        command = self.validate_command(command=command)
        return self.do_magic(command=command)


@dataclass(frozen=True)
class CommandObject(Generic[T]):
    """
    Instance of this object is always has command and its prefix.
    Can be passed as keyword argument **command** to the handler.

    When used with :class:`Command` and a typed ``data=`` model,
    the :attr:`parsed` field will contain the deserialized typed arguments.
    """

    prefix: str = "/"
    """Command prefix"""
    command: str = ""
    """Command without prefix and mention"""
    mention: str | None = None
    """Mention (if available)"""
    args: str | None = None
    """Command argument"""
    regexp_match: Match[str] | None = field(repr=False, default=None)
    """Will be presented match result if the command is presented as regexp in filter"""
    magic_result: Any | None = field(repr=False, default=None)
    """Result returned by the magic filter"""
    parsed: T | None = None
    """Typed parsed arguments when :class:`~aiogram.filters.DeeplinkData` is used"""

    @property
    def mentioned(self) -> bool:
        """
        This command has mention?
        """
        return bool(self.mention)

    @property
    def text(self) -> str:
        """
        Generate original text from object
        """
        line = self.prefix + self.command
        if self.mention:
            line += "@" + self.mention
        if self.args:
            line += " " + self.args
        return line


class CommandStart(Command[Any]):
    __slots__ = (
        "deep_link",
        "deep_link_encoded",
    )

    def __init__(
        self,
        deep_link: bool | None = None,
        deep_link_encoded: bool = False,
        ignore_case: bool = False,
        ignore_mention: bool = False,
        magic: MagicFilter | None = None,
    ):
        super().__init__(
            "start",
            prefix="/",
            ignore_case=ignore_case,
            ignore_mention=ignore_mention,
            magic=magic,
        )
        self.deep_link = deep_link
        self.deep_link_encoded = deep_link_encoded

    def __str__(self) -> str:
        return self._signature_to_string(
            ignore_case=self.ignore_case,
            ignore_mention=self.ignore_mention,
            magic=self.magic,
            deep_link=self.deep_link,
            deep_link_encoded=self.deep_link_encoded,
        )

    def validate_deeplink(self, command: CommandObject[Any]) -> CommandObject[Any]:
        if self.deep_link is None:
            return command
        if self.deep_link is False:
            if command.args:
                raise CommandException("Deep-link was not expected")
            return command
        if not command.args:
            raise CommandException("Deep-link was missing")
        if self.deep_link_encoded:
            try:
                args = decode_payload(command.args)
            except UnicodeDecodeError as e:
                raise CommandException(f"Failed to decode Base64: {e}") from e
            return replace(command, args=args)
        return command

    async def parse_command(self, text: str, bot: Bot) -> CommandObject[Any]:
        """
        Extract command from the text and validate

        :param text:
        :param bot:
        :return:
        """
        command = self.extract_command(text)
        self.validate_prefix(command=command)
        await self.validate_mention(bot=bot, command=command)
        command = self.validate_command(command)
        command = self.validate_deeplink(command=command)
        return self.do_magic(command=command)
