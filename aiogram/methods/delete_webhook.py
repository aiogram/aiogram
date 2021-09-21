from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class DeleteWebhook(TelegramMethod[bool]):
    """
    Use this method to remove webhook integration if you decide to switch back to :class:`aiogram.methods.get_updates.GetUpdates`. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#deletewebhook
    """

    __returning__ = bool

    drop_pending_updates: Optional[bool] = None
    """Pass :code:`True` to drop all pending updates"""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="deleteWebhook", data=data)
