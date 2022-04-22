from . import base
from . import fields


class ChatAdministratorRights(base.TelegramObject):
    """
    Represents rights of an administrator in a chat.

    Source: https://core.telegram.org/bots/api#chatadministratorrights
    """
    is_anonymous: base.Boolean = fields.Field()
    can_manage_chat: base.Boolean = fields.Field()
    can_delete_messages: base.Boolean = fields.Field()
    can_manage_video_chats: base.Boolean = fields.Field()
    can_restrict_members: base.Boolean = fields.Field()
    can_promote_members: base.Boolean = fields.Field()
    can_change_info: base.Boolean = fields.Field()
    can_invite_users: base.Boolean = fields.Field()
    can_post_messages: base.Boolean = fields.Field()
    can_edit_messages: base.Boolean = fields.Field()
    can_pin_messages: base.Boolean = fields.Field()
