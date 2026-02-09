from enum import Enum


class ButtonStyle(str, Enum):
    """
    This object represents a button style (inline- or reply-keyboard).

    Source: https://core.telegram.org/bots/api#chat
    """

    DANGER = "danger"
    SUCCESS = "success"
    PRIMARY = "primary"
