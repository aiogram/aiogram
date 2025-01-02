from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from .base import TelegramMethod


class RemoveChatVerification(TelegramMethod[bool]):
    """
    Removes verification from a chat that is currently verified on behalf of the organization represented by the bot. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#removechatverification
    """

    __returning__ = bool
    __api_method__ = "removeChatVerification"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__, *, chat_id: Union[int, str], **__pydantic_kwargs: Any
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(chat_id=chat_id, **__pydantic_kwargs)
