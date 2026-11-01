from enum import StrEnum


class ChatType(StrEnum):
    """
    This object represents a chat type

    Source: https://core.telegram.org/bots/api#chat
    """

    SENDER = "sender"
    PRIVATE = "private"
    GROUP = "group"
    SUPERGROUP = "supergroup"
    CHANNEL = "channel"
