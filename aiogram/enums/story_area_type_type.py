from enum import StrEnum


class StoryAreaTypeType(StrEnum):
    """
    This object represents input profile photo type

    Source: https://core.telegram.org/bots/api#storyareatype
    """

    LOCATION = "location"
    SUGGESTED_REACTION = "suggested_reaction"
    LINK = "link"
    WEATHER = "weather"
    UNIQUE_GIFT = "unique_gift"
