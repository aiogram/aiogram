import typing

from . import base
from . import fields


class PollOptions(base.TelegramObject):
    text: base.String = fields.Field()
    voter_count: base.Integer = fields.Field()


class Poll(base.TelegramObject):
    id: base.String = fields.Field()
    question: base.String = fields.Field()
    options: typing.List[PollOptions] = fields.ListField(base=PollOptions)
    is_closed: base.Boolean = fields.Field()
