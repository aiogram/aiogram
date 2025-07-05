from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from pydantic import Field

from ..client.default import Default
from ..types import (
    ChatIdUnion,
    DateTimeUnion,
    InputPollOptionUnion,
    Message,
    MessageEntity,
    ReplyMarkupUnion,
    ReplyParameters,
)
from .base import TelegramMethod


class SendPoll(TelegramMethod[Message]):
    """
    Use this method to send a native poll. On success, the sent :class:`aiogram.types.message.Message` is returned.

    Source: https://core.telegram.org/bots/api#sendpoll
    """

    __returning__ = Message
    __api_method__ = "sendPoll"

    chat_id: ChatIdUnion
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    question: str
    """Poll question, 1-300 characters"""
    options: list[InputPollOptionUnion]
    """A JSON-serialized list of 2-12 answer options"""
    business_connection_id: Optional[str] = None
    """Unique identifier of the business connection on behalf of which the message will be sent"""
    message_thread_id: Optional[int] = None
    """Unique identifier for the target message thread (topic) of the forum; for forum supergroups only"""
    question_parse_mode: Optional[Union[str, Default]] = Default("parse_mode")
    """Mode for parsing entities in the question. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details. Currently, only custom emoji entities are allowed"""
    question_entities: Optional[list[MessageEntity]] = None
    """A JSON-serialized list of special entities that appear in the poll question. It can be specified instead of *question_parse_mode*"""
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
    explanation_parse_mode: Optional[Union[str, Default]] = Default("parse_mode")
    """Mode for parsing entities in the explanation. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details."""
    explanation_entities: Optional[list[MessageEntity]] = None
    """A JSON-serialized list of special entities that appear in the poll explanation. It can be specified instead of *explanation_parse_mode*"""
    open_period: Optional[int] = None
    """Amount of time in seconds the poll will be active after creation, 5-600. Can't be used together with *close_date*."""
    close_date: Optional[DateTimeUnion] = None
    """Point in time (Unix timestamp) when the poll will be automatically closed. Must be at least 5 and no more than 600 seconds in the future. Can't be used together with *open_period*."""
    is_closed: Optional[bool] = None
    """Pass :code:`True` if the poll needs to be immediately closed. This can be useful for poll preview."""
    disable_notification: Optional[bool] = None
    """Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound."""
    protect_content: Optional[Union[bool, Default]] = Default("protect_content")
    """Protects the contents of the sent message from forwarding and saving"""
    allow_paid_broadcast: Optional[bool] = None
    """Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance"""
    message_effect_id: Optional[str] = None
    """Unique identifier of the message effect to be added to the message; for private chats only"""
    reply_parameters: Optional[ReplyParameters] = None
    """Description of the message to reply to"""
    reply_markup: Optional[ReplyMarkupUnion] = None
    """Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user"""
    allow_sending_without_reply: Optional[bool] = Field(
        None, json_schema_extra={"deprecated": True}
    )
    """Pass :code:`True` if the message should be sent even if the specified replied-to message is not found

.. deprecated:: API:7.0
   https://core.telegram.org/bots/api-changelog#december-29-2023"""
    reply_to_message_id: Optional[int] = Field(None, json_schema_extra={"deprecated": True})
    """If the message is a reply, ID of the original message

.. deprecated:: API:7.0
   https://core.telegram.org/bots/api-changelog#december-29-2023"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            chat_id: ChatIdUnion,
            question: str,
            options: list[InputPollOptionUnion],
            business_connection_id: Optional[str] = None,
            message_thread_id: Optional[int] = None,
            question_parse_mode: Optional[Union[str, Default]] = Default("parse_mode"),
            question_entities: Optional[list[MessageEntity]] = None,
            is_anonymous: Optional[bool] = None,
            type: Optional[str] = None,
            allows_multiple_answers: Optional[bool] = None,
            correct_option_id: Optional[int] = None,
            explanation: Optional[str] = None,
            explanation_parse_mode: Optional[Union[str, Default]] = Default("parse_mode"),
            explanation_entities: Optional[list[MessageEntity]] = None,
            open_period: Optional[int] = None,
            close_date: Optional[DateTimeUnion] = None,
            is_closed: Optional[bool] = None,
            disable_notification: Optional[bool] = None,
            protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
            allow_paid_broadcast: Optional[bool] = None,
            message_effect_id: Optional[str] = None,
            reply_parameters: Optional[ReplyParameters] = None,
            reply_markup: Optional[ReplyMarkupUnion] = None,
            allow_sending_without_reply: Optional[bool] = None,
            reply_to_message_id: Optional[int] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                chat_id=chat_id,
                question=question,
                options=options,
                business_connection_id=business_connection_id,
                message_thread_id=message_thread_id,
                question_parse_mode=question_parse_mode,
                question_entities=question_entities,
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
                allow_paid_broadcast=allow_paid_broadcast,
                message_effect_id=message_effect_id,
                reply_parameters=reply_parameters,
                reply_markup=reply_markup,
                allow_sending_without_reply=allow_sending_without_reply,
                reply_to_message_id=reply_to_message_id,
                **__pydantic_kwargs,
            )
