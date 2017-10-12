from . import base
from . import fields
from .user import User


class GameHighScore(base.TelegramObject):
    """
    This object represents one row of the high scores table for a game.
    And that‘s about all we’ve got for now.
    If you've got any questions, please check out our Bot FAQ

    https://core.telegram.org/bots/api#gamehighscore
    """
    position: base.Integer = fields.Field()
    user: User = fields.Field(base=User)
    score: base.Integer = fields.Field()
