from __future__ import annotations

from ..types import InlineQueryResult, SentWebAppMessage
from .base import TelegramMethod


class AnswerWebAppQuery(TelegramMethod[SentWebAppMessage]):
    """
    Use this method to set the result of an interaction with a `Web App <https://core.telegram.org/bots/webapps>`_ and send a corresponding message on behalf of the user to the chat from which the query originated. On success, a :class:`aiogram.types.sent_web_app_message.SentWebAppMessage` object is returned.

    Source: https://core.telegram.org/bots/api#answerwebappquery
    """

    __returning__ = SentWebAppMessage
    __api_method__ = "answerWebAppQuery"

    web_app_query_id: str
    """Unique identifier for the query to be answered"""
    result: InlineQueryResult
    """A JSON-serialized object describing the message to be sent"""
