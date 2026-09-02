from typing import TYPE_CHECKING, Any

from .base import TelegramObject


class Community(TelegramObject):
    """
    Represents a community (a group of chats).

    Source: https://core.telegram.org/bots/api#community
    """

    id: int
    """Unique identifier for this community. This number may have more than 32 significant bits and some programming languages may have difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a signed 64-bit integer or double-precision float type are safe for storing this identifier"""
    name: str
    """Name of the community"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(__pydantic__self__, *, id: int, name: str, **__pydantic_kwargs: Any) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(id=id, name=name, **__pydantic_kwargs)
