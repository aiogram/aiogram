from abc import ABC, abstractmethod
from typing import Any, Generator, Optional

from aiogram.dispatcher.filters import CommandObject
from aiogram.utils.help.engine import BaseHelpBackend


class BaseHelpRenderer(ABC):
    @abstractmethod
    def render(
        self, backend: BaseHelpBackend, command: CommandObject, **kwargs: Any
    ) -> Generator[Optional[str], None, None]:
        pass


class SimpleRenderer(BaseHelpRenderer):
    def __init__(
        self,
        help_title: str = "Commands list:",
        help_footer: str = "",
        aliases_line: str = "Aliases",
        command_title: str = "Help for command:",
        unknown_command: str = "Command not found",
    ):
        self.help_title = help_title
        self.help_footer = help_footer
        self.aliases_line = aliases_line
        self.command_title = command_title
        self.unknown_command = unknown_command

    def render_help(self, backend: BaseHelpBackend) -> Generator[Optional[str], None, None]:
        yield self.help_title

        for command in backend:
            yield f"{command.prefix[0]}{command.commands[0]} - {command.help}"

        if self.help_footer:
            yield None
            yield self.help_footer

    def render_command_help(
        self, backend: BaseHelpBackend, target: str
    ) -> Generator[Optional[str], None, None]:
        try:
            record = backend[target]
        except KeyError:
            yield f"{self.command_title} {target}"
            yield self.unknown_command
            return

        yield f"{self.command_title} {record.as_command()}"
        if len(record.commands) > 1 or len(record.prefix) > 1:
            yield f"{self.aliases_line}: {record.as_aliases()}"
        yield record.help
        yield None
        yield record.description

    def render(
        self, backend: BaseHelpBackend, command: CommandObject, **kwargs: Any
    ) -> Generator[Optional[str], None, None]:
        if command.args:
            yield from self.render_command_help(backend=backend, target=command.args)
        else:
            yield from self.render_help(backend=backend)
