import datetime

from aiogram.types import Deserializable
from aiogram.types.chat import Chat
from aiogram.types.message_entity import MessageEntity
from aiogram.types.user import User


class Message(Deserializable):
    __slots__ = (
        'data', 'message_id', 'from', 'date', 'chat', 'forward_from', 'forward_from_chat', 'forward_from_message_id',
        'forward_date', 'reply_to_message', 'edit_date', 'text', 'entities', 'audio', 'document', 'game', 'photo',
        'sticker', 'video', 'voice', 'video_note', 'new_chat_members', 'caption', 'contact', 'location', 'venue',
        'new_chat_member', 'left_chat_member', 'new_chat_title', 'new_chat_photo', 'delete_chat_photo',
        'group_chat_created', 'supergroup_chat_created', 'channel_chat_created', 'migrate_to_chat_id',
        'migrate_from_chat_id', 'pinned_message', 'invoice', 'successful_payment', 'content_type')

    def __init__(self, data, message_id, from_user, date, chat, forward_from, forward_from_chat,
                 forward_from_message_id, forward_date, reply_to_message, edit_date, text, entities, audio, document,
                 game, photo, sticker, video, voice, video_note, new_chat_members, caption, contact, location, venue,
                 new_chat_member, left_chat_member, new_chat_title, new_chat_photo, delete_chat_photo,
                 group_chat_created, supergroup_chat_created, channel_chat_created, migrate_to_chat_id,
                 migrate_from_chat_id, pinned_message, invoice, successful_payment, content_type):
        self.data = data

        self.message_id: int = message_id
        self.from_user: User = from_user
        self.date: datetime.datetime = date
        self.chat: Chat = chat
        self.forward_from: User = forward_from
        self.forward_from_chat: Chat = forward_from_chat
        self.forward_from_message_id: int = forward_from_message_id
        self.forward_date: datetime.datetime = forward_date
        self.reply_to_message: Message = reply_to_message
        self.edit_date: datetime.datetime = edit_date
        self.text: str = text
        self.entities = entities

        self.audio = audio
        self.document = document
        self.game = game
        self.photo = photo
        self.sticker = sticker
        self.video = video
        self.voice = voice
        self.video_note = video_note
        self.new_chat_members = new_chat_members
        self.caption = caption
        self.contact = contact
        self.location = location
        self.venue = venue
        self.new_chat_member = new_chat_member
        self.left_chat_member = left_chat_member
        self.new_chat_title = new_chat_title
        self.new_chat_photo = new_chat_photo
        self.delete_chat_photo = delete_chat_photo
        self.group_chat_created = group_chat_created
        self.supergroup_chat_created = supergroup_chat_created
        self.channel_chat_created = channel_chat_created
        self.migrate_to_chat_id = migrate_to_chat_id
        self.migrate_from_chat_id = migrate_from_chat_id
        self.pinned_message = pinned_message
        self.invoice = invoice
        self.successful_payment = successful_payment

        self.content_type = content_type

    @classmethod
    def _parse_date(cls, unix_time):
        return datetime.datetime.fromtimestamp(unix_time)

    @classmethod
    def _parse_user(cls, user):
        return User.de_json(user) if user else None

    @classmethod
    def _parse_chat(cls, chat):
        return Chat.de_json(chat) if chat else None

    @classmethod
    def _parse_message(cls, message):
        return Message.de_json(message) if message else None

    @classmethod
    def _parse_entities(cls, entities):
        return [MessageEntity.de_json(entity) for entity in entities] if entities else None

    @classmethod
    def de_json(cls, data):
        data = cls.check_json(data)

        message_id = data.get('message_id')
        from_user = cls._parse_user(data.get('from'))
        date = cls._parse_date(data.get('date', 0))
        chat = cls._parse_chat(data.get('chat', {}))
        forward_from = cls._parse_user(data.get('forward_from', {}))
        forward_from_chat = cls._parse_chat(data.get('forward_from_chat', {}))
        forward_from_message_id = data.get('forward_from_message_id')
        forward_date = cls._parse_date(data.get('forward_date', 0))
        reply_to_message = cls._parse_message(data.get('reply_to_message', {}))
        edit_date = cls._parse_date(data.get('edit_date', 0))
        text = data.get('text')
        entities = cls._parse_entities(data.get('entities'))

        audio = data.get('audio')
        document = data.get('document')
        game = data.get('game')
        photo = data.get('photo')
        sticker = data.get('sticker')
        video = data.get('video')
        voice = data.get('voice')
        video_note = data.get('video_note')
        new_chat_members = data.get('new_chat_members')
        caption = data.get('caption')
        contact = data.get('contact')
        location = data.get('location')
        venue = data.get('venue')
        new_chat_member = data.get('new_chat_member')
        left_chat_member = data.get('left_chat_member')
        new_chat_title = data.get('new_chat_title')
        new_chat_photo = data.get('new_chat_photo')
        delete_chat_photo = data.get('delete_chat_photo')
        group_chat_created = data.get('group_chat_created')
        supergroup_chat_created = data.get('supergroup_chat_created')
        channel_chat_created = data.get('channel_chat_created')
        migrate_to_chat_id = data.get('migrate_to_chat_id')
        migrate_from_chat_id = data.get('migrate_from_chat_id')
        pinned_message = data.get('pinned_message')
        invoice = data.get('invoice')
        successful_payment = data.get('successful_payment')

        if text:
            content_type = ContentType.TEXT
        elif audio:
            content_type = ContentType.AUDIO
        elif document:
            content_type = ContentType.DOCUMENT
        elif game:
            content_type = ContentType.GAME
        elif photo:
            content_type = ContentType.PHOTO
        elif sticker:
            content_type = ContentType.STICKER
        elif video:
            content_type = ContentType.VIDEO
        elif voice:
            content_type = ContentType.VOICE
        elif new_chat_member or new_chat_members:
            content_type = ContentType.NEW_CHAT_MEMBERS
        elif left_chat_member:
            content_type = ContentType.LEFT_CHAT_MEMBER
        elif invoice:
            content_type = ContentType.INVOICE
        elif successful_payment:
            content_type = ContentType.SUCCESSFUL_PAYMENT
        else:
            content_type = ContentType.UNKNOWN

        return Message(data, message_id, from_user, date, chat, forward_from, forward_from_chat,
                       forward_from_message_id, forward_date, reply_to_message, edit_date, text, entities, audio,
                       document, game, photo, sticker, video, voice, video_note, new_chat_members, caption, contact,
                       location, venue, new_chat_member, left_chat_member, new_chat_title, new_chat_photo,
                       delete_chat_photo, group_chat_created, supergroup_chat_created, channel_chat_created,
                       migrate_to_chat_id, migrate_from_chat_id, pinned_message, invoice, successful_payment,
                       content_type)

    def is_command(self):
        return self.text and self.text.startswith('/')


class ContentType:
    TEXT = 'text'
    AUDIO = 'audio'
    DOCUMENT = 'document'
    GAME = 'game'
    PHOTO = 'photo'
    STICKER = 'sticker'
    VIDEO = 'video'
    VOICE = 'voice'
    NEW_CHAT_MEMBERS = 'new_chat_members'
    LEFT_CHAT_MEMBER = 'left_chat_member'
    INVOICE = 'invoice'
    SUCCESSFUL_PAYMENT = 'successful_payment'

    UNKNOWN = 'unknown'


class ParseMode:
    MARKDOWN = 'markdown'
    HTML = 'html'
