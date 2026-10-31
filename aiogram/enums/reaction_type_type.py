from enum import StrEnum


class ReactionTypeType(StrEnum):
    """
    This object represents reaction type.

    Source: https://core.telegram.org/bots/api#reactiontype
    """

    EMOJI = "emoji"
    CUSTOM_EMOJI = "custom_emoji"
    PAID = "paid"
