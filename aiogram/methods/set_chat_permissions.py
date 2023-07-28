from __future__ import annotations

from typing import Optional, Union

from ..types import ChatPermissions
from .base import TelegramMethod


class SetChatPermissions(TelegramMethod[bool]):
    """
    Use this method to set default chat permissions for all members. The bot must be an administrator in the group or a supergroup for this to work and must have the *can_restrict_members* administrator rights. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#setchatpermissions
    """

    __returning__ = bool
    __api_method__ = "setChatPermissions"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)"""
    permissions: ChatPermissions
    """A JSON-serialized object for new default chat permissions"""
    use_independent_chat_permissions: Optional[bool] = None
    """Pass :code:`True` if chat permissions are set independently. Otherwise, the *can_send_other_messages* and *can_add_web_page_previews* permissions will imply the *can_send_messages*, *can_send_audios*, *can_send_documents*, *can_send_photos*, *can_send_videos*, *can_send_video_notes*, and *can_send_voice_notes* permissions; the *can_send_polls* permission will imply the *can_send_messages* permission."""
