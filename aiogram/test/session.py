from __future__ import annotations

from collections.abc import AsyncGenerator, Iterable, Mapping
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from aiogram.client.context_controller import BotContextController
from aiogram.client.session.base import BaseSession
from aiogram.methods import TelegramMethod
from aiogram.methods.base import TelegramType

from .errors import NoFileContentError

if TYPE_CHECKING:
    from aiogram.client.bot import Bot

    from .environment import BotTestEnvironment


def _mount_result(value: Any, bot: Bot) -> Any:
    """
    Bind ``value`` and everything nested inside it to ``bot``, and return it.

    A real session deserializes every response with ``context={"bot": bot}``, which
    pydantic threads through the whole object tree — so ``message.delete()``,
    ``message.answer()`` and the shortcuts of nested objects such as
    ``message.reply_to_message`` all work on whatever a Bot API call returned.

    The fake world hands back objects that were *constructed*, not parsed, so that
    context never runs and every shortcut on a result would raise. Re-parsing them to
    reuse pydantic's mechanism is not an option: pydantic skips validation of model
    instances (``revalidate_instances`` is ``"never"``), so binding would require a
    dump/validate round-trip — which mints copies, severing the identity between a
    returned message and the one the world keeps, and quietly reshapes unions and
    sentinel defaults along the way. Walking the tree and calling
    :meth:`~aiogram.client.context_controller.BotContextController.as_` mirrors what
    the context does while leaving the objects themselves untouched.
    """
    _mount(value, bot, seen=set())
    return value


def _mount(value: Any, bot: Bot, seen: set[int]) -> None:
    """Recurse through containers and model fields, binding every bindable object once."""
    # Cheap rejection first: results are most often `bool`, `int` or `str`.
    if isinstance(value, (str, bytes, int, float)) or value is None:
        return

    identity = id(value)
    if identity in seen:
        # The world stores objects by reference, so the same `Chat` shows up on every
        # message of a chat, and a message may transitively refer back to itself.
        return
    seen.add(identity)

    if isinstance(value, BaseModel):
        if isinstance(value, BotContextController):
            value.as_(bot)
        # `__dict__` holds the validated fields; `extra="allow"` parks unknown ones,
        # which may carry objects from a future Bot API version, in `__pydantic_extra__`.
        for field in value.__dict__.values():
            _mount(field, bot, seen)
        for extra in (value.__pydantic_extra__ or {}).values():
            _mount(extra, bot, seen)
        return

    if isinstance(value, Mapping):
        for item in value.values():
            _mount(item, bot, seen)
        return

    if isinstance(value, Iterable):
        # Nested lists are real: `InlineKeyboardMarkup.inline_keyboard` is a list of rows.
        for item in value:
            _mount(item, bot, seen)


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
        # so a result is mounted to the bot exactly like a parsed one would be.
        return _mount_result(result, bot)  # type: ignore[no-any-return]

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
