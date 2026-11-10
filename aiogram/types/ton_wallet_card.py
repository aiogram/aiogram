from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import TelegramObject

if TYPE_CHECKING:
    from .ton_wallet_card_sticker import TonWalletCardSticker


class TonWalletCard(TelegramObject):
    """
    This object describes a TON wallet card, which is shown on the profile page of a user to everyone.

    Source: https://core.telegram.org/bots/api#tonwalletcard
    """

    address: str
    """Address of the wallet"""
    amount: str
    """Balance of the wallet, in the *smallest units* of the cryptocurrency, as a decimal number"""
    stickers: list[TonWalletCardSticker]
    """Stickers placed on the card"""
    background_nft_address: str | None = None
    """*Optional*. Address of the NFT of one of the stickers, whose colors must be used for the card background; omitted if the default background must be used"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            address: str,
            amount: str,
            stickers: list[TonWalletCardSticker],
            background_nft_address: str | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                address=address,
                amount=amount,
                stickers=stickers,
                background_nft_address=background_nft_address,
                **__pydantic_kwargs,
            )
