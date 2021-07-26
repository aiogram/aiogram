from . import base, fields


class Dice(base.TelegramObject):
    """
    This object represents an animated emoji that displays a random value.
    
    https://core.telegram.org/bots/api#dice
    """
    emoji: base.String = fields.Field()
    value: base.Integer = fields.Field()


class DiceEmoji:
    DICE = '🎲'
    DART = '🎯'
    BASKETBALL = '🏀'
    FOOTBALL = '⚽'
    SLOT_MACHINE = '🎰'
    BOWLING = '🎳'
