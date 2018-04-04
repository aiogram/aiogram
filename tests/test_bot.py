import aresponses
import pytest

from aiogram import Bot, types

TOKEN = '123456789:AABBCCDDEEFFaabbccddeeff-1234567890'


class FakeTelegram(aresponses.ResponsesMockServer):
    def __init__(self, message_dict, **kwargs):
        super().__init__(**kwargs)
        self._body, self._headers = self.parse_data(message_dict)

    async def __aenter__(self):
        await super().__aenter__()
        _response = self.Response(text=self._body, headers=self._headers, status=200, reason='OK')
        self.add(self.ANY, response=_response)

    @staticmethod
    def parse_data(message_dict):
        import json

        _body = '{"ok":true,"result":' + json.dumps(message_dict) + '}'
        _headers = {'Server': 'nginx/1.12.2',
                    'Date': 'Tue, 03 Apr 2018 16:59:54 GMT',
                    'Content-Type': 'application/json',
                    'Content-Length': str(len(_body)),
                    'Connection': 'keep-alive',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                    'Access-Control-Expose-Headers': 'Content-Length,Content-Type,Date,Server,Connection',
                    'Strict-Transport-Security': 'max-age=31536000; includeSubdomains'}
        return _body, _headers


@pytest.yield_fixture()
@pytest.mark.asyncio
async def bot(event_loop):
    """ Bot fixture """
    _bot = Bot(TOKEN, loop=event_loop, parse_mode=types.ParseMode.MARKDOWN)
    yield _bot
    await _bot.close()


@pytest.mark.asyncio
async def test_get_me(bot: Bot, event_loop):
    """ getMe method test """
    from .types.dataset import USER
    user = types.User(**USER)

    async with FakeTelegram(message_dict=USER, loop=event_loop):
        result = await bot.me
        assert result == user


@pytest.mark.asyncio
async def test_send_message(bot: Bot, event_loop):
    """ sendMessage method test """
    from .types.dataset import MESSAGE
    msg = types.Message(**MESSAGE)

    async with FakeTelegram(message_dict=MESSAGE, loop=event_loop):
        result = await bot.send_message(chat_id=msg.chat.id, text=msg.text)
        assert result == msg


@pytest.mark.asyncio
async def test_forward_message(bot: Bot, event_loop):
    """ forwardMessage method test """
    from .types.dataset import FORWARDED_MESSAGE
    msg = types.Message(**FORWARDED_MESSAGE)

    async with FakeTelegram(message_dict=FORWARDED_MESSAGE, loop=event_loop):
        result = await bot.forward_message(chat_id=msg.chat.id, from_chat_id=msg.forward_from_chat.id,
                                           message_id=msg.forward_from_message_id)
        assert result == msg


@pytest.mark.asyncio
async def test_photo_message(bot: Bot, event_loop):
    """ sendPhoto method test """
    from .types.dataset import MESSAGE_WITH_PHOTO, PHOTO
    msg = types.Message(**MESSAGE_WITH_PHOTO)
    photo = types.PhotoSize(**PHOTO)

    async with FakeTelegram(message_dict=MESSAGE_WITH_PHOTO, loop=event_loop):
        result = await bot.send_photo(msg.chat.id, photo=photo.file_id, caption=msg.caption,
                                      parse_mode=types.ParseMode.HTML, disable_notification=False)
        assert result == msg


@pytest.mark.asyncio
async def test_send_audio(bot: Bot, event_loop):
    """ sendAudio method test """
    from .types.dataset import MESSAGE_WITH_AUDIO
    msg = types.Message(**MESSAGE_WITH_AUDIO)

    async with FakeTelegram(message_dict=MESSAGE_WITH_AUDIO, loop=event_loop):
        result = await bot.send_audio(chat_id=msg.chat.id, audio=msg.audio.file_id, caption=msg.caption,
                                      parse_mode=types.ParseMode.HTML, duration=msg.audio.duration,
                                      performer=msg.audio.performer, title=msg.audio.title, disable_notification=False)
        assert result == msg


@pytest.mark.asyncio
async def test_send_document(bot: Bot, event_loop):
    """ sendDocument method test """
    from .types.dataset import MESSAGE_WITH_DOCUMENT
    msg = types.Message(**MESSAGE_WITH_DOCUMENT)

    async with FakeTelegram(message_dict=MESSAGE_WITH_DOCUMENT, loop=event_loop):
        result = await bot.send_document(chat_id=msg.chat.id, document=msg.document.file_id, caption=msg.caption,
                                         parse_mode=types.ParseMode.HTML, disable_notification=False)
        assert result == msg


@pytest.mark.asyncio
async def test_send_video(bot: Bot, event_loop):
    """ sendVideo method test """
    from .types.dataset import MESSAGE_WITH_VIDEO, VIDEO
    msg = types.Message(**MESSAGE_WITH_VIDEO)
    video = types.Video(**VIDEO)

    async with FakeTelegram(message_dict=MESSAGE_WITH_VIDEO, loop=event_loop):
        result = await bot.send_video(chat_id=msg.chat.id, video=video.file_id, duration=video.duration,
                                      width=video.width, height=video.height, caption=msg.caption,
                                      parse_mode=types.ParseMode.HTML, supports_streaming=True,
                                      disable_notification=False)
        assert result == msg
