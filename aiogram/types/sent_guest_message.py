from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..client.default import Default
from .base import TelegramObject

if TYPE_CHECKING:
    from ..methods import (
        EditMessageCaption,
        EditMessageMedia,
        EditMessageReplyMarkup,
        EditMessageText,
    )
    from .chat_id_union import ChatIdUnion
    from .inline_keyboard_markup import InlineKeyboardMarkup
    from .input_media_union import InputMediaUnion
    from .input_rich_message import InputRichMessage
    from .link_preview_options import LinkPreviewOptions
    from .message_entity import MessageEntity


class SentGuestMessage(TelegramObject):
    """
    Describes an inline message sent by a guest bot.

    Source: https://core.telegram.org/bots/api#sentguestmessage
    """

    inline_message_id: str
    """Identifier of the sent inline message"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__, *, inline_message_id: str, **__pydantic_kwargs: Any
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(inline_message_id=inline_message_id, **__pydantic_kwargs)

    def edit_text(
        self,
        text: str | None = None,
        business_connection_id: str | None = None,
        chat_id: ChatIdUnion | None = None,
        message_id: int | None = None,
        parse_mode: str | Default | None = Default("parse_mode"),
        entities: list[MessageEntity] | None = None,
        link_preview_options: LinkPreviewOptions | Default | None = Default("link_preview"),
        reply_markup: InlineKeyboardMarkup | None = None,
        rich_message: InputRichMessage | None = None,
        disable_web_page_preview: bool | Default | None = Default("link_preview_is_disabled"),
        **kwargs: Any,
    ) -> EditMessageText:
        """
        Shortcut for method :class:`aiogram.methods.edit_message_text.EditMessageText`
        will automatically fill method attributes:

        - :code:`inline_message_id`

        Use this method to edit text, rich and `game <https://core.telegram.org/bots/api#games>`_ messages. On success, if the edited message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned. Note that business messages that were not sent by the bot and do not contain an inline keyboard can only be edited within **48 hours** from the time they were sent.

        Source: https://core.telegram.org/bots/api#editmessagetext

        :param text: New text of the message, 1-4096 characters after entity parsing; required if *rich_message* isn't specified
        :param business_connection_id: Unique identifier of the business connection on behalf of which the message to be edited was sent
        :param chat_id: Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target bot, supergroup or channel in the format :code:`@username`
        :param message_id: Required if *inline_message_id* is not specified. Identifier of the message to edit
        :param parse_mode: Mode for parsing entities in the message text. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details
        :param entities: A JSON-serialized list of special entities that appear in message text, which can be specified instead of *parse_mode*
        :param link_preview_options: Link preview generation options for the message
        :param reply_markup: A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_
        :param rich_message: New rich content of the message; required if *text* isn't specified. Direct upload of new files and explicit upload of files by a URL isn't supported when an inline message is edited
        :param disable_web_page_preview: Disables link previews for links in this message
        :return: instance of method :class:`aiogram.methods.edit_message_text.EditMessageText`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import EditMessageText

        return EditMessageText(
            inline_message_id=self.inline_message_id,
            text=text,
            business_connection_id=business_connection_id,
            chat_id=chat_id,
            message_id=message_id,
            parse_mode=parse_mode,
            entities=entities,
            link_preview_options=link_preview_options,
            reply_markup=reply_markup,
            rich_message=rich_message,
            disable_web_page_preview=disable_web_page_preview,
            **kwargs,
        ).as_(self._bot)

    def edit_caption(
        self,
        business_connection_id: str | None = None,
        chat_id: ChatIdUnion | None = None,
        message_id: int | None = None,
        caption: str | None = None,
        parse_mode: str | Default | None = Default("parse_mode"),
        caption_entities: list[MessageEntity] | None = None,
        show_caption_above_media: bool | Default | None = Default("show_caption_above_media"),
        reply_markup: InlineKeyboardMarkup | None = None,
        **kwargs: Any,
    ) -> EditMessageCaption:
        """
        Shortcut for method :class:`aiogram.methods.edit_message_caption.EditMessageCaption`
        will automatically fill method attributes:

        - :code:`inline_message_id`

        Use this method to edit captions of messages. On success, if the edited message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned. Note that business messages that were not sent by the bot and do not contain an inline keyboard can only be edited within **48 hours** from the time they were sent.

        Source: https://core.telegram.org/bots/api#editmessagecaption

        :param business_connection_id: Unique identifier of the business connection on behalf of which the message to be edited was sent
        :param chat_id: Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target bot, supergroup or channel in the format :code:`@username`
        :param message_id: Required if *inline_message_id* is not specified. Identifier of the message to edit
        :param caption: New caption of the message, 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the message caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details
        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*
        :param show_caption_above_media: Pass :code:`True` if the caption must be shown above the message media. Supported only for animation, photo and video messages
        :param reply_markup: A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_
        :return: instance of method :class:`aiogram.methods.edit_message_caption.EditMessageCaption`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import EditMessageCaption

        return EditMessageCaption(
            inline_message_id=self.inline_message_id,
            business_connection_id=business_connection_id,
            chat_id=chat_id,
            message_id=message_id,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            show_caption_above_media=show_caption_above_media,
            reply_markup=reply_markup,
            **kwargs,
        ).as_(self._bot)

    def edit_media(
        self,
        media: InputMediaUnion,
        business_connection_id: str | None = None,
        chat_id: ChatIdUnion | None = None,
        message_id: int | None = None,
        reply_markup: InlineKeyboardMarkup | None = None,
        **kwargs: Any,
    ) -> EditMessageMedia:
        """
        Shortcut for method :class:`aiogram.methods.edit_message_media.EditMessageMedia`
        will automatically fill method attributes:

        - :code:`inline_message_id`

        Use this method to edit animation, audio, document, live photo, photo, or video messages, or to replace a text or a rich message with a media. If a message is part of a message album, then it can be edited only to an audio for audio albums, only to a document for document albums and to a photo, a live photo, or a video otherwise. When an inline message is edited, a new file can't be uploaded; use a previously uploaded file via its file_id or specify a URL. On success, if the edited message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned. Note that business messages that were not sent by the bot and do not contain an inline keyboard can only be edited within **48 hours** from the time they were sent.

        Source: https://core.telegram.org/bots/api#editmessagemedia

        :param media: A JSON-serialized object for the new media content of the message
        :param business_connection_id: Unique identifier of the business connection on behalf of which the message to be edited was sent
        :param chat_id: Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target bot, supergroup or channel in the format :code:`@username`
        :param message_id: Required if *inline_message_id* is not specified. Identifier of the message to edit
        :param reply_markup: A JSON-serialized object for a new `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_
        :return: instance of method :class:`aiogram.methods.edit_message_media.EditMessageMedia`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import EditMessageMedia

        return EditMessageMedia(
            inline_message_id=self.inline_message_id,
            media=media,
            business_connection_id=business_connection_id,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=reply_markup,
            **kwargs,
        ).as_(self._bot)

    def edit_reply_markup(
        self,
        business_connection_id: str | None = None,
        chat_id: ChatIdUnion | None = None,
        message_id: int | None = None,
        reply_markup: InlineKeyboardMarkup | None = None,
        **kwargs: Any,
    ) -> EditMessageReplyMarkup:
        """
        Shortcut for method :class:`aiogram.methods.edit_message_reply_markup.EditMessageReplyMarkup`
        will automatically fill method attributes:

        - :code:`inline_message_id`

        Use this method to edit only the reply markup of messages. On success, if the edited message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned. Note that business messages that were not sent by the bot and do not contain an inline keyboard can only be edited within **48 hours** from the time they were sent.

        Source: https://core.telegram.org/bots/api#editmessagereplymarkup

        :param business_connection_id: Unique identifier of the business connection on behalf of which the message to be edited was sent
        :param chat_id: Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target bot, supergroup or channel in the format :code:`@username`
        :param message_id: Required if *inline_message_id* is not specified. Identifier of the message to edit
        :param reply_markup: A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_
        :return: instance of method :class:`aiogram.methods.edit_message_reply_markup.EditMessageReplyMarkup`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import EditMessageReplyMarkup

        return EditMessageReplyMarkup(
            inline_message_id=self.inline_message_id,
            business_connection_id=business_connection_id,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=reply_markup,
            **kwargs,
        ).as_(self._bot)
