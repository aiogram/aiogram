import datetime

from .base import Deserializable
from .user import User


class ChatMember(Deserializable):
    """
    This object contains information about one member of the chat.
    
    https://core.telegram.org/bots/api#chatmember
    """

    def __init__(self, user, status, until_date, can_be_edited, can_change_info, can_post_messages,
                 can_edit_messages, can_delete_messages, can_invite_users, can_restrict_members,
                 can_pin_messages, can_promote_members, can_send_messages, can_send_media_messages,
                 can_send_other_messages, can_add_web_page_previews
                 ):
        self.user: User = user
        self.status: str = status

        self.until_date: datetime.datetime = until_date
        self.can_be_edited: bool = can_be_edited
        self.can_change_info: bool = can_change_info
        self.can_post_messages: bool = can_post_messages
        self.can_edit_messages: bool = can_edit_messages
        self.can_delete_messages: bool = can_delete_messages
        self.can_invite_users: bool = can_invite_users
        self.can_restrict_members: bool = can_restrict_members
        self.can_pin_messages: bool = can_pin_messages
        self.can_promote_members: bool = can_promote_members
        self.can_send_messages: bool = can_send_messages
        self.can_send_media_messages: bool = can_send_media_messages
        self.can_send_other_messages: bool = can_send_other_messages
        self.can_add_web_page_previews: bool = can_add_web_page_previews

    @classmethod
    def _parse_date(cls, unix_time):
        return datetime.datetime.fromtimestamp(unix_time)

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        user = User.deserialize(raw_data.get('user'))
        status = raw_data.get('status')

        until_date = cls._parse_date(raw_data.get('until_date'))
        can_be_edited = raw_data.get('can_be_edited')
        can_change_info = raw_data.get('can_change_info')
        can_post_messages = raw_data.get('can_post_messages')
        can_edit_messages = raw_data.get('can_edit_messages')
        can_delete_messages = raw_data.get('can_delete_messages')
        can_invite_users = raw_data.get('can_invite_users')
        can_restrict_members = raw_data.get('can_restrict_members')
        can_pin_messages = raw_data.get('can_pin_messages')
        can_promote_members = raw_data.get('can_promote_members')
        can_send_messages = raw_data.get('can_send_messages')
        can_send_media_messages = raw_data.get('can_send_media_messages')
        can_send_other_messages = raw_data.get('can_send_other_messages')
        can_add_web_page_previews = raw_data.get('can_add_web_page_previews')

        return ChatMember(user, status, until_date, can_be_edited, can_change_info, can_post_messages,
                          can_edit_messages, can_delete_messages, can_invite_users, can_restrict_members,
                          can_pin_messages, can_promote_members, can_send_messages, can_send_media_messages,
                          can_send_other_messages, can_add_web_page_previews
                          )


class ChatMemberStatus:
    CREATOR = 'creator'
    ADMINISTRATOR = 'administrator'
    MEMBER = 'member'
    LEFT = 'left'
    KICKED = 'kicked'

    @classmethod
    def is_admin(cls, role):
        return role in [cls.ADMINISTRATOR, cls.CREATOR]

    @classmethod
    def is_member(cls, role):
        return role in [cls.MEMBER, cls.ADMINISTRATOR, cls.CREATOR]
