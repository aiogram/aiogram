from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, List, Optional, Union

from ..types import (
    UNSET_PARSE_MODE,
    ForceReply,
    InlineKeyboardMarkup,
    Message,
    MessageEntity,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from ..types.base import UNSET_PROTECT_CONTENT
from .base import TelegramMethod


class SendPoll(TelegramMethod[Message]):
    """
    Use this method to send a native poll. On success, the sent :class:`aiogram.types.message.Message` is returned.

    Source: https://core.telegram.org/bots/api#sendpoll
    """

    __returning__ = Message
    __api_method__ = "sendPoll"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    question: str
    """Poll question, 1-300 characters"""
    options: List[str]
    """A JSON-serialized list of answer options, 2-10 strings 1-100 characters each"""
    message_thread_id: Optional[int] = None
    """Unique identifier for the target message thread (topic) of the forum; for forum supergroups only"""
    is_anonymous: Optional[bool] = None
    """:code:`True`, if the poll needs to be anonymous, defaults to :code:`True`"""
    type: Optional[str] = None
    """Poll type, 'quiz' or 'regular', defaults to 'regular'"""
    allows_multiple_answers: Optional[bool] = None
    """:code:`True`, if the poll allows multiple answers, ignored for polls in quiz mode, defaults to :code:`False`"""
    correct_option_id: Optional[int] = None
    """0-based identifier of the correct answer option, required for polls in quiz mode"""
    explanation: Optional[str] = None
    """Text that is shown when a user chooses an incorrect answer or taps on the lamp icon in a quiz-style poll, 0-200 characters with at most 2 line feeds after entities parsing"""
    explanation_parse_mode: Optional[str] = UNSET_PARSE_MODE
    """Mode for parsing entities in the explanation. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details."""
    explanation_entities: Optional[List[MessageEntity]] = None
    """A JSON-serialized list of special entities that appear in the poll explanation, which can be specified instead of *parse_mode*"""
    open_period: Optional[int] = None
    """Amount of time in seconds the poll will be active after creation, 5-600. Can't be used together with *close_date*."""
    close_date: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None
    """Point in time (Unix timestamp) when the poll will be automatically closed. Must be at least 5 and no more than 600 seconds in the future. Can't be used together with *open_period*."""
    is_closed: Optional[bool] = None
    """Pass :code:`True` if the poll needs to be immediately closed. This can be useful for poll preview."""
    disable_notification: Optional[bool] = None
    """Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound."""
    protect_content: Optional[bool] = UNSET_PROTECT_CONTENT
    """Protects the contents of the sent message from forwarding and saving"""
    reply_to_message_id: Optional[int] = None
    """If the message is a reply, ID of the original message"""
    allow_sending_without_reply: Optional[bool] = None
    """Pass :code:`True` if the message should be sent even if the specified replied-to message is not found"""
    reply_markup: Optional[
        Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
    ] = None
    """Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user."""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            chat_id: Union[int, str],
            question: str,
            options: List[str],
            message_thread_id: Optional[int] = None,
            is_anonymous: Optional[bool] = None,
            type: Optional[str] = None,
            allows_multiple_answers: Optional[bool] = None,
            correct_option_id: Optional[int] = None,
            explanation: Optional[str] = None,
            explanation_parse_mode: Optional[str] = UNSET_PARSE_MODE,
            explanation_entities: Optional[List[MessageEntity]] = None,
            open_period: Optional[int] = None,
            close_date: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None,
            is_closed: Optional[bool] = None,
            disable_notification: Optional[bool] = None,
            protect_content: Optional[bool] = UNSET_PROTECT_CONTENT,
            reply_to_message_id: Optional[int] = None,
            allow_sending_without_reply: Optional[bool] = None,
            reply_markup: Optional[
                Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
            ] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                chat_id=chat_id,
                question=question,
                options=options,
                message_thread_id=message_thread_id,
                is_anonymous=is_anonymous,
                type=type,
                allows_multiple_answers=allows_multiple_answers,
                correct_option_id=correct_option_id,
                explanation=explanation,
                explanation_parse_mode=explanation_parse_mode,
                explanation_entities=explanation_entities,
                open_period=open_period,
                close_date=close_date,
                is_closed=is_closed,
                disable_notification=disable_notification,
                protect_content=protect_content,
                reply_to_message_id=reply_to_message_id,
                allow_sending_without_reply=allow_sending_without_reply,
                reply_markup=reply_markup,
                **__pydantic_kwargs,
            )
