from __future__ import annotations

from typing import Optional

from ..types import ChatAdministratorRights
from .base import TelegramMethod


class SetMyDefaultAdministratorRights(TelegramMethod[bool]):
    """
    Use this method to change the default administrator rights requested by the bot when it's added as an administrator to groups or channels. These rights will be suggested to users, but they are free to modify the list before adding the bot. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#setmydefaultadministratorrights
    """

    __returning__ = bool
    __api_method__ = "setMyDefaultAdministratorRights"

    rights: Optional[ChatAdministratorRights] = None
    """A JSON-serialized object describing new default administrator rights. If not specified, the default administrator rights will be cleared."""
    for_channels: Optional[bool] = None
    """Pass :code:`True` to change the default administrator rights of the bot in channels. Otherwise, the default administrator rights of the bot for groups and supergroups will be changed."""
