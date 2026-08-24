from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram.client.default import Default
from aiogram.methods import TelegramMethod
from aiogram.types import TelegramObject

if TYPE_CHECKING:
    from aiogram.client.bot import Bot


def resolve_defaults(value: Any, bot: Bot) -> Any:
    """
    Replace every :class:`~aiogram.client.default.Default` sentinel with the bot's value.

    The framework performs this substitution during serialization
    (:meth:`aiogram.client.session.base.BaseSession.prepare_value`), which a fake session
    never reaches. Doing it here — but keeping the typed objects instead of flattening
    them to JSON — is what lets the world and the call log see the same values Telegram
    would have received.
    """
    if isinstance(value, Default):
        return resolve_defaults(bot.default[value.name], bot)
    if isinstance(value, list):
        return [resolve_defaults(item, bot) for item in value]
    if isinstance(value, tuple):
        return tuple(resolve_defaults(item, bot) for item in value)
    if isinstance(value, dict):
        return {key: resolve_defaults(item, bot) for key, item in value.items()}
    if isinstance(value, (TelegramObject, TelegramMethod)):
        changes: dict[str, Any] = {}
        for name in type(value).model_fields:
            current = getattr(value, name, None)
            resolved = resolve_defaults(current, bot)
            if resolved is not current:
                changes[name] = resolved
        if changes:
            return value.model_copy(update=changes)
    return value
