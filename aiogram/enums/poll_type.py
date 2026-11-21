from enum import StrEnum


class PollType(StrEnum):
    """
    This object represents poll type

    Source: https://core.telegram.org/bots/api#poll
    """

    REGULAR = "regular"
    QUIZ = "quiz"
