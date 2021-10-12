from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from typing import Any, Dict, Match, Optional, Pattern, Sequence, Tuple, Union, cast

from magic_filter import MagicFilter
from pydantic import Field, validator

from aiogram import Bot
from aiogram.dispatcher.filters import BaseFilter
from aiogram.types import Message
from aiogram.utils.deep_linking import decode_payload

CommandPatterType = Union[str, re.Pattern]


class CommandException(Exception):
    pass


class Command(BaseFilter):
    """
    This filter can be helpful for handling commands from the text messages.

    Works only with :class:`aiogram.types.message.Message` events which have the :code:`text`.
    """

    commands: Union[Sequence[CommandPatterType], CommandPatterType]
    """List of commands (string or compiled regexp patterns)"""
    commands_prefix: str = "/"
    """Prefix for command. Prefix is always is single char but here you can pass all of allowed prefixes,
    for example: :code:`"/!"` will work with commands prefixed by :code:`"/"` or :code:`"!"`."""
    commands_ignore_case: bool = False
    """Ignore case (Does not work with regexp, use flags instead)"""
    commands_ignore_mention: bool = False
    """Ignore bot mention. By default bot can not handle commands intended for other bots"""
    command_magic: Optional[MagicFilter] = None
    """Validate command object via Magic filter after all checks done"""

    def update_handler_flags(self, flags: Dict[str, Any]) -> None:
        commands = flags.setdefault("commands", [])
        commands.append(self)

    @validator("commands", always=True)
    def _validate_commands(
        cls, value: Union[Sequence[CommandPatterType], CommandPatterType]
    ) -> Sequence[CommandPatterType]:
        if isinstance(value, (str, re.Pattern)):
            value = [value]
        return value

    async def __call__(self, message: Message, bot: Bot) -> Union[bool, Dict[str, Any]]:
        text = message.text or message.caption
        if not text:
            return False

        try:
            command = await self.parse_command(text=text, bot=bot)
        except CommandException:
            return False
        return {"command": command}

    def extract_command(self, text: str) -> CommandObject:
        # First step: separate command with arguments
        # "/command@mention arg1 arg2" -> "/command@mention", ["arg1 arg2"]
        try:
            full_command, *args = text.split(maxsplit=1)
        except ValueError:
            raise CommandException("not enough values to unpack")

        # Separate command into valuable parts
        # "/command@mention" -> "/", ("command", "@", "mention")
        prefix, (command, _, mention) = full_command[0], full_command[1:].partition("@")
        return CommandObject(
            prefix=prefix, command=command, mention=mention, args=args[0] if args else None
        )

    def validate_prefix(self, command: CommandObject) -> None:
        if command.prefix not in self.commands_prefix:
            raise CommandException("Invalid command prefix")

    async def validate_mention(self, bot: Bot, command: CommandObject) -> None:
        if command.mention and not self.commands_ignore_mention:
            me = await bot.me()
            if me.username and command.mention.lower() != me.username.lower():
                raise CommandException("Mention did not match")

    def validate_command(self, command: CommandObject) -> CommandObject:
        for allowed_command in cast(Sequence[CommandPatterType], self.commands):
            # Command can be presented as regexp pattern or raw string
            # then need to validate that in different ways
            if isinstance(allowed_command, Pattern):  # Regexp
                result = allowed_command.match(command.command)
                if result:
                    return replace(command, regexp_match=result)
            elif command.command == allowed_command:  # String
                return command
        raise CommandException("Command did not match pattern")

    async def parse_command(self, text: str, bot: Bot) -> CommandObject:
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
        self.do_magic(command=command)
        return command

    def do_magic(self, command: CommandObject) -> None:
        if not self.command_magic:
            return
        if not self.command_magic.resolve(command):
            raise CommandException("Rejected via magic filter")

    class Config:
        arbitrary_types_allowed = True


@dataclass
class CommandObject:
    """
    Instance of this object is always has command and it prefix.
    Can be passed as keyword argument **command** to the handler
    """

    prefix: str = "/"
    """Command prefix"""
    command: str = ""
    """Command without prefix and mention"""
    mention: Optional[str] = None
    """Mention (if available)"""
    args: Optional[str] = field(repr=False, default=None)
    """Command argument"""
    regexp_match: Optional[Match[str]] = field(repr=False, default=None)
    """Will be presented match result if the command is presented as regexp in filter"""

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


class CommandStart(Command):
    commands: Tuple[str] = Field(("start",), const=True)
    commands_prefix: str = Field("/", const=True)
    deep_link: bool = False
    deep_link_encoded: bool = False

    async def parse_command(self, text: str, bot: Bot) -> CommandObject:
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
        self.do_magic(command=command)
        return command

    def validate_deeplink(self, command: CommandObject) -> CommandObject:
        if not self.deep_link:
            return command
        if not command.args:
            raise CommandException("Deep-link was missing")
        args = command.args
        if self.deep_link_encoded:
            try:
                args = decode_payload(args)
            except UnicodeDecodeError as e:
                raise CommandException(f"Failed to decode Base64: {e}")
            return replace(command, args=args)
        return command
