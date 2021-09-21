from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from ..types import WebhookInfo
from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class GetWebhookInfo(TelegramMethod[WebhookInfo]):
    """
    Use this method to get current webhook status. Requires no parameters. On success, returns a :class:`aiogram.types.webhook_info.WebhookInfo` object. If the bot is using :class:`aiogram.methods.get_updates.GetUpdates`, will return an object with the *url* field empty.

    Source: https://core.telegram.org/bots/api#getwebhookinfo
    """

    __returning__ = WebhookInfo

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="getWebhookInfo", data=data)
