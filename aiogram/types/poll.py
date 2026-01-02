from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import TelegramObject
from .custom import DateTime

if TYPE_CHECKING:
    from .message_entity import MessageEntity
    from .poll_option import PollOption


class Poll(TelegramObject):
    """
    This object contains information about a poll.

    Source: https://core.telegram.org/bots/api#poll
    """

    id: str
    """Unique poll identifier"""
    question: str
    """Poll question, 1-300 characters"""
    options: list[PollOption]
    """List of poll options"""
    total_voter_count: int
    """Total number of users that voted in the poll"""
    is_closed: bool
    """:code:`True`, if the poll is closed"""
    is_anonymous: bool
    """:code:`True`, if the poll is anonymous"""
    type: str
    """Poll type, currently can be 'regular' or 'quiz'"""
    allows_multiple_answers: bool
    """:code:`True`, if the poll allows multiple answers"""
    question_entities: list[MessageEntity] | None = None
    """*Optional*. Special entities that appear in the *question*. Currently, only custom emoji entities are allowed in poll questions"""
    correct_option_id: int | None = None
    """*Optional*. 0-based identifier of the correct answer option. Available only for polls in the quiz mode, which are closed, or was sent (not forwarded) by the bot or to the private chat with the bot."""
    explanation: str | None = None
    """*Optional*. Text that is shown when a user chooses an incorrect answer or taps on the lamp icon in a quiz-style poll, 0-200 characters"""
    explanation_entities: list[MessageEntity] | None = None
    """*Optional*. Special entities like usernames, URLs, bot commands, etc. that appear in the *explanation*"""
    open_period: int | None = None
    """*Optional*. Amount of time in seconds the poll will be active after creation"""
    close_date: DateTime | None = None
    """*Optional*. Point in time (Unix timestamp) when the poll will be automatically closed"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            id: str,
            question: str,
            options: list[PollOption],
            total_voter_count: int,
            is_closed: bool,
            is_anonymous: bool,
            type: str,
            allows_multiple_answers: bool,
            question_entities: list[MessageEntity] | None = None,
            correct_option_id: int | None = None,
            explanation: str | None = None,
            explanation_entities: list[MessageEntity] | None = None,
            open_period: int | None = None,
            close_date: DateTime | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                id=id,
                question=question,
                options=options,
                total_voter_count=total_voter_count,
                is_closed=is_closed,
                is_anonymous=is_anonymous,
                type=type,
                allows_multiple_answers=allows_multiple_answers,
                question_entities=question_entities,
                correct_option_id=correct_option_id,
                explanation=explanation,
                explanation_entities=explanation_entities,
                open_period=open_period,
                close_date=close_date,
                **__pydantic_kwargs,
            )
