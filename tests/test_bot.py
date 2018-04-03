import aresponses
import pytest

from aiogram import Bot, types

TOKEN = '123456789:AABBCCDDEEFFaabbccddeeff-1234567890'


@pytest.yield_fixture()
@pytest.mark.asyncio
async def bot(event_loop):
    """ Bot fixture """
    _bot = Bot(TOKEN, loop=event_loop)
    yield _bot
    await _bot.close()


@pytest.mark.asyncio
async def test_get_bot(bot, event_loop):
    """ GetMe method test """
    _body = '{"ok":true,"result":{"id":492189143,"is_bot":true,' \
            '"first_name":"Dev Tester","username":"MiscDevTesterBot"}}'
    _headers = {'Server': 'nginx/1.12.2',
                'Date': 'Tue, 03 Apr 2018 16:59:54 GMT',
                'Content-Type': 'application/json',
                'Content-Length': str(len(_body)),
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Expose-Headers': 'Content-Length,Content-Type,Date,Server,Connection',
                'Strict-Transport-Security': 'max-age=31536000; includeSubdomains'}
    async with aresponses.ResponsesMockServer(loop=event_loop) as server:
        server.add(server.ANY, response=server.Response(text=_body,
                                                        status=200,
                                                        reason='OK',
                                                        headers=_headers))
        bot_user = await bot.me
        assert isinstance(bot_user, types.User)


@pytest.mark.asyncio
async def test_send_message(bot, event_loop):
    """ SendMessage method test """
    message_text = 'Test message'
    chat_id = -1234567890
    _body = """{"ok":true,"result":{"message_id":74,"from":{"id":492189143,"is_bot":true,"first_name":"Dev Tester",
    "username":"MiscDevTesterBot"},"chat":{"id":66812456,"first_name":"O","username":"Oleg_Oleg_Oleg","type":"private"},
    "date":1522774794,"text":"Test message"}}"""
    _headers = {'Server': 'nginx/1.12.2',
                'Date': 'Tue, 03 Apr 2018 16:59:54 GMT',
                'Content-Type': 'application/json',
                'Content-Length': str(len(_body)),
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Expose-Headers': 'Content-Length,Content-Type,Date,Server,Connection',
                'Strict-Transport-Security': 'max-age=31536000; includeSubdomains'}

    async with aresponses.ResponsesMockServer(loop=event_loop) as server:
        server.add(server.ANY, response=server.Response(text=_body,
                                                        status=200,
                                                        reason='OK',
                                                        headers=_headers))
        msg: types.Message = await bot.send_message(chat_id=chat_id, text=message_text)
        assert msg.text == message_text
