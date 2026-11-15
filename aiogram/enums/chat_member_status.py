from enum import StrEnum


class ChatMemberStatus(StrEnum):
    """
    This object represents chat member status.

    Source: https://core.telegram.org/bots/api#chatmember
    """

    CREATOR = "creator"
    ADMINISTRATOR = "administrator"
    MEMBER = "member"
    RESTRICTED = "restricted"
    LEFT = "left"
    KICKED = "kicked"
