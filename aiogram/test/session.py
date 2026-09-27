from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

from aiogram.client.session.base import BaseSession
from aiogram.methods import TelegramMethod
from aiogram.methods.base import TelegramType

from .errors import NoFileContentError
from .mounting import mount

if TYPE_CHECKING:
    from aiogram.client.bot import Bot

    from .environment import BotTestEnvironment


class FakeTelegramSession(BaseSession):
    """
    Session that answers from the test world instead of the network.

    Every Bot API call in aiogram funnels through :meth:`make_request`, so intercepting
    here — rather than patching :class:`~aiogram.client.bot.Bot` — keeps shortcuts,
    middlewares and error handling exactly as they are in production.
    """

    def __init__(self, environment: BotTestEnvironment) -> None:
        super().__init__()
        self.environment = environment
        self.closed = False

    async def close(self) -> None:
        self.closed = True

    async def make_request(
        self,
        bot: Bot,
        method: TelegramMethod[TelegramType],
        timeout: int | None = None,
    ) -> TelegramType:
        self.closed = False
        result: TelegramType = await self.environment.handle_call(bot, method)
        # The single choke point for every answer — modeled, synthesized or overridden —
        # so a freshly minted result is mounted to the bot exactly like a parsed one would
        # be. Objects the world already owns come back already bound, and `mount` leaves
        # them to their owner rather than claiming them for `bot`.
        return mount(result, bot)  # type: ignore[no-any-return]

    async def stream_content(
        self,
        url: str,
        headers: dict[str, Any] | None = None,
        timeout: int = 30,
        chunk_size: int = 65536,
        raise_for_status: bool = True,
    ) -> AsyncGenerator[bytes, None]:
        """
        Serve declared content, or say plainly that there is none.

        Yielding empty bytes instead would be indistinguishable from "the file was empty",
        a state real bots handle — so a download the environment cannot answer would
        silently exercise the wrong branch of every test. See design decision D1.
        """
        # `file_url` appends the path, and `getFile` mints the path as the file id.
        file_id = url.rsplit("/", 1)[-1]
        content = self.environment.world.files.get(file_id)
        if content is None:
            raise NoFileContentError(file_id)
        for start in range(0, len(content), chunk_size):
            yield content[start : start + chunk_size]
