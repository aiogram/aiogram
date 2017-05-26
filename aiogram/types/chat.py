from . import Deserializable


class Chat(Deserializable):
    def __init__(self, id, type, title, username, first_name, last_name, all_members_are_administrators):
        self.id: int = id
        self.type: str = type
        self.title: str = title
        self.username: str = username
        self.first_name: str = first_name
        self.last_name: str = last_name
        self.all_members_are_administrators: bool = all_members_are_administrators

    @classmethod
    def de_json(cls, raw_data) -> 'Chat':
        """
        id	Integer	Unique identifier for this chat. This number may be greater than 32 bits and some programming languages may have difficulty/silent defects in interpreting it. But it is smaller than 52 bits, so a signed 64 bit integer or double-precision float type are safe for storing this identifier.
        type	String	Type of chat, can be either “private”, “group”, “supergroup” or “channel”
        title	String	Optional. Title, for supergroups, channels and group chats
        username	String	Optional. Username, for private chats, supergroups and channels if available
        first_name	String	Optional. First name of the other party in a private chat
        last_name	String	Optional. Last name of the other party in a private chat
        all_members_are_administrators	Boolean	Optional. True if a group has ‘All Members Are Admins’ enabled.
        :param raw_data: 
        :return: 
        """
        raw_data = cls.check_json(raw_data)

        id: int = raw_data.get('id')
        type: str = raw_data.get('type')
        title: str = raw_data.get('title')
        username: str = raw_data.get('username')
        first_name: str = raw_data.get('first_name')
        last_name: str = raw_data.get('last_name')
        all_members_are_administrators: bool = raw_data.get('all_members_are_administrators', False)

        return Chat(id, type, title, username, first_name, last_name, all_members_are_administrators)

    @property
    def full_name(self):
        if self.type == ChatType.PRIVATE:
            full_name = self.first_name
            if self.last_name:
                full_name += ' ' + self.last_name
            return full_name
        return self.title

    @property
    def mention(self):
        if self.username:
            return '@' + self.username
        if self.type == ChatType.PRIVATE:
            return self.full_name
        return None


class ChatType:
    PRIVATE = 'private'
    GROUP = 'group'
    SUPER_GROUP = 'supergroup'
    CHANNEL = 'channel'


class ChatActions:
    TYPING = 'typing'
    UPLOAD_PHOTO = 'upload_photo'
    RECORD_VIDEO = 'record_video'
    UPLOAD_VIDEO = 'upload_video'
    RECORD_AUDIO = 'record_audio'
    UPLOAD_AUDIO = 'upload_audio'
    UPLOAD_DOCUMENT = 'upload_document'
    FIND_LOCATION = 'find_location'
    RECORD_VIDEO_NOTE = 'record_video_note'
    UPLOAD_VIDEO_NOTE = 'upload_video_note'
