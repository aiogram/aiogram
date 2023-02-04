from __future__ import annotations

from typing import Optional

from .base import MutableTelegramObject


class ChatPermissions(MutableTelegramObject):
    """
    Describes actions that a non-administrator user is allowed to take in a chat.

    Source: https://core.telegram.org/bots/api#chatpermissions
    """

    can_send_messages: Optional[bool] = None
    """*Optional*. :code:`True`, if the user is allowed to send text messages, contacts, invoices, locations and venues"""
    can_send_audios: Optional[bool] = None
    """*Optional*. :code:`True`, if the user is allowed to send audios"""
    can_send_documents: Optional[bool] = None
    """*Optional*. :code:`True`, if the user is allowed to send documents"""
    can_send_photos: Optional[bool] = None
    """*Optional*. :code:`True`, if the user is allowed to send photos"""
    can_send_videos: Optional[bool] = None
    """*Optional*. :code:`True`, if the user is allowed to send videos"""
    can_send_video_notes: Optional[bool] = None
    """*Optional*. :code:`True`, if the user is allowed to send video notes"""
    can_send_voice_notes: Optional[bool] = None
    """*Optional*. :code:`True`, if the user is allowed to send voice notes"""
    can_send_polls: Optional[bool] = None
    """*Optional*. :code:`True`, if the user is allowed to send polls"""
    can_send_other_messages: Optional[bool] = None
    """*Optional*. :code:`True`, if the user is allowed to send animations, games, stickers and use inline bots"""
    can_add_web_page_previews: Optional[bool] = None
    """*Optional*. :code:`True`, if the user is allowed to add web page previews to their messages"""
    can_change_info: Optional[bool] = None
    """*Optional*. :code:`True`, if the user is allowed to change the chat title, photo and other settings. Ignored in public supergroups"""
    can_invite_users: Optional[bool] = None
    """*Optional*. :code:`True`, if the user is allowed to invite new users to the chat"""
    can_pin_messages: Optional[bool] = None
    """*Optional*. :code:`True`, if the user is allowed to pin messages. Ignored in public supergroups"""
    can_manage_topics: Optional[bool] = None
    """*Optional*. :code:`True`, if the user is allowed to create forum topics. If omitted defaults to the value of can_pin_messages"""
