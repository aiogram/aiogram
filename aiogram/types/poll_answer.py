from __future__ import annotations

from typing import TYPE_CHECKING, Any, List

from .base import TelegramObject

if TYPE_CHECKING:
    from .user import User


class PollAnswer(TelegramObject):
    """
    This object represents an answer of a user in a non-anonymous poll.

    Source: https://core.telegram.org/bots/api#pollanswer
    """

    poll_id: str
    """Unique poll identifier"""
    user: User
    """The user, who changed the answer to the poll"""
    option_ids: List[int]
    """0-based identifiers of answer options, chosen by the user. May be empty if the user retracted their vote."""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            poll_id: str,
            user: User,
            option_ids: List[int],
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                poll_id=poll_id, user=user, option_ids=option_ids, **__pydantic_kwargs
            )
