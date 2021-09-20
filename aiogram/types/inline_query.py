from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from pydantic import Field

from .base import TelegramObject

if TYPE_CHECKING:
    from ..methods import AnswerInlineQuery
    from .inline_query_result import InlineQueryResult
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
    """*Optional*. Type of the chat, from which the inline query was sent. Can be either 'sender' for a private chat with the inline query sender, 'private', 'group', 'supergroup', or 'channel'. The chat type should be always known for requests sent from official clients and most third-party clients, unless the request was sent from a secret chat"""
    location: Optional[Location] = None
    """*Optional*. Sender location, only for bots that request user location"""

    def answer(
        self,
        results: List[InlineQueryResult],
        cache_time: Optional[int] = None,
        is_personal: Optional[bool] = None,
        next_offset: Optional[str] = None,
        switch_pm_text: Optional[str] = None,
        switch_pm_parameter: Optional[str] = None,
    ) -> AnswerInlineQuery:
        """
        :param results:
        :param cache_time:
        :param is_personal:
        :param next_offset:
        :param switch_pm_text:
        :param switch_pm_parameter:
        :return:
        """
        from ..methods import AnswerInlineQuery

        return AnswerInlineQuery(
            inline_query_id=self.id,
            results=results,
            cache_time=cache_time,
            is_personal=is_personal,
            next_offset=next_offset,
            switch_pm_text=switch_pm_text,
            switch_pm_parameter=switch_pm_parameter,
        )
