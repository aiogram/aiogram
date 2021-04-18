from dataclasses import dataclass
from itertools import product
from typing import Generator, Optional, Sequence

from aiogram.dispatcher.filters import Command

DEFAULT_PREFIXES = "/"


@dataclass
class CommandRecord:
    commands: Sequence[str]
    help: str
    description: Optional[str] = None
    prefix: str = DEFAULT_PREFIXES
    ignore_case: bool = False
    ignore_mention: bool = False
    priority: int = 0

    def as_filter(self) -> Command:
        return Command(commands=self.commands, commands_prefix=self.prefix)

    def as_keys(self, with_empty_prefix: bool = False) -> Generator[str, None, None]:
        for command in self.commands:
            yield command
            for prefix in self.prefix:
                yield f"{prefix}{command}"

    def as_command(self) -> str:
        return f"{self.prefix[0]}{self.commands[0]}"

    def as_aliases(self) -> str:
        return ", ".join(f"{p}{c}" for c, p in product(self.commands, self.prefix))
