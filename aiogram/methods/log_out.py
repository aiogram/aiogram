from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class LogOut(TelegramMethod[bool]):
    """
    Use this method to log out from the cloud Bot API server before launching the bot locally. You **must** log out the bot before running it locally, otherwise there is no guarantee that the bot will receive updates. After a successful call, you can immediately log in on a local server, but will not be able to log in back to the cloud Bot API server for 10 minutes. Returns :code:`True` on success. Requires no parameters.

    Source: https://core.telegram.org/bots/api#logout
    """

    __returning__ = bool

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="logOut", data=data)
