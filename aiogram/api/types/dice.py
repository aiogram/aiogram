from __future__ import annotations

from .base import TelegramObject


class Dice(TelegramObject):
    """
    This object represents a dice with a random value from 1 to 6 for currently supported base
    emoji. (Yes, we're aware of the 'proper' singular of die. But it's awkward, and we decided to
    help it change. One dice at a time!)

    Source: https://core.telegram.org/bots/api#dice
    """

    emoji: str
    """Emoji on which the dice throw animation is based"""
    value: int
    """Value of the dice, 1-6 for currently supported base emoji"""


class DiceEmoji:
    DICE = "🎲"
    DART = "🎯"
