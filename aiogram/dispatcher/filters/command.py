from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, AnyStr, Dict, List, Match, Optional, Pattern, Union

from pydantic import root_validator

from aiogram import Bot
from aiogram.api.types import Message
from aiogram.dispatcher.filters import BaseFilter

CommandPatterType = Union[str, re.Pattern]


class Command(BaseFilter):
    commands: List[CommandPatterType]
    commands_prefix: str = "/"
    commands_ignore_case: bool = False
    commands_ignore_mention: bool = False

    @root_validator
    def validate_constraints(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if "commands" not in values:
            raise ValueError("Commands required")
        if not isinstance(values["commands"], list):
            values["commands"] = [values["commands"]]
        return values

    async def __call__(self, message: Message, bot: Bot) -> Union[bool, Dict[str, Any]]:
        if not message.text:
            return False

        return await self.parse_command(text=message.text, bot=bot)

    async def parse_command(self, text: str, bot: Bot) -> Union[bool, Dict[str, CommandObject]]:
        """
        Extract command from the text and validate

        :param text:
        :param bot:
        :return:
        """
        # First step: separate command with arguments
        # "/command@mention arg1 arg2" -> "/command@mention", ["arg1 arg2"]
        full_command, *args = text.split(maxsplit=1)

        # Separate command into valuable parts
        # "/command@mention" -> "/", ("command", "@", "mention")
        prefix, (command, _, mention) = full_command[0], full_command[1:].partition("@")

        # Validate prefixes
        if prefix not in self.commands_prefix:
            return False

        # Validate mention
        if (
            mention
            and not self.commands_ignore_mention
            and mention.lower() != (await bot.me()).username.lower()
        ):
            return False

        # Validate command
        for allowed_command in self.commands:
            # Command can be presented as regexp pattern or raw string
            # then need to validate that in different ways
            if isinstance(allowed_command, Pattern):  # Regexp
                result = allowed_command.match(command)
                if result:
                    return {
                        "command": CommandObject(
                            prefix=prefix,
                            command=command,
                            mention=mention,
                            args=args[0] if args else None,
                            match=result,
                        )
                    }

            elif command == allowed_command:  # String
                return {
                    "command": CommandObject(
                        prefix=prefix,
                        command=command,
                        mention=mention,
                        args=args[0] if args else None,
                        match=None,
                    )
                }

        return False

    class Config:
        arbitrary_types_allowed = True


@dataclass
class CommandObject:
    """
    Instance of this object is always has command and it prefix.
    Can be passed as keyword argument ``command`` to the handler
    """

    prefix: str = "/"
    """Command prefix"""
    command: str = ""
    """Command without prefix and mention"""
    mention: str = None
    """Mention (if available)"""
    args: str = field(repr=False, default=None)
    """Command argument"""
    match: Optional[Match[AnyStr]] = None
    """Will be presented match result if the command is presented as regexp in filter"""

    @property
    def mentioned(self) -> bool:
        """
        This command has mention?
        :return:
        """
        return bool(self.mention)

    @property
    def text(self) -> str:
        """
        Generate original text from object
        :return:
        """
        line = self.prefix + self.command
        if self.mentioned:
            line += "@" + self.mention
        if self.args:
            line += " " + self.args
        return line
