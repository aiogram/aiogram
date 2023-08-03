from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import TelegramObject


class MessageId(TelegramObject):
    """
    This object represents a unique message identifier.

    Source: https://core.telegram.org/bots/api#messageid
    """

    message_id: int
    """Unique message identifier"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(__pydantic__self__, *, message_id: int, **__pydantic_kwargs: Any) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(message_id=message_id, **__pydantic_kwargs)
