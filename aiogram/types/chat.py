from .base import Deserializable
from .chat_photo import ChatPhoto


class Chat(Deserializable):
    """
    This object represents a chat.

    https://core.telegram.org/bots/api#chat
    """

    def __init__(self, id, type, title, username, first_name, last_name, all_members_are_administrators, photo,
                 description, invite_link):
        self.id: int = id
        self.type: str = type
        self.title: str = title
        self.username: str = username
        self.first_name: str = first_name
        self.last_name: str = last_name
        self.all_members_are_administrators: bool = all_members_are_administrators
        self.photo: ChatPhoto = photo
        self.description: str = description
        self.invite_link: str = invite_link

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
        photo = raw_data.get('photo')
        description = raw_data.get('description')
        invite_link = raw_data.get('invite_link')

        return Chat(id, type, title, username, first_name, last_name, all_members_are_administrators, photo,
                    description, invite_link)

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

    async def set_photo(self, photo):
        return await self.bot.set_chat_photo(self.id, photo)

    async def delete_photo(self):
        return await self.bot.delete_chat_photo(self.id)

    async def set_title(self, title):
        return await self.bot.set_chat_title(self.id, title)

    async def set_description(self, description):
        return await self.bot.delete_chat_description(self.id, description)

    async def pin_message(self, message_id: int, disable_notification: bool = False):
        return await self.bot.pin_chat_message(self.id, message_id, disable_notification)

    async def unpin_message(self):
        return await self.bot.unpin_chat_message(self.id)

    async def leave(self):
        return await self.bot.leave_chat(self.id)

    async def get_administrators(self):
        return await self.bot.get_chat_administrators(self.id)

    async def get_members_count(self):
        return await self.bot.get_chat_members_count(self.id)

    async def get_member(self, user_id):
        return await self.bot.get_chat_member(self.id, user_id)

    async def do(self, action):
        return await self.bot.send_chat_action(self.id, action)


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
