from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from .base import TelegramObject

if TYPE_CHECKING:
    from .reaction_type_custom_emoji import ReactionTypeCustomEmoji
    from .reaction_type_emoji import ReactionTypeEmoji
    from .reaction_type_paid import ReactionTypePaid


class ReactionCount(TelegramObject):
    """
    Represents a reaction added to a message along with the number of times it was added.

    Source: https://core.telegram.org/bots/api#reactioncount
    """

    type: Union[ReactionTypeEmoji, ReactionTypeCustomEmoji, ReactionTypePaid]
    """Type of the reaction"""
    total_count: int
    """Number of times the reaction was added"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Union[ReactionTypeEmoji, ReactionTypeCustomEmoji, ReactionTypePaid],
            total_count: int,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(type=type, total_count=total_count, **__pydantic_kwargs)
