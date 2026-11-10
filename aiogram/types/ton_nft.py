from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import TelegramObject

if TYPE_CHECKING:
    from .ton_nft_attribute import TonNftAttribute
    from .unique_gift import UniqueGift


class TonNft(TelegramObject):
    """
    This object represents an NFT in the TON blockchain.

    Source: https://core.telegram.org/bots/api#tonnft
    """

    address: str
    """Address of the NFT"""
    index: str
    """Index of the NFT among all NFTs from the collection as a decimal number"""
    name: str
    """Name of the NFT"""
    description: str
    """Description of the NFT"""
    collection_address: str | None = None
    """*Optional*. Address of the collection to which the NFT belongs; omitted if unknown"""
    attributes: list[TonNftAttribute] | None = None
    """*Optional*. Attributes of the NFT"""
    gift: UniqueGift | None = None
    """*Optional*. The unique gift corresponding to the NFT"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            address: str,
            index: str,
            name: str,
            description: str,
            collection_address: str | None = None,
            attributes: list[TonNftAttribute] | None = None,
            gift: UniqueGift | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                address=address,
                index=index,
                name=name,
                description=description,
                collection_address=collection_address,
                attributes=attributes,
                gift=gift,
                **__pydantic_kwargs,
            )
