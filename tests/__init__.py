import aresponses
from _pytest.monkeypatch import MonkeyPatch
from aiogram.dispatcher import ctx
from aiogram import Bot

TOKEN = '123456789:AABBCCDDEEFFaabbccddeeff-1234567890'


class FakeTelegram(aresponses.ResponsesMockServer):
    def __init__(self, message_dict, bot=None, monkeypatch=None, **kwargs):
        super().__init__(**kwargs)
        self._body, self._headers = self.parse_data(message_dict)

        if isinstance(bot, Bot) and monkeypatch:
            self.monkeypatch = monkeypatch
            self.monkeypatch.setattr(ctx, 'get_bot', lambda: bot)

    async def __aenter__(self):
        await super().__aenter__()
        _response = self.Response(text=self._body, headers=self._headers, status=200, reason='OK')
        self.add(self.ANY, response=_response)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, 'monkeypatch'):
            self.monkeypatch.undo()
        await super().__aexit__(exc_type, exc_val, exc_tb)

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
