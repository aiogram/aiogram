from enum import StrEnum


class ChatBoostSourceType(StrEnum):
    """
    This object represents a type of chat boost source.

    Source: https://core.telegram.org/bots/api#chatboostsource
    """

    PREMIUM = "premium"
    GIFT_CODE = "gift_code"
    GIVEAWAY = "giveaway"
