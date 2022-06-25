from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from ..types import InlineQueryResult, SentWebAppMessage
from .base import Request, TelegramMethod, prepare_parse_mode

if TYPE_CHECKING:
    from ..client.bot import Bot


class AnswerWebAppQuery(TelegramMethod[SentWebAppMessage]):
    """
    Use this method to set the result of an interaction with a `Web App <https://core.telegram.org/bots/webapps>`_ and send a corresponding message on behalf of the user to the chat from which the query originated. On success, a :class:`aiogram.types.sent_web_app_message.SentWebAppMessage` object is returned.

    Source: https://core.telegram.org/bots/api#answerwebappquery
    """

    __returning__ = SentWebAppMessage

    web_app_query_id: str
    """Unique identifier for the query to be answered"""
    result: InlineQueryResult
    """A JSON-serialized object describing the message to be sent"""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        prepare_parse_mode(
            bot, data["result"], parse_mode_property="parse_mode", entities_property="entities"
        )

        return Request(method="answerWebAppQuery", data=data)
