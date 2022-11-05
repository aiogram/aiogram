from . import base
from . import fields


class ForumTopicCreated(base.TelegramObject):
    """
    This object represents a service message about a new forum topic created in the chat.

    https://core.telegram.org/bots/api#forumtopiccreated
    """
    name: base.String = fields.Field()
    icon_color: base.Integer = fields.Field()
    icon_custom_emoji_id: base.String = fields.Field()
