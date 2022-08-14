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

    def __init__(self,
                 is_anonymous: base.Boolean = None,
                 can_manage_chat: base.Boolean = None,
                 can_delete_messages: base.Boolean = None,
                 can_manage_video_chats: base.Boolean = None,
                 can_restrict_members: base.Boolean = None,
                 can_promote_members: base.Boolean = None,
                 can_change_info: base.Boolean = None,
                 can_invite_users: base.Boolean = None,
                 can_post_messages: base.Boolean = None,
                 can_edit_messages: base.Boolean = None,
                 can_pin_messages: base.Boolean = None):
        super(ChatAdministratorRights, self).__init__(
            is_anonymous=is_anonymous,
            can_manage_chat=can_manage_chat,
            can_delete_messages=can_delete_messages,
            can_manage_video_chats=can_manage_video_chats,
            can_restrict_members=can_restrict_members,
            can_promote_members=can_promote_members,
            can_change_info=can_change_info,
            can_invite_users=can_invite_users,
            can_post_messages=can_post_messages,
            can_edit_messages=can_edit_messages,
            can_pin_messages=can_pin_messages)
