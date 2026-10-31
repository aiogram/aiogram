from enum import StrEnum


class InputStoryContentType(StrEnum):
    """
    This object represents input story content photo type.

    Source: https://core.telegram.org/bots/api#inputstorycontentphoto
    """

    PHOTO = "photo"
    VIDEO = "video"
