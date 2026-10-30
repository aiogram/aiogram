from enum import StrEnum


class StickerFormat(StrEnum):
    """
    Format of the sticker

    Source: https://core.telegram.org/bots/api#createnewstickerset
    """

    STATIC = "static"
    ANIMATED = "animated"
    VIDEO = "video"
