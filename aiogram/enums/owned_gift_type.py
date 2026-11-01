from enum import StrEnum


class OwnedGiftType(StrEnum):
    """
    This object represents owned gift type

    Source: https://core.telegram.org/bots/api#ownedgift
    """

    REGULAR = "regular"
    UNIQUE = "unique"
