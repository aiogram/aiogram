from __future__ import annotations

from typing import Annotated, TypeAlias

from pydantic import Field

from .chat_boost_source_gift_code import ChatBoostSourceGiftCode
from .chat_boost_source_giveaway import ChatBoostSourceGiveaway
from .chat_boost_source_premium import ChatBoostSourcePremium

ChatBoostSourceUnion: TypeAlias = Annotated[
    ChatBoostSourcePremium | ChatBoostSourceGiftCode | ChatBoostSourceGiveaway,
    Field(discriminator="source"),
]
