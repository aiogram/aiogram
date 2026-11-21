from pathlib import Path

import pytest

from aiogram.client.telegram import (
    PRODUCTION,
    TEST,
    BareFilesPathWrapper,
    SimpleFilesPathWrapper,
    TelegramAPIServer,
)


class TestAPIServer:
    def test_method_url(self):
        method_url = PRODUCTION.api_url(token="42:TEST", method="apiMethod")
        assert method_url == "https://api.telegram.org/bot42:TEST/apiMethod"

    @pytest.mark.parametrize("path", ["path", Path("path")])
    def test_file_url(self, path):
        file_url = PRODUCTION.file_url(token="42:TEST", path=path)
        assert file_url == "https://api.telegram.org/file/bot42:TEST/path"

    @pytest.mark.parametrize("path", ["path", Path("path")])
    def test_from_base(self, path):
        local_server = TelegramAPIServer.from_base("http://localhost:8081", is_local=True)

        method_url = local_server.api_url("42:TEST", method="apiMethod")
        file_url = local_server.file_url(token="42:TEST", path=path)

        assert method_url == "http://localhost:8081/bot42:TEST/apiMethod"
        assert file_url == "http://localhost:8081/file/bot42:TEST/path"
        assert local_server.is_local

    @pytest.mark.parametrize(
        ("server", "url", "expected"),
        [
            (
                PRODUCTION,
                "https://api.telegram.org/bot42:TEST/getMe",
                "https://api.telegram.org/bot42:***/getMe",
            ),
            (
                PRODUCTION,
                "https://api.telegram.org/file/bot42:TEST/documents/a.pdf",
                "https://api.telegram.org/file/bot42:***/documents/a.pdf",
            ),
            (
                TEST,
                "https://api.telegram.org/bot42:TEST/test/getMe",
                "https://api.telegram.org/bot42:***/test/getMe",
            ),
            (
                TelegramAPIServer.from_base("http://localhost:8081/", is_local=True),
                "http://localhost:8081/file/bot42:TEST/x",
                "http://localhost:8081/file/bot42:***/x",
            ),
            # No id part: nothing of the token is shown
            (
                PRODUCTION,
                "https://api.telegram.org/botSECRET/getMe",
                "https://api.telegram.org/bot***/getMe",
            ),
            # A foreign URL may carry other secrets: origin only, no credentials
            (
                PRODUCTION,
                "https://u:p@example.com:8443/a?sig=SECRET",
                "https://example.com:8443/...",
            ),
            (PRODUCTION, "not a url", "<invalid URL>"),
        ],
    )
    def test_redact_url(self, server: TelegramAPIServer, url: str, expected: str):
        assert server.redact_url(url) == expected

    def test_redact_url_token_at_template_end(self):
        server = TelegramAPIServer(base="https://h/{method}?t={token}", file="https://h/f/{token}")
        assert server.redact_url("https://h/f/42:TEST") == "https://h/f/42:***"
        # `{method}` before `{token}` does not match the template prefix literally
        assert server.redact_url("https://h/getMe?t=42:TEST") == "https://h/..."


class TestBareFilesPathWrapper:
    def test_to_local(self):
        wrapper = BareFilesPathWrapper()
        assert wrapper.to_local("/path/to/file.dat") == "/path/to/file.dat"

    def test_to_server(self):
        wrapper = BareFilesPathWrapper()
        assert wrapper.to_server("/path/to/file.dat") == "/path/to/file.dat"


class TestSimpleFilesPathWrapper:
    def test_to_local(self):
        wrapper = SimpleFilesPathWrapper(Path("/etc/telegram-bot-api/data"), Path("/opt/app/data"))
        assert wrapper.to_local("/etc/telegram-bot-api/data/documents/file.dat") == Path(
            "/opt/app/data/documents/file.dat"
        )

    def test_to_server(self):
        wrapper = SimpleFilesPathWrapper(Path("/etc/telegram-bot-api/data"), Path("/opt/app/data"))
        assert wrapper.to_server("/opt/app/data/documents/file.dat") == Path(
            "/etc/telegram-bot-api/data/documents/file.dat"
        )
