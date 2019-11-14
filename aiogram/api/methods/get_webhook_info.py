from typing import Any, Dict

from ..types import WebhookInfo
from .base import Request, TelegramMethod


class GetWebhookInfo(TelegramMethod[WebhookInfo]):
    """
    Use this method to get current webhook status. Requires no parameters. On success, returns a WebhookInfo object. If the bot is using getUpdates, will return an object with the url field empty.

    Source: https://core.telegram.org/bots/api#getwebhookinfo
    """

    __returning__ = WebhookInfo

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="getWebhookInfo", data=data)
