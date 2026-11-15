from typing import TYPE_CHECKING, Any

from ..client.default import Default
from ..types import ChatIdUnion, Message, MessageEntity, ReplyMarkupUnion, ReplyParameters
from .base import TelegramMethod


class SendWidget(TelegramMethod[Message]):
    """
    Use this method to send a message with an `HTML widget <https://core.telegram.org/bots/widgets>`_. Currently, in the production environment, widgets can be sent only to private chats, and sent widgets automatically have protected content and therefore can't be forwarded. On success, the sent :class:`aiogram.types.message.Message` is returned.

    Source: https://core.telegram.org/bots/api#sendwidget
    """

    __returning__ = Message
    __api_method__ = "sendWidget"

    chat_id: ChatIdUnion
    """Unique identifier for the target chat or username of the target supergroup in the format :code:`@username`"""
    html: str
    """HTML code of the widget, 1-32768 bytes. The code must not exceed 4096 bytes when compressed by zlib with the maximum compression level"""
    message_thread_id: int | None = None
    """Unique identifier for the target message thread (topic) of a forum; for forum supergroups and private chats of bots with forum topic mode enabled only"""
    width: int | None = None
    """Width of the widget in logical pixels; omit if the widget must occupy the whole width of the message bubble. The width is clamped by the app to the range from 200 to the maximum width of the message bubble"""
    height: int | None = None
    """Height of the widget in logical pixels; omit if the height of the widget isn't fixed. The height is clamped by the app to the range 50-600"""
    public_data: str | None = None
    """Public data of the widget, 0-1024 bytes, which will be available wherever the widget is shown. If the widget is shared, then all messages with it will have the same public data"""
    chat_data: str | None = None
    """Data of the widget, which is specific to the message, 0-1024 bytes"""
    caption: str | None = None
    """Widget caption, 0-1024 characters after entities parsing"""
    parse_mode: str | Default | None = Default("parse_mode")
    """Mode for parsing entities in the widget caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details"""
    caption_entities: list[MessageEntity] | None = None
    """A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*"""
    show_caption_above_media: bool | Default | None = Default("show_caption_above_media")
    """Pass :code:`True` if the caption must be shown above the widget"""
    allow_queries: bool | None = None
    """Pass :code:`True` to allow the widget to send queries to the bot"""
    is_shared: bool | None = None
    """Pass :code:`True` to create a shared widget, which can be sent again using the method :class:`aiogram.methods.send_shared_widget.SendSharedWidget`"""
    disable_notification: bool | None = None
    """Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound"""
    protect_content: bool | Default | None = Default("protect_content")
    """Protects the contents of the sent message from forwarding and saving"""
    allow_paid_broadcast: bool | None = None
    """Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance"""
    message_effect_id: str | None = None
    """Unique identifier of the message effect to be added to the message; for private chats only"""
    reply_parameters: ReplyParameters | None = None
    """Description of the message to reply to"""
    reply_markup: ReplyMarkupUnion | None = None
    """Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            chat_id: ChatIdUnion,
            html: str,
            message_thread_id: int | None = None,
            width: int | None = None,
            height: int | None = None,
            public_data: str | None = None,
            chat_data: str | None = None,
            caption: str | None = None,
            parse_mode: str | Default | None = Default("parse_mode"),
            caption_entities: list[MessageEntity] | None = None,
            show_caption_above_media: bool | Default | None = Default("show_caption_above_media"),
            allow_queries: bool | None = None,
            is_shared: bool | None = None,
            disable_notification: bool | None = None,
            protect_content: bool | Default | None = Default("protect_content"),
            allow_paid_broadcast: bool | None = None,
            message_effect_id: str | None = None,
            reply_parameters: ReplyParameters | None = None,
            reply_markup: ReplyMarkupUnion | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                chat_id=chat_id,
                html=html,
                message_thread_id=message_thread_id,
                width=width,
                height=height,
                public_data=public_data,
                chat_data=chat_data,
                caption=caption,
                parse_mode=parse_mode,
                caption_entities=caption_entities,
                show_caption_above_media=show_caption_above_media,
                allow_queries=allow_queries,
                is_shared=is_shared,
                disable_notification=disable_notification,
                protect_content=protect_content,
                allow_paid_broadcast=allow_paid_broadcast,
                message_effect_id=message_effect_id,
                reply_parameters=reply_parameters,
                reply_markup=reply_markup,
                **__pydantic_kwargs,
            )
