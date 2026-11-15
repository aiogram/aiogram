from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import TelegramObject

if TYPE_CHECKING:
    from .area_position import AreaPosition
    from .ton_nft import TonNft


class TonWalletCardSticker(TelegramObject):
    """
    This object describes a sticker on a TON wallet card.

    Source: https://core.telegram.org/bots/api#tonwalletcardsticker
    """

    position: AreaPosition
    """Position of the sticker on the card"""
    nft: TonNft
    """The NFT shown as the sticker"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__, *, position: AreaPosition, nft: TonNft, **__pydantic_kwargs: Any
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(position=position, nft=nft, **__pydantic_kwargs)
