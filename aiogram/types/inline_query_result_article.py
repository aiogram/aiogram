from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Optional, Union

from pydantic import Field

from ..enums import InlineQueryResultType
from .inline_query_result import InlineQueryResult

if TYPE_CHECKING:
    from .inline_keyboard_markup import InlineKeyboardMarkup
    from .input_contact_message_content import InputContactMessageContent
    from .input_invoice_message_content import InputInvoiceMessageContent
    from .input_location_message_content import InputLocationMessageContent
    from .input_text_message_content import InputTextMessageContent
    from .input_venue_message_content import InputVenueMessageContent


class InlineQueryResultArticle(InlineQueryResult):
    """
    Represents a link to an article or web page.

    Source: https://core.telegram.org/bots/api#inlinequeryresultarticle
    """

    type: Literal[InlineQueryResultType.ARTICLE] = InlineQueryResultType.ARTICLE
    """Type of the result, must be *article*"""
    id: str
    """Unique identifier for this result, 1-64 Bytes"""
    title: str
    """Title of the result"""
    input_message_content: Union[
        InputTextMessageContent,
        InputLocationMessageContent,
        InputVenueMessageContent,
        InputContactMessageContent,
        InputInvoiceMessageContent,
    ]
    """Content of the message to be sent"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """*Optional*. `Inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_ attached to the message"""
    url: Optional[str] = None
    """*Optional*. URL of the result"""
    description: Optional[str] = None
    """*Optional*. Short description of the result"""
    thumbnail_url: Optional[str] = None
    """*Optional*. Url of the thumbnail for the result"""
    thumbnail_width: Optional[int] = None
    """*Optional*. Thumbnail width"""
    thumbnail_height: Optional[int] = None
    """*Optional*. Thumbnail height"""
    hide_url: Optional[bool] = Field(None, json_schema_extra={"deprecated": True})
    """*Optional*. Pass :code:`True` if you don't want the URL to be shown in the message

.. deprecated:: API:8.2
   https://core.telegram.org/bots/api-changelog#january-1-2025"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal[InlineQueryResultType.ARTICLE] = InlineQueryResultType.ARTICLE,
            id: str,
            title: str,
            input_message_content: Union[
                InputTextMessageContent,
                InputLocationMessageContent,
                InputVenueMessageContent,
                InputContactMessageContent,
                InputInvoiceMessageContent,
            ],
            reply_markup: Optional[InlineKeyboardMarkup] = None,
            url: Optional[str] = None,
            description: Optional[str] = None,
            thumbnail_url: Optional[str] = None,
            thumbnail_width: Optional[int] = None,
            thumbnail_height: Optional[int] = None,
            hide_url: Optional[bool] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                type=type,
                id=id,
                title=title,
                input_message_content=input_message_content,
                reply_markup=reply_markup,
                url=url,
                description=description,
                thumbnail_url=thumbnail_url,
                thumbnail_width=thumbnail_width,
                thumbnail_height=thumbnail_height,
                hide_url=hide_url,
                **__pydantic_kwargs,
            )
