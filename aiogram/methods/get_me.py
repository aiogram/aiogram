from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from ..types import User
from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class GetMe(TelegramMethod[User]):
    """
    A simple method for testing your bot's authentication token. Requires no parameters. Returns basic information about the bot in form of a :class:`aiogram.types.user.User` object.

    Source: https://core.telegram.org/bots/api#getme
    """

    __returning__ = User

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="getMe", data=data)
