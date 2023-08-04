from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from .base import TelegramMethod


class ApproveChatJoinRequest(TelegramMethod[bool]):
    """
    Use this method to approve a chat join request. The bot must be an administrator in the chat for this to work and must have the *can_invite_users* administrator right. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#approvechatjoinrequest
    """

    __returning__ = bool
    __api_method__ = "approveChatJoinRequest"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    user_id: int
    """Unique identifier of the target user"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__, *, chat_id: Union[int, str], user_id: int, **__pydantic_kwargs: Any
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(chat_id=chat_id, user_id=user_id, **__pydantic_kwargs)
