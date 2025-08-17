from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from .base import TelegramObject

if TYPE_CHECKING:
    from .user import User


class DirectMessagesTopic(TelegramObject):
    """
    Describes a topic of a direct messages chat.

    Source: https://core.telegram.org/bots/api#directmessagestopic
    """

    topic_id: int
    """Unique identifier of the topic"""
    user: Optional[User] = None
    """*Optional*. Information about the user that created the topic. Currently, it is always present"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            topic_id: int,
            user: Optional[User] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(topic_id=topic_id, user=user, **__pydantic_kwargs)
