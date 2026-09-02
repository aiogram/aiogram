from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import TelegramObject

if TYPE_CHECKING:
    from .community import Community


class CommunityChatJoined(TelegramObject):
    """
    Describes a service message about a chat being joined by a user from a community.

    Source: https://core.telegram.org/bots/api#communitychatjoined
    """

    community: Community
    """The community from which the chat was joined"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__, *, community: Community, **__pydantic_kwargs: Any
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(community=community, **__pydantic_kwargs)
