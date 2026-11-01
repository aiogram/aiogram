from enum import StrEnum


class InputMediaType(StrEnum):
    """
    This object represents input media type

    Source: https://core.telegram.org/bots/api#inputmedia
    """

    ANIMATION = "animation"
    AUDIO = "audio"
    DOCUMENT = "document"
    PHOTO = "photo"
    VIDEO = "video"
    LIVE_PHOTO = "live_photo"
    VENUE = "venue"
    STICKER = "sticker"
    LOCATION = "location"
