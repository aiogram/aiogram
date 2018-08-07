from asyncio import BaseEventLoop

import pytest

from aiogram import Bot, types
from aiogram.dispatcher import ctx
from . import FakeTelegram, TOKEN
from .types import dataset

pytestmark = pytest.mark.asyncio


@pytest.yield_fixture()
async def bot(event_loop):
    """ Bot fixture """
    _bot = Bot(TOKEN, loop=event_loop, parse_mode=types.ParseMode.HTML)
    yield _bot
    await _bot.close()


@pytest.yield_fixture()
async def message(bot, event_loop):
    """
    Message fixture

    :param bot: Telegram bot fixture
    :type bot: Bot
    :param event_loop: asyncio event loop
    :type event_loop: BaseEventLoop
    """
    from .types.dataset import MESSAGE
    msg = types.Message(**MESSAGE)

    async with FakeTelegram(message_dict=MESSAGE, loop=event_loop):
        _message = await bot.send_message(chat_id=msg.chat.id, text=msg.text)

    yield _message


class TestMessageContentType:
    async def test_message_content_type_text(self):
        """ Test message with text content type """
        msg = types.Message(**dataset.MESSAGE)
        assert msg.content_type in types.ContentType.TEXT

    async def test_message_content_type_audio(self):
        """ Test message with audio content type """
        msg = types.Message(**dataset.MESSAGE_WITH_AUDIO)
        assert msg.content_type in types.ContentType.AUDIO

    async def test_message_content_type_animation(self):
        """ Test message with animation content type """
        msg = types.Message(**dataset.MESSAGE_WITH_ANIMATION)
        assert msg.content_type in types.ContentType.ANIMATION

    async def test_message_content_type_document(self):
        """ Test message with document content type """
        msg = types.Message(**dataset.MESSAGE_WITH_DOCUMENT)
        assert msg.content_type in types.ContentType.DOCUMENT

    async def test_message_content_type_game(self):
        """ Test message with game content type """
        msg = types.Message(**dataset.MESSAGE_WITH_GAME)
        assert msg.content_type in types.ContentType.GAME

    async def test_message_content_type_photo(self):
        """ Test message with photo content type """
        msg = types.Message(**dataset.MESSAGE_WITH_PHOTO)
        assert msg.content_type in types.ContentType.PHOTO

    async def test_message_content_type_sticker(self):
        """ Test message with sticker content type """
        msg = types.Message(**dataset.MESSAGE_WITH_STICKER)
        assert msg.content_type in types.ContentType.STICKER

    async def test_message_content_type_video(self):
        """ Test message with video content type """
        msg = types.Message(**dataset.MESSAGE_WITH_VIDEO)
        assert msg.content_type in types.ContentType.VIDEO

    async def test_message_content_type_video_note(self):
        """ Test message with video note content type """
        msg = types.Message(**dataset.MESSAGE_WITH_VIDEO_NOTE)
        assert msg.content_type in types.ContentType.VIDEO_NOTE

    async def test_message_content_type_voice(self):
        """ Test message with voice content type """
        msg = types.Message(**dataset.MESSAGE_WITH_VOICE)
        assert msg.content_type in types.ContentType.VOICE

    async def test_message_content_type_contact(self):
        """ Test message with contact content type """
        msg = types.Message(**dataset.MESSAGE_WITH_CONTACT)
        assert msg.content_type in types.ContentType.CONTACT

    async def test_message_content_type_venue(self):
        """ Test message with venue content type """
        msg = types.Message(**dataset.MESSAGE_WITH_VENUE)
        assert msg.content_type in types.ContentType.VENUE

    async def test_message_content_type_location(self):
        """ Test message with location content type """
        msg = types.Message(**dataset.MESSAGE_WITH_LOCATION)
        assert msg.content_type in types.ContentType.LOCATION

    async def test_message_content_type_new_chat_members(self):
        """ Test message with new chat members content type """
        msg = types.Message(**dataset.MESSAGE_WITH_NEW_CHAT_MEMBERS)
        assert msg.content_type in types.ContentType.NEW_CHAT_MEMBERS

    async def test_message_content_type_left_chat_member(self):
        """ Test message with left chat member content type """
        msg = types.Message(**dataset.MESSAGE_WITH_LEFT_CHAT_MEMBER)
        assert msg.content_type in types.ContentType.LEFT_CHAT_MEMBER

    async def test_message_content_type_invoice(self):
        """ Test message with invoice content type """
        msg = types.Message(**dataset.MESSAGE_WITH_INVOICE)
        assert msg.content_type in types.ContentType.INVOICE

    async def test_message_content_type_successful_payment(self):
        """ Test message with successful payment content type """
        msg = types.Message(**dataset.MESSAGE_WITH_SUCCESSFUL_PAYMENT)
        assert msg.content_type in types.ContentType.SUCCESSFUL_PAYMENT

    @pytest.mark.skipif(not dataset.MESSAGE_WITH_CONNECTED_WEBSITE, reason='No MESSAGE_WITH_CONNECTED_WEBSITE')
    async def test_message_content_type_connected_website(self):
        """ Test message with connected website content type """
        msg = types.Message(**dataset.MESSAGE_WITH_CONNECTED_WEBSITE)
        assert msg.content_type in types.ContentType.CONNECTED_WEBSITE

    async def test_message_content_type_migrate_from_chat_id(self):
        """ Test message with migrate from chat id content type """
        msg = types.Message(**dataset.MESSAGE_WITH_MIGRATE_FROM_CHAT_ID)
        assert msg.content_type in types.ContentType.MIGRATE_FROM_CHAT_ID

    async def test_message_content_type_migrate_to_chat_id(self):
        """ Test message with migrate to chat id content type """
        msg = types.Message(**dataset.MESSAGE_WITH_MIGRATE_TO_CHAT_ID)
        assert msg.content_type in types.ContentType.MIGRATE_TO_CHAT_ID

    async def test_message_content_type_pinned_message(self):
        """ Test message with pin content type """
        msg = types.Message(**dataset.MESSAGE_WITH_PINNED_MESSAGE)
        assert msg.content_type in types.ContentType.PINNED_MESSAGE

    async def test_message_content_type_new_chat_title(self):
        """ Test message with new chat title content type """
        msg = types.Message(**dataset.MESSAGE_WITH_NEW_CHAT_TITLE)
        assert msg.content_type in types.ContentType.NEW_CHAT_TITLE

    async def test_message_content_type_new_chat_photo(self):
        """ Test message with new chat photo content type """
        msg = types.Message(**dataset.MESSAGE_WITH_NEW_CHAT_PHOTO)
        assert msg.content_type in types.ContentType.NEW_CHAT_PHOTO

    @pytest.mark.skipif(not dataset.MESSAGE_WITH_GROUP_CHAT_CREATED, reason='No MESSAGE_WITH_GROUP_CHAT_CREATED')
    async def test_message_content_type_group_chat_created(self):
        """ Test message with group created content type """
        msg = types.Message(**dataset.MESSAGE_WITH_GROUP_CHAT_CREATED)
        assert msg.content_type in types.ContentType.GROUP_CHAT_CREATED

    @pytest.mark.skipif(not dataset.MESSAGE_WITH_PASSPORT_DATA, reason='No MESSAGE_WITH_PASSPORT_DATA')
    async def test_message_content_type_passport_data(self):
        """ Test message with passport data content type """
        msg = types.Message(**dataset.MESSAGE_WITH_PASSPORT_DATA)
        assert msg.content_type in types.ContentType.PASSPORT_DATA

    async def test_message_content_type_unknown(self):
        """ Test message with unknown content type """
        msg = types.Message(**dataset.MESSAGE_UNKNOWN)
        assert msg.content_type in types.ContentType.UNKNOWN

    async def test_message_content_type_delete_chat_photo(self):
        """ Test message with delete chat photo content type """
        msg = types.Message(**dataset.MESSAGE_WITH_DELETE_CHAT_PHOTO)
        assert msg.content_type in types.ContentType.DELETE_CHAT_PHOTO


class TestMessageCommand:
    PURE_COMMAND = 'command'
    COMMAND = f'/{PURE_COMMAND}@TestBot'
    NOT_COMMAND = 'not command'
    ARGS = 'simple text'

    async def test_message_is_command(self):
        msg = types.Message(text=self.COMMAND)
        assert msg.is_command() is True

    async def test_message_is_not_command(self):
        msg = types.Message(text=self.NOT_COMMAND)
        assert msg.is_command() is False

    async def test_message_get_full_command(self):
        msg = types.Message(text=f'{self.COMMAND} {self.ARGS}')
        command, args = msg.get_full_command()
        assert command == self.COMMAND
        assert args == self.ARGS

    async def test_message_get_command(self):
        msg = types.Message(text=f'{self.COMMAND} {self.ARGS}')
        command = msg.get_command()
        assert command == self.COMMAND

    async def test_message_get_command_pure(self):
        msg = types.Message(text=f'{self.COMMAND} {self.ARGS}')
        command = msg.get_command(pure=True)
        assert command == self.PURE_COMMAND

    async def test_message_get_args(self):
        msg = types.Message(text=f'{self.COMMAND} {self.ARGS}')
        args = msg.get_args()
        assert args == self.ARGS


class TestMessageEntities:
    @pytest.mark.skip(reason='Need to add md entities result assertion')
    async def test_message_parse_md_entities(self):
        msg = types.Message(text="""*sample text*""")
        _ = msg.md_text
        # todo add md assertion

    @pytest.mark.skip(reason='Need to add html entities result assertion')
    async def test_message_parse_html_entities(self):
        msg = types.Message(text="""<b>sample text</b>""")
        _ = msg.html_text
        # todo add html assertion


class TestMessageReply:
    async def test_reply(self, message, bot, monkeypatch, event_loop):
        """ Message.reply method test """
        msg = types.Message(**dataset.MESSAGE_WITH_REPLY_TO_MESSAGE)

        async with FakeTelegram(message_dict=dataset.MESSAGE_WITH_REPLY_TO_MESSAGE,
                                loop=event_loop, bot=bot, monkeypatch=monkeypatch):
            result = await message.reply(text=msg.text)

        assert result == msg

    async def test_reply_without_reply(self, message, bot, monkeypatch, event_loop):
        """ Message.reply method test (without reply_to_message) """
        msg = types.Message(**dataset.MESSAGE)

        async with FakeTelegram(message_dict=dataset.MESSAGE,
                                loop=event_loop, bot=bot, monkeypatch=monkeypatch):
            result = await message.reply(text=msg.text, reply=False)

        assert result == msg


class TestMessageReplyPhoto:
    async def test_reply_photo(self, message, bot, monkeypatch, event_loop):
        """ Message.reply_photo method test """
        msg = types.Message(**dataset.MESSAGE_WITH_PHOTO_AND_REPLY)
        async with FakeTelegram(message_dict=dataset.MESSAGE_WITH_PHOTO_AND_REPLY,
                                loop=event_loop, bot=bot, monkeypatch=monkeypatch):
            result = await message.reply_photo(photo=msg.photo[0].file_id, caption=msg.caption)

        assert result == msg

    async def test_reply_photo_without_reply(self, message, bot, monkeypatch, event_loop):
        """ Message.reply_photo method test (without reply_to_message) """
        msg = types.Message(**dataset.MESSAGE_WITH_PHOTO)

        async with FakeTelegram(message_dict=dataset.MESSAGE_WITH_PHOTO,
                                loop=event_loop, bot=bot, monkeypatch=monkeypatch):
            result = await message.reply_photo(photo=msg.photo[0].file_id, caption=msg.caption, reply=False)

        assert result == msg


class TestMessageReplyAudio:
    async def test_reply_audio(self, message, bot, monkeypatch, event_loop):
        """ Message.reply_audio method test """
        msg = types.Message(**dataset.MESSAGE_WITH_AUDIO_AND_REPLY)
        async with FakeTelegram(message_dict=dataset.MESSAGE_WITH_AUDIO_AND_REPLY,
                                loop=event_loop, bot=bot, monkeypatch=monkeypatch):
            result = await message.reply_audio(audio=msg.audio.file_id, caption=msg.caption)

        assert result == msg

    async def test_reply_photo_without_reply(self, message, bot, monkeypatch, event_loop):
        """ Message.reply_audio method test (without reply_to_message) """
        msg = types.Message(**dataset.MESSAGE_WITH_AUDIO)

        async with FakeTelegram(message_dict=dataset.MESSAGE_WITH_AUDIO,
                                loop=event_loop, bot=bot, monkeypatch=monkeypatch):
            result = await message.reply_audio(audio=msg.audio.file_id, caption=msg.caption, reply=False)

        assert result == msg


class TestMessageReplyDocument:
    async def test_reply_document(self, message, bot, monkeypatch, event_loop):
        """ Message.reply_document method test """
        msg = types.Message(**dataset.MESSAGE_WITH_DOCUMENT_AND_REPLY)
        async with FakeTelegram(message_dict=dataset.MESSAGE_WITH_DOCUMENT_AND_REPLY,
                                loop=event_loop, bot=bot, monkeypatch=monkeypatch):
            result = await message.reply_document(document=msg.document.file_id, caption=msg.caption)

        assert result == msg

    async def test_reply_document_without_reply(self, message, bot, monkeypatch, event_loop):
        """ Message.reply_document method test (without reply_to_message) """
        msg = types.Message(**dataset.MESSAGE_WITH_DOCUMENT)

        async with FakeTelegram(message_dict=dataset.MESSAGE_WITH_DOCUMENT,
                                loop=event_loop, bot=bot, monkeypatch=monkeypatch):
            result = await message.reply_document(document=msg.document.file_id, caption=msg.caption, reply=False)

        assert result == msg


class TestMessageReplyVideo:
    async def test_reply_video(self, message, bot, monkeypatch, event_loop):
        """ Message.reply_video method test """
        msg = types.Message(**dataset.MESSAGE_WITH_VIDEO_AND_REPLY)
        async with FakeTelegram(message_dict=dataset.MESSAGE_WITH_VIDEO_AND_REPLY,
                                loop=event_loop, bot=bot, monkeypatch=monkeypatch):
            result = await message.reply_video(video=msg.video.file_id, caption=msg.caption)

        assert result == msg

    async def test_reply_video_without_reply(self, message, bot, monkeypatch, event_loop):
        """ Message.reply_video method test (without reply_to_message) """
        msg = types.Message(**dataset.MESSAGE_WITH_VIDEO)

        async with FakeTelegram(message_dict=dataset.MESSAGE_WITH_VIDEO,
                                loop=event_loop, bot=bot, monkeypatch=monkeypatch):
            result = await message.reply_video(video=msg.video.file_id, caption=msg.caption, reply=False)

        assert result == msg


class TestMessageReplyVoice:
    async def test_reply_voice(self, message, bot, monkeypatch, event_loop):
        """ Message.reply_voice method test """
        msg = types.Message(**dataset.MESSAGE_WITH_VOICE_AND_REPLY)
        async with FakeTelegram(message_dict=dataset.MESSAGE_WITH_VOICE_AND_REPLY,
                                loop=event_loop, bot=bot, monkeypatch=monkeypatch):
            result = await message.reply_voice(voice=msg.voice.file_id, caption=msg.caption)

        assert result == msg

    async def test_reply_voice_without_reply(self, message, bot, monkeypatch, event_loop):
        """ Message.reply_voice method test (without reply_to_message) """
        msg = types.Message(**dataset.MESSAGE_WITH_VOICE)

        async with FakeTelegram(message_dict=dataset.MESSAGE_WITH_VOICE,
                                loop=event_loop, bot=bot, monkeypatch=monkeypatch):
            result = await message.reply_voice(voice=msg.voice.file_id, caption=msg.caption, reply=False)

        assert result == msg


class TestMessageVideoNote:
    async def test_reply_video_note(self, message, bot, monkeypatch, event_loop):
        """ Message.reply_video_note method test """
        msg = types.Message(**dataset.MESSAGE_WITH_VIDEO_NOTE_AND_REPLY)
        async with FakeTelegram(message_dict=dataset.MESSAGE_WITH_VIDEO_NOTE_AND_REPLY,
                                loop=event_loop, bot=bot, monkeypatch=monkeypatch):
            vn = msg.video_note
            result = await message.reply_video_note(video_note=vn.file_id, duration=vn.duration, length=vn.length)

        assert result == msg

    async def test_reply_video_note_without_reply(self, message, bot, monkeypatch, event_loop):
        """ Message.reply_video_note method test (without reply_to_message) """
        msg = types.Message(**dataset.MESSAGE_WITH_VIDEO_NOTE)

        async with FakeTelegram(message_dict=dataset.MESSAGE_WITH_VIDEO_NOTE,
                                loop=event_loop, bot=bot, monkeypatch=monkeypatch):
            vn = msg.video_note
            result = await message.reply_video_note(video_note=vn.file_id, duration=vn.duration,
                                                    length=vn.length, reply=False)

        assert result == msg


class TestMessageMediaGroup:
    async def test_reply_media_group(self, message, bot, monkeypatch, event_loop):
        """ Message.reply_media_group method test """
        msg = types.Message(**dataset.MESSAGE_WITH_MEDIA_GROUP_AND_REPLY)
        photo = types.InputMediaPhoto
        async with FakeTelegram(message_dict=dataset.MESSAGE_WITH_MEDIA_GROUP_AND_REPLY,
                                loop=event_loop, bot=bot, monkeypatch=monkeypatch):
            result = await message.reply_media_group(media=types.MediaGroup())

        assert result == msg

    async def test_reply_video_note_without_reply(self, message, bot, monkeypatch, event_loop):
        """ Message.reply_media_group method test (without reply_to_message) """
        msg = types.Message(**dataset.MESSAGE_WITH_MEDIA_GROUP)

        async with FakeTelegram(message_dict=dataset.MESSAGE_WITH_MEDIA_GROUP,
                                loop=event_loop, bot=bot, monkeypatch=monkeypatch):
            result = await message.reply_media_group(media=types.MediaGroup(), reply=False)

        assert result == msg
