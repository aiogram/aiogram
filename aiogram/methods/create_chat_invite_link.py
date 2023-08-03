from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, Optional, Union

from ..types import ChatInviteLink
from .base import TelegramMethod


class CreateChatInviteLink(TelegramMethod[ChatInviteLink]):
    """
    Use this method to create an additional invite link for a chat. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. The link can be revoked using the method :class:`aiogram.methods.revoke_chat_invite_link.RevokeChatInviteLink`. Returns the new invite link as :class:`aiogram.types.chat_invite_link.ChatInviteLink` object.

    Source: https://core.telegram.org/bots/api#createchatinvitelink
    """

    __returning__ = ChatInviteLink
    __api_method__ = "createChatInviteLink"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    name: Optional[str] = None
    """Invite link name; 0-32 characters"""
    expire_date: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None
    """Point in time (Unix timestamp) when the link will expire"""
    member_limit: Optional[int] = None
    """The maximum number of users that can be members of the chat simultaneously after joining the chat via this invite link; 1-99999"""
    creates_join_request: Optional[bool] = None
    """:code:`True`, if users joining the chat via the link need to be approved by chat administrators. If :code:`True`, *member_limit* can't be specified"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            chat_id: Union[int, str],
            name: Optional[str] = None,
            expire_date: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None,
            member_limit: Optional[int] = None,
            creates_join_request: Optional[bool] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                chat_id=chat_id,
                name=name,
                expire_date=expire_date,
                member_limit=member_limit,
                creates_join_request=creates_join_request,
                **__pydantic_kwargs,
            )
