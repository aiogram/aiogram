from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Union

from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class DeleteMessage(TelegramMethod[bool]):
    """
    Use this method to delete a message, including service messages, with the following limitations:

    - A message can only be deleted if it was sent less than 48 hours ago.

    - Service messages about a supergroup, channel, or forum topic creation can't be deleted.

    - A dice message in a private chat can only be deleted if it was sent more than 24 hours ago.

    - Bots can delete outgoing messages in private chats, groups, and supergroups.

    - Bots can delete incoming messages in private chats.

    - Bots granted *can_post_messages* permissions can delete outgoing messages in channels.

    - If the bot is an administrator of a group, it can delete any message there.

    - If the bot has *can_delete_messages* permission in a supergroup or a channel, it can delete any message there.

    Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#deletemessage
    """

    __returning__ = bool

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    message_id: int
    """Identifier of the message to delete"""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="deleteMessage", data=data)
