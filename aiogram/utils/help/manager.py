from typing import Any, Optional, Tuple

from aiogram import Bot, Router
from aiogram.dispatcher.filters import Command, CommandObject
from aiogram.types import BotCommand, Message
from aiogram.utils.help.engine import BaseHelpBackend, MappingBackend
from aiogram.utils.help.record import DEFAULT_PREFIXES, CommandRecord
from aiogram.utils.help.render import BaseHelpRenderer, SimpleRenderer


class HelpManager:
    def __init__(
        self,
        backend: Optional[BaseHelpBackend] = None,
        renderer: Optional[BaseHelpRenderer] = None,
    ) -> None:
        if backend is None:
            backend = MappingBackend()
        if renderer is None:
            renderer = SimpleRenderer()
        self._backend = backend
        self._renderer = renderer

    def add(
        self,
        *commands: str,
        help: str,
        description: Optional[str] = None,
        prefix: str = DEFAULT_PREFIXES,
        ignore_case: bool = False,
        ignore_mention: bool = False,
        priority: int = 0,
    ) -> CommandRecord:
        record = CommandRecord(
            commands=commands,
            help=help,
            description=description,
            prefix=prefix,
            ignore_case=ignore_case,
            ignore_mention=ignore_mention,
            priority=priority,
        )
        self._backend.add(record)
        return record

    def command(
        self,
        *commands: str,
        help: str,
        description: Optional[str] = None,
        prefix: str = DEFAULT_PREFIXES,
        ignore_case: bool = False,
        ignore_mention: bool = False,
        priority: int = 0,
    ) -> Command:
        record = self.add(
            *commands,
            help=help,
            description=description,
            prefix=prefix,
            ignore_case=ignore_case,
            ignore_mention=ignore_mention,
            priority=priority,
        )
        return record.as_filter()

    def mount_help(
        self,
        router: Router,
        *commands: str,
        prefix: str = "/",
        help: str = "Help",
        description: str = "Show help for the commands\n"
        "Also you can use '/help command' for get help for specific command",
        as_reply: bool = True,
        filters: Tuple[Any, ...] = (),
        **kw_filters: Any,
    ) -> Any:
        if not commands:
            commands = ("help",)
        help_filter = self.command(*commands, prefix=prefix, help=help, description=description)

        async def handle(message: Message, command: CommandObject, **kwargs: Any) -> Any:
            return await self._handle_help(
                message=message, command=command, as_reply=as_reply, **kwargs
            )

        return router.message.register(handle, help_filter, *filters, **kw_filters)

    async def _handle_help(
        self,
        message: Message,
        bot: Bot,
        command: CommandObject,
        as_reply: bool = True,
        **kwargs: Any,
    ) -> Any:
        lines = self._renderer.render(backend=self._backend, command=command, **kwargs)
        text = "\n".join(line or "" for line in lines)
        return await bot.send_message(
            chat_id=message.chat.id,
            text=text,
            reply_to_message_id=message.message_id if as_reply else None,
        )

    async def set_bot_commands(self, bot: Bot) -> bool:
        return await bot.set_my_commands(
            commands=[
                BotCommand(command=record.commands[0], description=record.help)
                for record in self._backend
                if "/" in record.prefix
            ]
        )
