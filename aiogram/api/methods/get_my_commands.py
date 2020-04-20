from typing import Any, Dict, List

from ..types import BotCommand
from .base import Request, TelegramMethod


class GetMyCommands(TelegramMethod[List[BotCommand]]):
    """
    Use this method to get the current list of the bot's commands. Requires no parameters. Returns
    Array of BotCommand on success.

    Source: https://core.telegram.org/bots/api#getmycommands
    """

    __returning__ = List[BotCommand]

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="getMyCommands", data=data)
