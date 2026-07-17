from typing import TYPE_CHECKING, Any

from ..types import ChatIdUnion, InlineKeyboardMarkup, InputMediaUnion
from .base import TelegramMethod


class EditEphemeralMessageMedia(TelegramMethod[bool]):
    """
    Use this method to edit the media of an ephemeral message. Note that it is not guaranteed that the user will receive the message edit event, especially if they are offline. On success, :code:`True` is returned.

    Source: https://core.telegram.org/bots/api#editephemeralmessagemedia
    """

    __returning__ = bool
    __api_method__ = "editEphemeralMessageMedia"

    chat_id: ChatIdUnion
    """Unique identifier for the target chat or username of the target supergroup in the format :code:`@username`"""
    receiver_user_id: int
    """Identifier of the user who received the message"""
    ephemeral_message_id: int
    """Identifier of the ephemeral message to edit"""
    media: InputMediaUnion
    """A JSON-serialized object for the new media content of the message. A new file can't be uploaded; use a previously uploaded file via its file_id or specify a URL"""
    reply_markup: InlineKeyboardMarkup | None = None
    """A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            chat_id: ChatIdUnion,
            receiver_user_id: int,
            ephemeral_message_id: int,
            media: InputMediaUnion,
            reply_markup: InlineKeyboardMarkup | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                chat_id=chat_id,
                receiver_user_id=receiver_user_id,
                ephemeral_message_id=ephemeral_message_id,
                media=media,
                reply_markup=reply_markup,
                **__pydantic_kwargs,
            )
