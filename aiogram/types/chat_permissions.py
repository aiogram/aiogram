from . import base
from . import fields


class ChatPermissions(base.TelegramObject):
    """
    Describes actions that a non-administrator user is allowed to take in a chat.

    https://core.telegram.org/bots/api#chatpermissions
    """
    can_send_messages: base.Boolean = fields.Field()
    can_send_media_messages: base.Boolean = fields.Field()
    can_send_polls: base.Boolean = fields.Field()
    can_send_other_messages: base.Boolean = fields.Field()
    can_add_web_page_previews: base.Boolean = fields.Field()
    can_change_info: base.Boolean = fields.Field()
    can_invite_users: base.Boolean = fields.Field()
    can_pin_messages: base.Boolean = fields.Field()
    can_manage_topics: base.Boolean = fields.Field()

    def __init__(self,
                 can_send_messages: base.Boolean = None,
                 can_send_media_messages: base.Boolean = None,
                 can_send_polls: base.Boolean = None,
                 can_send_other_messages: base.Boolean = None,
                 can_add_web_page_previews: base.Boolean = None,
                 can_change_info: base.Boolean = None,
                 can_invite_users: base.Boolean = None,
                 can_pin_messages: base.Boolean = None,
                 can_manage_topics: base.Boolean = None,
                 **kwargs):
        super(ChatPermissions, self).__init__(
            can_send_messages=can_send_messages,
            can_send_media_messages=can_send_media_messages,
            can_send_polls=can_send_polls,
            can_send_other_messages=can_send_other_messages,
            can_add_web_page_previews=can_add_web_page_previews,
            can_change_info=can_change_info,
            can_invite_users=can_invite_users,
            can_pin_messages=can_pin_messages,
            can_manage_topics=can_manage_topics,
        )
