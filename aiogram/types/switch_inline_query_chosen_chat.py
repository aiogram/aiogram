from typing import TYPE_CHECKING, Any, Optional

from .base import TelegramObject


class SwitchInlineQueryChosenChat(TelegramObject):
    """
    This object represents an inline button that switches the current user to inline mode in a chosen chat, with an optional default inline query.

    Source: https://core.telegram.org/bots/api#switchinlinequerychosenchat
    """

    query: Optional[str] = None
    """*Optional*. The default inline query to be inserted in the input field. If left empty, only the bot's username will be inserted"""
    allow_user_chats: Optional[bool] = None
    """*Optional*. True, if private chats with users can be chosen"""
    allow_bot_chats: Optional[bool] = None
    """*Optional*. True, if private chats with bots can be chosen"""
    allow_group_chats: Optional[bool] = None
    """*Optional*. True, if group and supergroup chats can be chosen"""
    allow_channel_chats: Optional[bool] = None
    """*Optional*. True, if channel chats can be chosen"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            query: Optional[str] = None,
            allow_user_chats: Optional[bool] = None,
            allow_bot_chats: Optional[bool] = None,
            allow_group_chats: Optional[bool] = None,
            allow_channel_chats: Optional[bool] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                query=query,
                allow_user_chats=allow_user_chats,
                allow_bot_chats=allow_bot_chats,
                allow_group_chats=allow_group_chats,
                allow_channel_chats=allow_channel_chats,
                **__pydantic_kwargs,
            )
