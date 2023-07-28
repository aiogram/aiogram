from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional, Union

from pydantic import Field

from .base import TelegramObject

if TYPE_CHECKING:
    from ..methods import AnswerInlineQuery
    from .inline_query_result_article import InlineQueryResultArticle
    from .inline_query_result_audio import InlineQueryResultAudio
    from .inline_query_result_cached_audio import InlineQueryResultCachedAudio
    from .inline_query_result_cached_document import InlineQueryResultCachedDocument
    from .inline_query_result_cached_gif import InlineQueryResultCachedGif
    from .inline_query_result_cached_mpeg4_gif import InlineQueryResultCachedMpeg4Gif
    from .inline_query_result_cached_photo import InlineQueryResultCachedPhoto
    from .inline_query_result_cached_sticker import InlineQueryResultCachedSticker
    from .inline_query_result_cached_video import InlineQueryResultCachedVideo
    from .inline_query_result_cached_voice import InlineQueryResultCachedVoice
    from .inline_query_result_contact import InlineQueryResultContact
    from .inline_query_result_document import InlineQueryResultDocument
    from .inline_query_result_game import InlineQueryResultGame
    from .inline_query_result_gif import InlineQueryResultGif
    from .inline_query_result_location import InlineQueryResultLocation
    from .inline_query_result_mpeg4_gif import InlineQueryResultMpeg4Gif
    from .inline_query_result_photo import InlineQueryResultPhoto
    from .inline_query_result_venue import InlineQueryResultVenue
    from .inline_query_result_video import InlineQueryResultVideo
    from .inline_query_result_voice import InlineQueryResultVoice
    from .inline_query_results_button import InlineQueryResultsButton
    from .location import Location
    from .user import User


class InlineQuery(TelegramObject):
    """
    This object represents an incoming inline query. When the user sends an empty query, your bot could return some default or trending results.

    Source: https://core.telegram.org/bots/api#inlinequery
    """

    id: str
    """Unique identifier for this query"""
    from_user: User = Field(..., alias="from")
    """Sender"""
    query: str
    """Text of the query (up to 256 characters)"""
    offset: str
    """Offset of the results to be returned, can be controlled by the bot"""
    chat_type: Optional[str] = None
    """*Optional*. Type of the chat from which the inline query was sent. Can be either 'sender' for a private chat with the inline query sender, 'private', 'group', 'supergroup', or 'channel'. The chat type should be always known for requests sent from official clients and most third-party clients, unless the request was sent from a secret chat"""
    location: Optional[Location] = None
    """*Optional*. Sender location, only for bots that request user location"""

    def answer(
        self,
        results: List[
            Union[
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
        ],
        cache_time: Optional[int] = None,
        is_personal: Optional[bool] = None,
        next_offset: Optional[str] = None,
        button: Optional[InlineQueryResultsButton] = None,
        switch_pm_parameter: Optional[str] = None,
        switch_pm_text: Optional[str] = None,
        **kwargs: Any,
    ) -> AnswerInlineQuery:
        """
        Shortcut for method :class:`aiogram.methods.answer_inline_query.AnswerInlineQuery`
        will automatically fill method attributes:

        - :code:`inline_query_id`

        Use this method to send answers to an inline query. On success, :code:`True` is returned.

        No more than **50** results per query are allowed.

        Source: https://core.telegram.org/bots/api#answerinlinequery

        :param results: A JSON-serialized array of results for the inline query
        :param cache_time: The maximum amount of time in seconds that the result of the inline query may be cached on the server. Defaults to 300.
        :param is_personal: Pass :code:`True` if results may be cached on the server side only for the user that sent the query. By default, results may be returned to any user who sends the same query.
        :param next_offset: Pass the offset that a client should send in the next query with the same text to receive more results. Pass an empty string if there are no more results or if you don't support pagination. Offset length can't exceed 64 bytes.
        :param button: A JSON-serialized object describing a button to be shown above inline query results
        :param switch_pm_parameter: `Deep-linking <https://core.telegram.org/bots/features#deep-linking>`_ parameter for the /start message sent to the bot when user presses the switch button. 1-64 characters, only :code:`A-Z`, :code:`a-z`, :code:`0-9`, :code:`_` and :code:`-` are allowed.
        :param switch_pm_text: If passed, clients will display a button with specified text that switches the user to a private chat with the bot and sends the bot a start message with the parameter *switch_pm_parameter*
        :return: instance of method :class:`aiogram.methods.answer_inline_query.AnswerInlineQuery`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import AnswerInlineQuery

        return AnswerInlineQuery(
            inline_query_id=self.id,
            results=results,
            cache_time=cache_time,
            is_personal=is_personal,
            next_offset=next_offset,
            button=button,
            switch_pm_parameter=switch_pm_parameter,
            switch_pm_text=switch_pm_text,
            **kwargs,
        ).as_(self._bot)
