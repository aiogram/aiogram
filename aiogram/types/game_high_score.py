from .base import Deserializable
from .user import User


class GameHighScore(Deserializable):
    """
    This object represents one row of the high scores table for a game.
    
    https://core.telegram.org/bots/api#gamehighscore
    """
    def __init__(self, position, user, score):
        self.position: int = position
        self.user: User = user
        self.score: int = score

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        position = raw_data.get('position')
        user = User.deserialize(raw_data.get('user'))
        score = raw_data.get('score')

        return GameHighScore(position, user, score)
