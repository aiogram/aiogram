from enum import StrEnum


class InputProfilePhotoType(StrEnum):
    """
    This object represents input profile photo type

    Source: https://core.telegram.org/bots/api#inputprofilephoto
    """

    STATIC = "static"
    ANIMATED = "animated"
