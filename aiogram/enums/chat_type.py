from enum import Enum


class ChatType(str, Enum):
    """
    Type of chat
    """

    PRIVATE = "private"
    GROUP = "group"
    SUPERGROUP = "supergroup"
    CHANNEL = "channel"
