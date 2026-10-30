from enum import StrEnum


class KeyboardButtonPollTypeType(StrEnum):
    """
    This object represents type of a poll, which is allowed to be created and sent when the corresponding button is pressed.

    Source: https://core.telegram.org/bots/api#keyboardbuttonpolltype
    """

    QUIZ = "quiz"
    REGULAR = "regular"
