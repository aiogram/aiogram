import asyncio

from . import base
from . import fields
from .chat_photo import ChatPhoto
from ..utils import helper
from ..utils import markdown


class Chat(base.TelegramObject):
    """
    This object represents a chat.

    https://core.telegram.org/bots/api#chat
    """
    id: base.Integer = fields.Field()
    type: base.String = fields.Field()
    title: base.String = fields.Field()
    username: base.String = fields.Field()
    first_name: base.String = fields.Field()
    last_name: base.String = fields.Field()
    all_members_are_administrators: base.Boolean = fields.Field()
    photo: ChatPhoto = fields.Field(base=ChatPhoto)
    description: base.String = fields.Field()
    invite_link: base.String = fields.Field()
    pinned_message: 'Message' = fields.Field(base='Message')
    sticker_set_name: base.String = fields.Field()
    can_set_sticker_set: base.Boolean = fields.Field()

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

    @property
    def user_url(self):
        if self.type != ChatType.PRIVATE:
            raise TypeError('This property available only in private chats.')

        return f"tg://user?id={self.id}"

    def get_mention(self, name=None, as_html=False):
        if name is None:
            name = self.mention
        if as_html:
            return markdown.hlink(name, self.user_url)
        return markdown.link(name, self.user_url)

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

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return other.id == self.id
        return self.id == other

    def __int__(self):
        return self.id


class ChatType(helper.Helper):
    """
    List of chat types

    :key: PRIVATE
    :key: GROUP
    :key: SUPER_GROUP
    :key: CHANNEL
    """

    mode = helper.HelperMode.lowercase

    PRIVATE = helper.Item()  # private
    GROUP = helper.Item()  # group
    SUPER_GROUP = helper.Item()  # supergroup
    CHANNEL = helper.Item()  # channel

    @staticmethod
    def _check(obj, chat_types) -> bool:
        if not hasattr(obj, 'chat'):
            return False
        return obj.chat.type in chat_types

    @classmethod
    def is_private(cls, obj) -> bool:
        """
        Check chat is private

        :param obj:
        :return:
        """
        return cls._check(obj, [cls.PRIVATE])

    @classmethod
    def is_group(cls, obj) -> bool:
        """
        Check chat is group

        :param obj:
        :return:
        """
        return cls._check(obj, [cls.GROUP])

    @classmethod
    def is_super_group(cls, obj) -> bool:
        """
        Check chat is super-group

        :param obj:
        :return:
        """
        return cls._check(obj, [cls.SUPER_GROUP])

    @classmethod
    def is_group_or_super_group(cls, obj) -> bool:
        """
        Check chat is group or super-group

        :param obj:
        :return:
        """
        return cls._check(obj, [cls.GROUP, cls.SUPER_GROUP])

    @classmethod
    def is_channel(cls, obj) -> bool:
        """
        Check chat is channel

        :param obj:
        :return:
        """
        return cls._check(obj, [cls.CHANNEL])


class ChatActions(helper.Helper):
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

    mode = helper.HelperMode.snake_case

    TYPING: str = helper.Item()  # typing
    UPLOAD_PHOTO: str = helper.Item()  # upload_photo
    RECORD_VIDEO: str = helper.Item()  # record_video
    UPLOAD_VIDEO: str = helper.Item()  # upload_video
    RECORD_AUDIO: str = helper.Item()  # record_audio
    UPLOAD_AUDIO: str = helper.Item()  # upload_audio
    UPLOAD_DOCUMENT: str = helper.Item()  # upload_document
    FIND_LOCATION: str = helper.Item()  # find_location
    RECORD_VIDEO_NOTE: str = helper.Item()  # record_video_note
    UPLOAD_VIDEO_NOTE: str = helper.Item()  # upload_video_note

    @classmethod
    async def _do(cls, action: str, sleep=None):
        from aiogram.dispatcher.ctx import get_bot, get_chat
        await get_bot().send_chat_action(get_chat(), action)
        if sleep:
            await asyncio.sleep(sleep)

    @classmethod
    def calc_timeout(cls, text, timeout=.8):
        """
        Calculate timeout for text

        :param text:
        :param timeout:
        :return:
        """
        return min((len(str(text)) * timeout, 5.0))

    @classmethod
    async def typing(cls, sleep=None):
        """
        Do typing

        :param sleep: sleep timeout
        :return:
        """
        if isinstance(sleep, str):
            sleep = cls.calc_timeout(sleep)
        await cls._do(cls.TYPING, sleep)

    @classmethod
    async def upload_photo(cls, sleep=None):
        """
        Do upload_photo

        :param sleep: sleep timeout
        :return:
        """
        await cls._do(cls.UPLOAD_PHOTO, sleep)

    @classmethod
    async def record_video(cls, sleep=None):
        """
        Do record video

        :param sleep: sleep timeout
        :return:
        """
        await cls._do(cls.UPLOAD_PHOTO, sleep)

    @classmethod
    async def upload_video(cls, sleep=None):
        """
        Do upload video

        :param sleep: sleep timeout
        :return:
        """
        await cls._do(cls.RECORD_VIDEO, sleep)

    @classmethod
    async def record_audio(cls, sleep=None):
        """
        Do record audio

        :param sleep: sleep timeout
        :return:
        """
        await cls._do(cls.UPLOAD_VIDEO, sleep)

    @classmethod
    async def upload_audio(cls, sleep=None):
        """
        Do upload audio

        :param sleep: sleep timeout
        :return:
        """
        await cls._do(cls.RECORD_AUDIO, sleep)

    @classmethod
    async def upload_document(cls, sleep=None):
        """
        Do upload document

        :param sleep: sleep timeout
        :return:
        """
        await cls._do(cls.UPLOAD_AUDIO, sleep)

    @classmethod
    async def find_location(cls, sleep=None):
        """
        Do find location

        :param sleep: sleep timeout
        :return:
        """
        await cls._do(cls.UPLOAD_DOCUMENT, sleep)

    @classmethod
    async def record_video_note(cls, sleep=None):
        """
        Do record video note

        :param sleep: sleep timeout
        :return:
        """
        await cls._do(cls.FIND_LOCATION, sleep)

    @classmethod
    async def upload_video_note(cls, sleep=None):
        """
        Do upload video note

        :param sleep: sleep timeout
        :return:
        """
        await cls._do(cls.RECORD_VIDEO_NOTE, sleep)
