from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..types import InlineQueryResult
from .base import Request, TelegramMethod, prepare_parse_mode

if TYPE_CHECKING:
    from ..client.bot import Bot


class AnswerInlineQuery(TelegramMethod[bool]):
    """
    Use this method to send answers to an inline query. On success, :code:`True` is returned.

    No more than **50** results per query are allowed.

    Source: https://core.telegram.org/bots/api#answerinlinequery
    """

    __returning__ = bool

    inline_query_id: str
    """Unique identifier for the answered query"""
    results: List[InlineQueryResult]
    """A JSON-serialized array of results for the inline query"""
    cache_time: Optional[int] = None
    """The maximum amount of time in seconds that the result of the inline query may be cached on the server. Defaults to 300."""
    is_personal: Optional[bool] = None
    """Pass :code:`True`, if results may be cached on the server side only for the user that sent the query. By default, results may be returned to any user who sends the same query"""
    next_offset: Optional[str] = None
    """Pass the offset that a client should send in the next query with the same text to receive more results. Pass an empty string if there are no more results or if you don't support pagination. Offset length can't exceed 64 bytes."""
    switch_pm_text: Optional[str] = None
    """If passed, clients will display a button with specified text that switches the user to a private chat with the bot and sends the bot a start message with the parameter *switch_pm_parameter*"""
    switch_pm_parameter: Optional[str] = None
    """`Deep-linking <https://core.telegram.org/bots#deep-linking>`_ parameter for the /start message sent to the bot when user presses the switch button. 1-64 characters, only :code:`A-Z`, :code:`a-z`, :code:`0-9`, :code:`_` and :code:`-` are allowed."""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        input_message_contents = []
        for result in data["results"]:
            input_message_content = result.get("input_message_content", None)
            if input_message_content is not None:
                input_message_contents.append(input_message_content)

        prepare_parse_mode(bot, data["results"] + input_message_contents)
        return Request(method="answerInlineQuery", data=data)
