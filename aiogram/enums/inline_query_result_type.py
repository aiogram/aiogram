from enum import Enum


class InlineQueryResultType(str, Enum):
    """
    The part of the face relative to which the mask should be placed.

    Source: https://core.telegram.org/bots/api#maskposition
    """

    AUDIO = "audio"
    DOCUMENT = "document"
    GIF = "gif"
    MPEG = "mpeg"
    PHOTO = "photo"
    STICKER = "sticker"
    VIDEO = "video"
    VOICE = "voice"
    ARTICLE = "article"
    CONTACT = "contact"
    GAME = "game"
    LOCATION = "location"
    VENUE = "venue"
