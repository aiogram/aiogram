from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from ..types.inline_query_result_article import InlineQueryResultArticle
from ..types.inline_query_result_audio import InlineQueryResultAudio
from ..types.inline_query_result_cached_audio import InlineQueryResultCachedAudio
from ..types.inline_query_result_cached_document import InlineQueryResultCachedDocument
from ..types.inline_query_result_cached_gif import InlineQueryResultCachedGif
from ..types.inline_query_result_cached_mpeg4_gif import InlineQueryResultCachedMpeg4Gif
from ..types.inline_query_result_cached_photo import InlineQueryResultCachedPhoto
from ..types.inline_query_result_cached_sticker import InlineQueryResultCachedSticker
from ..types.inline_query_result_cached_video import InlineQueryResultCachedVideo
from ..types.inline_query_result_cached_voice import InlineQueryResultCachedVoice
from ..types.inline_query_result_contact import InlineQueryResultContact
from ..types.inline_query_result_document import InlineQueryResultDocument
from ..types.inline_query_result_game import InlineQueryResultGame
from ..types.inline_query_result_gif import InlineQueryResultGif
from ..types.inline_query_result_location import InlineQueryResultLocation
from ..types.inline_query_result_mpeg4_gif import InlineQueryResultMpeg4Gif
from ..types.inline_query_result_photo import InlineQueryResultPhoto
from ..types.inline_query_result_venue import InlineQueryResultVenue
from ..types.inline_query_result_video import InlineQueryResultVideo
from ..types.inline_query_result_voice import InlineQueryResultVoice
from ..types.prepared_inline_message import PreparedInlineMessage
from .base import TelegramMethod


class SavePreparedInlineMessage(TelegramMethod[PreparedInlineMessage]):
    """
    Stores a message that can be sent by a user of a Mini App. Returns a :class:`aiogram.types.prepared_inline_message.PreparedInlineMessage` object.

    Source: https://core.telegram.org/bots/api#savepreparedinlinemessage
    """

    __returning__ = PreparedInlineMessage
    __api_method__ = "savePreparedInlineMessage"

    user_id: int
    """Unique identifier of the target user that can use the prepared message"""
    result: Union[
        InlineQueryResultCachedAudio,
        InlineQueryResultCachedDocument,
        InlineQueryResultCachedGif,
        InlineQueryResultCachedMpeg4Gif,
        InlineQueryResultCachedPhoto,
        InlineQueryResultCachedSticker,
        InlineQueryResultCachedVideo,
        InlineQueryResultCachedVoice,
        InlineQueryResultArticle,
        InlineQueryResultAudio,
        InlineQueryResultContact,
        InlineQueryResultGame,
        InlineQueryResultDocument,
        InlineQueryResultGif,
        InlineQueryResultLocation,
        InlineQueryResultMpeg4Gif,
        InlineQueryResultPhoto,
        InlineQueryResultVenue,
        InlineQueryResultVideo,
        InlineQueryResultVoice,
    ]
    """A JSON-serialized object describing the message to be sent"""
    allow_user_chats: Optional[bool] = None
    """Pass :code:`True` if the message can be sent to private chats with users"""
    allow_bot_chats: Optional[bool] = None
    """Pass :code:`True` if the message can be sent to private chats with bots"""
    allow_group_chats: Optional[bool] = None
    """Pass :code:`True` if the message can be sent to group and supergroup chats"""
    allow_channel_chats: Optional[bool] = None
    """Pass :code:`True` if the message can be sent to channel chats"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            user_id: int,
            result: Union[
                InlineQueryResultCachedAudio,
                InlineQueryResultCachedDocument,
                InlineQueryResultCachedGif,
                InlineQueryResultCachedMpeg4Gif,
                InlineQueryResultCachedPhoto,
                InlineQueryResultCachedSticker,
                InlineQueryResultCachedVideo,
                InlineQueryResultCachedVoice,
                InlineQueryResultArticle,
                InlineQueryResultAudio,
                InlineQueryResultContact,
                InlineQueryResultGame,
                InlineQueryResultDocument,
                InlineQueryResultGif,
                InlineQueryResultLocation,
                InlineQueryResultMpeg4Gif,
                InlineQueryResultPhoto,
                InlineQueryResultVenue,
                InlineQueryResultVideo,
                InlineQueryResultVoice,
            ],
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
                user_id=user_id,
                result=result,
                allow_user_chats=allow_user_chats,
                allow_bot_chats=allow_bot_chats,
                allow_group_chats=allow_group_chats,
                allow_channel_chats=allow_channel_chats,
                **__pydantic_kwargs,
            )
