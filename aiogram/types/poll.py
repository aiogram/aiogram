import typing

from . import base
from . import fields


class PollOption(base.TelegramObject):
    text: base.String = fields.Field()
    voter_count: base.Integer = fields.Field()


class Poll(base.TelegramObject):
    id: base.String = fields.Field()
    question: base.String = fields.Field()
    options: typing.List[PollOption] = fields.ListField(base=PollOption)
    is_closed: base.Boolean = fields.Field()
