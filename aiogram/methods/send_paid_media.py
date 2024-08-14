from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional, Union

from ..types import (
    ForceReply,
    InlineKeyboardMarkup,
    InputPaidMediaPhoto,
    InputPaidMediaVideo,
    Message,
    MessageEntity,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    ReplyParameters,
)
from .base import TelegramMethod


class SendPaidMedia(TelegramMethod[Message]):
    """
    Use this method to send paid media. On success, the sent :class:`aiogram.types.message.Message` is returned.

    Source: https://core.telegram.org/bots/api#sendpaidmedia
    """

    __returning__ = Message
    __api_method__ = "sendPaidMedia"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`). If the chat is a channel, all Telegram Star proceeds from this media will be credited to the chat's balance. Otherwise, they will be credited to the bot's balance."""
    star_count: int
    """The number of Telegram Stars that must be paid to buy access to the media"""
    media: List[Union[InputPaidMediaPhoto, InputPaidMediaVideo]]
    """A JSON-serialized array describing the media to be sent; up to 10 items"""
    business_connection_id: Optional[str] = None
    """Unique identifier of the business connection on behalf of which the message will be sent"""
    caption: Optional[str] = None
    """Media caption, 0-1024 characters after entities parsing"""
    parse_mode: Optional[str] = None
    """Mode for parsing entities in the media caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details."""
    caption_entities: Optional[List[MessageEntity]] = None
    """A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*"""
    show_caption_above_media: Optional[bool] = None
    """Pass :code:`True`, if the caption must be shown above the message media"""
    disable_notification: Optional[bool] = None
    """Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound."""
    protect_content: Optional[bool] = None
    """Protects the contents of the sent message from forwarding and saving"""
    reply_parameters: Optional[ReplyParameters] = None
    """Description of the message to reply to"""
    reply_markup: Optional[
        Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
    ] = None
    """Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            chat_id: Union[int, str],
            star_count: int,
            media: List[Union[InputPaidMediaPhoto, InputPaidMediaVideo]],
            business_connection_id: Optional[str] = None,
            caption: Optional[str] = None,
            parse_mode: Optional[str] = None,
            caption_entities: Optional[List[MessageEntity]] = None,
            show_caption_above_media: Optional[bool] = None,
            disable_notification: Optional[bool] = None,
            protect_content: Optional[bool] = None,
            reply_parameters: Optional[ReplyParameters] = None,
            reply_markup: Optional[
                Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
            ] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                chat_id=chat_id,
                star_count=star_count,
                media=media,
                business_connection_id=business_connection_id,
                caption=caption,
                parse_mode=parse_mode,
                caption_entities=caption_entities,
                show_caption_above_media=show_caption_above_media,
                disable_notification=disable_notification,
                protect_content=protect_content,
                reply_parameters=reply_parameters,
                reply_markup=reply_markup,
                **__pydantic_kwargs,
            )
