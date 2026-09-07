from pathlib import Path

import pytest

from aiogram.client.butagram import (
    PRODUCTION,
    TEST,
    ButagramAPIServer,
    ButagramBot,
)


class TestButagramAPIServer:
    def test_production_url(self):
        method_url = PRODUCTION.api_url(token="42:TEST", method="apiMethod")
        assert method_url == "https://api.butagram.com/bot42:TEST/apiMethod"

    @pytest.mark.parametrize("path", ["path", Path("path")])
    def test_file_url(self, path):
        file_url = PRODUCTION.file_url(token="42:TEST", path=path)
        assert file_url == "https://api.butagram.com/file/bot42:TEST/path"

    def test_test_server(self):
        method_url = TEST.api_url(token="42:TEST", method="apiMethod")
        assert method_url == "https://api.butagram.com/bot42:TEST/test/apiMethod"
        file_url = TEST.file_url(token="42:TEST", path="path")
        assert file_url == "https://api.butagram.com/file/bot42:TEST/test/path"

    @pytest.mark.parametrize("path", ["path", Path("path")])
    def test_from_base(self, path):
        server = ButagramAPIServer.from_base("https://custom.butagram.com")
        method_url = server.api_url("42:TEST", method="apiMethod")
        file_url = server.file_url(token="42:TEST", path=path)

        assert method_url == "https://custom.butagram.com/bot42:TEST/apiMethod"
        assert file_url == "https://custom.butagram.com/file/bot42:TEST/path"


class TestButagramBot:
    def test_default_session(self):
        bot = ButagramBot("42:TEST")
        assert bot.session.api == PRODUCTION
        assert bot.session.api.api_url("42:TEST", "getMe") == "https://api.butagram.com/bot42:TEST/getMe"
