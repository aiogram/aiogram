from .base import Deserializable


class Chat(Deserializable):
    """
    This object represents a chat.

    https://core.telegram.org/bots/api#chat
    """

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
        """
        Get mention if dialog have username or full name if this is Private dialog otherwise None
        """
        if self.username:
            return '@' + self.username
        if self.type == ChatType.PRIVATE:
            return self.full_name
        return None


class ChatType:
    """
    List of chat types
    
    :key: PRIVATE
    :key: GROUP
    :key: SUPER_GROUP
    :key: CHANNEL
    """

    PRIVATE = 'private'
    GROUP = 'group'
    SUPER_GROUP = 'supergroup'
    CHANNEL = 'channel'


class ChatActions:
    """
    List of chat actions
    
    :key: TYPING 
    :key: UPLOAD_PHOTO 
    :key: RECORD_VIDEO 
    :key: UPLOAD_VIDEO 
    :key: RECORD_AUDIO 
    :key: UPLOAD_AUDIO 
    :key: UPLOAD_DOCUMENT 
    :key: FIND_LOCATION 
    :key: RECORD_VIDEO_NOTE 
    :key: UPLOAD_VIDEO_NOTE 
    """

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
