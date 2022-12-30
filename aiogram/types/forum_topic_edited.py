import typing

from . import base
from . import fields


class ForumTopicEdited(base.TelegramObject):
    """
    This object represents a service message about an edited forum topic.

    https://core.telegram.org/bots/api#forumtopicedited
    """
    name: typing.Optional[base.String] = fields.Field()
    icon_custom_emoji_id: typing.Optional[base.String] = fields.Field()
