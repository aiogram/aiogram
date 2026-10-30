from enum import StrEnum


class MaskPositionPoint(StrEnum):
    """
    The part of the face relative to which the mask should be placed.

    Source: https://core.telegram.org/bots/api#maskposition
    """

    FOREHEAD = "forehead"
    EYES = "eyes"
    MOUTH = "mouth"
    CHIN = "chin"
