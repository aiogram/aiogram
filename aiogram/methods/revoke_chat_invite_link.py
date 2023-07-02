from __future__ import annotations

from typing import Union

from ..types import ChatInviteLink
from .base import TelegramMethod


class RevokeChatInviteLink(TelegramMethod[ChatInviteLink]):
    """
    Use this method to revoke an invite link created by the bot. If the primary link is revoked, a new link is automatically generated. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns the revoked invite link as :class:`aiogram.types.chat_invite_link.ChatInviteLink` object.

    Source: https://core.telegram.org/bots/api#revokechatinvitelink
    """

    __returning__ = ChatInviteLink
    __api_method__ = "revokeChatInviteLink"

    chat_id: Union[int, str]
    """Unique identifier of the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    invite_link: str
    """The invite link to revoke"""
