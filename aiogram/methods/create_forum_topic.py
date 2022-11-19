from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from ..types import ForumTopic
from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class CreateForumTopic(TelegramMethod[ForumTopic]):
    """
    Use this method to create a topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the *can_manage_topics* administrator rights. Returns information about the created topic as a :class:`aiogram.types.forum_topic.ForumTopic` object.

    Source: https://core.telegram.org/bots/api#createforumtopic
    """

    __returning__ = ForumTopic

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)"""
    name: str
    """Topic name, 1-128 characters"""
    icon_color: Optional[int] = None
    """Color of the topic icon in RGB format. Currently, must be one of 7322096 (0x6FB9F0), 16766590 (0xFFD67E), 13338331 (0xCB86DB), 9367192 (0x8EEE98), 16749490 (0xFF93B2), or 16478047 (0xFB6F5F)"""
    icon_custom_emoji_id: Optional[str] = None
    """Unique identifier of the custom emoji shown as the topic icon. Use :class:`aiogram.methods.get_forum_topic_icon_stickers.GetForumTopicIconStickers` to get all allowed custom emoji identifiers."""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="createForumTopic", data=data)
