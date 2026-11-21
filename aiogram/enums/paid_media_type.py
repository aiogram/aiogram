from enum import StrEnum


class PaidMediaType(StrEnum):
    """
    This object represents the type of a media in a paid message.

    Source: https://core.telegram.org/bots/api#paidmedia
    """

    PHOTO = "photo"
    PREVIEW = "preview"
    VIDEO = "video"
    LIVE_PHOTO = "live_photo"
