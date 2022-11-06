from . import base
from . import fields


class ForumTopic(base.TelegramObject):
    """
    This object represents a forum topic.

    https://core.telegram.org/bots/api#forumtopic
    """
    message_thread_id: base.Integer = fields.Field()
    name: base.String = fields.Field()
    icon_color: base.Integer = fields.Field()
    icon_custom_emoji_id: base.String = fields.Field()
