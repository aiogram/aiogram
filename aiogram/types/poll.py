import typing

from ..utils import helper
from . import base, fields
from .user import User


class PollOption(base.TelegramObject):
    """
    This object contains information about one answer option in a poll.

    https://core.telegram.org/bots/api#polloption
    """

    text: base.String = fields.Field()
    voter_count: base.Integer = fields.Field()


class PollAnswer(base.TelegramObject):
    """
    This object represents an answer of a user in a non-anonymous poll.
    
    https://core.telegram.org/bots/api#pollanswer
    """

    poll_id: base.String = fields.Field()
    user: User = fields.Field(base=User)
    option_ids: typing.List[base.Integer] = fields.ListField()


class Poll(base.TelegramObject):
    """
    This object contains information about a poll.
    
    https://core.telegram.org/bots/api#poll
    """

    id: base.String = fields.Field()
    question: base.String = fields.Field()
    options: typing.List[PollOption] = fields.ListField(base=PollOption)
    total_voter_count: base.Integer = fields.Field()
    is_closed: base.Boolean = fields.Field()
    is_anonymous: base.Boolean = fields.Field()
    type: base.String = fields.Field()
    allows_multiple_answers: base.Boolean = fields.Field()
    correct_option_id: base.Integer = fields.Field()


class PollType(helper.Helper):
    mode = helper.HelperMode.snake_case

    REGULAR = helper.Item()
    QUIZ = helper.Item()
