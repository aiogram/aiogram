from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional

from .base import TelegramObject

if TYPE_CHECKING:
    from .chat import Chat
    from .user import User


class PollAnswer(TelegramObject):
    """
    This object represents an answer of a user in a non-anonymous poll.

    Source: https://core.telegram.org/bots/api#pollanswer
    """

    poll_id: str
    """Unique poll identifier"""
    option_ids: List[int]
    """0-based identifiers of chosen answer options. May be empty if the vote was retracted."""
    voter_chat: Optional[Chat] = None
    """*Optional*. The chat that changed the answer to the poll, if the voter is anonymous"""
    user: Optional[User] = None
    """*Optional*. The user that changed the answer to the poll, if the voter isn't anonymous"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            poll_id: str,
            option_ids: List[int],
            voter_chat: Optional[Chat] = None,
            user: Optional[User] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                poll_id=poll_id,
                option_ids=option_ids,
                voter_chat=voter_chat,
                user=user,
                **__pydantic_kwargs,
            )
