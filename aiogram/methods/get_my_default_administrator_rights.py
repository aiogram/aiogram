from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from ..types import ChatAdministratorRights
from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class GetMyDefaultAdministratorRights(TelegramMethod[ChatAdministratorRights]):
    """
    Use this method to get the current default administrator rights of the bot. Returns :class:`aiogram.types.chat_administrator_rights.ChatAdministratorRights` on success.

    Source: https://core.telegram.org/bots/api#getmydefaultadministratorrights
    """

    __returning__ = ChatAdministratorRights

    for_channels: Optional[bool] = None
    """Pass :code:`True` to get default administrator rights of the bot in channels. Otherwise, default administrator rights of the bot for groups and supergroups will be returned."""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="getMyDefaultAdministratorRights", data=data)
