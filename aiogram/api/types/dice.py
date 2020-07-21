from __future__ import annotations

from .base import TelegramObject


class Dice(TelegramObject):
    """
    This object represents an animated emoji that displays a random value.

    Source: https://core.telegram.org/bots/api#dice
    """

    emoji: str
    """Emoji on which the dice throw animation is based"""
    value: int
    """Value of the dice, 1-6 for '' and '' base emoji, 1-5 for '' base emoji"""


class DiceEmoji:
    DICE = "🎲"
    DART = "🎯"
