from typing import Any, Dict

from ..types import User
from .base import Request, TelegramMethod


class GetMe(TelegramMethod[User]):
    """
    A simple method for testing your bot's auth token. Requires no parameters. Returns basic
    information about the bot in form of a User object.

    Source: https://core.telegram.org/bots/api#getme
    """

    __returning__ = User

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="getMe", data=data)
