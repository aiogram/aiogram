from typing import TYPE_CHECKING, Any

from ..types import InputRichMessage
from .base import TelegramMethod


class SendRichMessageDraft(TelegramMethod[bool]):
    """
    Use this method to stream a partial rich message to a user while the message is being generated. Note that the streamed draft is ephemeral and acts as a temporary 30-second preview - once the output is finalized, you **must** call :class:`aiogram.methods.send_rich_message.SendRichMessage` with the complete message to persist it in the user's chat. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#sendrichmessagedraft
    """

    __returning__ = bool
    __api_method__ = "sendRichMessageDraft"

    chat_id: int
    """Unique identifier for the target private chat"""
    draft_id: int
    """Unique identifier of the message draft; must be non-zero. Changes to drafts with the same identifier are animated. Otherwise, the draft is replaced without animation"""
    rich_message: InputRichMessage
    """The partial message to be streamed. Direct upload of new files and explicit upload of files by a URL isn't supported"""
    message_thread_id: int | None = None
    """Unique identifier for the target message thread"""
    can_stop: bool | None = None
    """Pass :code:`True` to show the user a button to stop further drafts. The bot will receive an :class:`aiogram.types.update.Update` 'stopped_message_generation' if the user presses the button"""
    keep_on_stop: bool | None = None
    """Pass :code:`True` to keep the draft in the chat when the button is pressed. The draft will still disappear after a short time or if the bot sends a message. To fully preserve the partial draft, the bot should send it as a new message"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            chat_id: int,
            draft_id: int,
            rich_message: InputRichMessage,
            message_thread_id: int | None = None,
            can_stop: bool | None = None,
            keep_on_stop: bool | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                chat_id=chat_id,
                draft_id=draft_id,
                rich_message=rich_message,
                message_thread_id=message_thread_id,
                can_stop=can_stop,
                keep_on_stop=keep_on_stop,
                **__pydantic_kwargs,
            )
