from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

from ..types import BotCommand
from .base import Request, TelegramMethod

if TYPE_CHECKING:  # pragma: no cover
    from ..client.bot import Bot


class GetMyCommands(TelegramMethod[List[BotCommand]]):
    """
    Use this method to get the current list of the bot's commands. Requires no parameters. Returns
    Array of BotCommand on success.

    Source: https://core.telegram.org/bots/api#getmycommands
    """

    __returning__ = List[BotCommand]

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="getMyCommands", data=data)
