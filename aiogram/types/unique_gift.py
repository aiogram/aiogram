from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from .base import TelegramObject

if TYPE_CHECKING:
    from .chat import Chat
    from .unique_gift_backdrop import UniqueGiftBackdrop
    from .unique_gift_model import UniqueGiftModel
    from .unique_gift_symbol import UniqueGiftSymbol


class UniqueGift(TelegramObject):
    """
    This object describes a unique gift that was upgraded from a regular gift.

    Source: https://core.telegram.org/bots/api#uniquegift
    """

    base_name: str
    """Human-readable name of the regular gift from which this unique gift was upgraded"""
    name: str
    """Unique name of the gift. This name can be used in :code:`https://t.me/nft/...` links and story areas"""
    number: int
    """Unique number of the upgraded gift among gifts upgraded from the same regular gift"""
    model: UniqueGiftModel
    """Model of the gift"""
    symbol: UniqueGiftSymbol
    """Symbol of the gift"""
    backdrop: UniqueGiftBackdrop
    """Backdrop of the gift"""
    publisher_chat: Optional[Chat] = None
    """*Optional*. Information about the chat that published the gift"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            base_name: str,
            name: str,
            number: int,
            model: UniqueGiftModel,
            symbol: UniqueGiftSymbol,
            backdrop: UniqueGiftBackdrop,
            publisher_chat: Optional[Chat] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                base_name=base_name,
                name=name,
                number=number,
                model=model,
                symbol=symbol,
                backdrop=backdrop,
                publisher_chat=publisher_chat,
                **__pydantic_kwargs,
            )
