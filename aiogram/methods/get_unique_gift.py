from typing import TYPE_CHECKING, Any

from ..types import UniqueGift
from .base import TelegramMethod


class GetUniqueGift(TelegramMethod[UniqueGift]):
    """
    Use this method to get information about a unique gift by its name. Returns a :class:`aiogram.types.unique_gift.UniqueGift` object on success.

    Source: https://core.telegram.org/bots/api#getuniquegift
    """

    __returning__ = UniqueGift
    __api_method__ = "getUniqueGift"

    name: str
    """Unique name of the gift"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(__pydantic__self__, *, name: str, **__pydantic_kwargs: Any) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(name=name, **__pydantic_kwargs)
