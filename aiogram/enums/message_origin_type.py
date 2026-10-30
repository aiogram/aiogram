from enum import StrEnum


class MessageOriginType(StrEnum):
    """
    This object represents origin of a message.

    Source: https://core.telegram.org/bots/api#messageorigin
    """

    USER = "user"
    HIDDEN_USER = "hidden_user"
    CHAT = "chat"
    CHANNEL = "channel"
