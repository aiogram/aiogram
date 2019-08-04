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
