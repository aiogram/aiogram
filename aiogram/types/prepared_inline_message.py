from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, Union

from .base import TelegramObject


class PreparedInlineMessage(TelegramObject):
    """
    Describes an inline message to be sent by a user of a Mini App.

    Source: https://core.telegram.org/bots/api#preparedinlinemessage
    """

    id: str
    """Unique identifier of the prepared message"""
    expiration_date: Union[datetime.datetime, datetime.timedelta, int]
    """Expiration date of the prepared message, in Unix time. Expired prepared messages can no longer be used"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            id: str,
            expiration_date: Union[datetime.datetime, datetime.timedelta, int],
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(id=id, expiration_date=expiration_date, **__pydantic_kwargs)
