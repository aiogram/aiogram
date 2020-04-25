import datetime
import typing

from . import base, fields
from .message_entity import MessageEntity
from .user import User
from ..utils import helper
from ..utils.text_decorations import html_decoration, markdown_decoration


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
    explanation: base.String = fields.Field()
    explanation_entities: base.String = fields.ListField(base=MessageEntity)
    open_period: base.Integer = fields.Field()
    close_date: datetime.datetime = fields.DateTimeField()

    def parse_entities(self, as_html=True):
        text_decorator = html_decoration if as_html else markdown_decoration

        return text_decorator.unparse(self.explanation or '', self.explanation_entities or [])

    @property
    def md_explanation(self) -> str:
        """
        Explanation formatted as markdown.

        :return: str
        """
        return self.parse_entities(False)

    @property
    def html_explanation(self) -> str:
        """
        Explanation formatted as HTML

        :return: str
        """
        return self.parse_entities()


class PollType(helper.Helper):
    mode = helper.HelperMode.snake_case

    REGULAR = helper.Item()
    QUIZ = helper.Item()
