from typing import Any, Dict, List, Optional

from ..types import InlineQueryResult
from .base import Request, TelegramMethod, prepare_parse_mode


class AnswerInlineQuery(TelegramMethod[bool]):
    """
    Use this method to send answers to an inline query. On success, True is returned.
    No more than 50 results per query are allowed.

    Source: https://core.telegram.org/bots/api#answerinlinequery
    """

    __returning__ = bool

    inline_query_id: str
    """Unique identifier for the answered query"""
    results: List[InlineQueryResult]
    """A JSON-serialized array of results for the inline query"""
    cache_time: Optional[int] = None
    """The maximum amount of time in seconds that the result of the inline query may be cached on
    the server. Defaults to 300."""
    is_personal: Optional[bool] = None
    """Pass True, if results may be cached on the server side only for the user that sent the
    query. By default, results may be returned to any user who sends the same query"""
    next_offset: Optional[str] = None
    """Pass the offset that a client should send in the next query with the same text to receive
    more results. Pass an empty string if there are no more results or if you don‘t support
    pagination. Offset length can’t exceed 64 bytes."""
    switch_pm_text: Optional[str] = None
    """If passed, clients will display a button with specified text that switches the user to a
    private chat with the bot and sends the bot a start message with the parameter
    switch_pm_parameter"""
    switch_pm_parameter: Optional[str] = None
    """Deep-linking parameter for the /start message sent to the bot when user presses the switch
    button. 1-64 characters, only A-Z, a-z, 0-9, _ and - are allowed."""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict()
        prepare_parse_mode(data["results"])

        return Request(method="answerInlineQuery", data=data)
