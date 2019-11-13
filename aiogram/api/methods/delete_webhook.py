from typing import Any, Dict

from .base import Request, TelegramMethod


class DeleteWebhook(TelegramMethod[bool]):
    """
    Use this method to remove webhook integration if you decide to switch back to getUpdates. Returns True on success. Requires no parameters.

    Source: https://core.telegram.org/bots/api#deletewebhook
    """

    __returning__ = bool

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict(exclude_unset=True, exclude={})

        return Request(method="deleteWebhook", data=data)
