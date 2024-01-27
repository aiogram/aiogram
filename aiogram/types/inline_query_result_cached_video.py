from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Literal, Optional, Union

from ..client.default import Default
from ..enums import InlineQueryResultType
from .inline_query_result import InlineQueryResult

if TYPE_CHECKING:
    from .inline_keyboard_markup import InlineKeyboardMarkup
    from .input_contact_message_content import InputContactMessageContent
    from .input_invoice_message_content import InputInvoiceMessageContent
    from .input_location_message_content import InputLocationMessageContent
    from .input_text_message_content import InputTextMessageContent
    from .input_venue_message_content import InputVenueMessageContent
    from .message_entity import MessageEntity


class InlineQueryResultCachedVideo(InlineQueryResult):
    """
    Represents a link to a video file stored on the Telegram servers. By default, this video file will be sent by the user with an optional caption. Alternatively, you can use *input_message_content* to send a message with the specified content instead of the video.

    Source: https://core.telegram.org/bots/api#inlinequeryresultcachedvideo
    """

    type: Literal[InlineQueryResultType.VIDEO] = InlineQueryResultType.VIDEO
    """Type of the result, must be *video*"""
    id: str
    """Unique identifier for this result, 1-64 bytes"""
    video_file_id: str
    """A valid file identifier for the video file"""
    title: str
    """Title for the result"""
    description: Optional[str] = None
    """*Optional*. Short description of the result"""
    caption: Optional[str] = None
    """*Optional*. Caption of the video to be sent, 0-1024 characters after entities parsing"""
    parse_mode: Optional[Union[str, Default]] = Default("parse_mode")
    """*Optional*. Mode for parsing entities in the video caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details."""
    caption_entities: Optional[List[MessageEntity]] = None
    """*Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """*Optional*. `Inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_ attached to the message"""
    input_message_content: Optional[
        Union[
            InputTextMessageContent,
            InputLocationMessageContent,
            InputVenueMessageContent,
            InputContactMessageContent,
            InputInvoiceMessageContent,
        ]
    ] = None
    """*Optional*. Content of the message to be sent instead of the video"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal[InlineQueryResultType.VIDEO] = InlineQueryResultType.VIDEO,
            id: str,
            video_file_id: str,
            title: str,
            description: Optional[str] = None,
            caption: Optional[str] = None,
            parse_mode: Optional[Union[str, Default]] = Default("parse_mode"),
            caption_entities: Optional[List[MessageEntity]] = None,
            reply_markup: Optional[InlineKeyboardMarkup] = None,
            input_message_content: Optional[
                Union[
                    InputTextMessageContent,
                    InputLocationMessageContent,
                    InputVenueMessageContent,
                    InputContactMessageContent,
                    InputInvoiceMessageContent,
                ]
            ] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                type=type,
                id=id,
                video_file_id=video_file_id,
                title=title,
                description=description,
                caption=caption,
                parse_mode=parse_mode,
                caption_entities=caption_entities,
                reply_markup=reply_markup,
                input_message_content=input_message_content,
                **__pydantic_kwargs,
            )
