from aiogram.client.telegram import PRODUCTION, TelegramAPIServer


class TestAPIServer:
    def test_method_url(self):
        method_url = PRODUCTION.api_url(token="42:TEST", method="apiMethod")
        assert method_url == "https://api.telegram.org/bot42:TEST/apiMethod"

    def test_file_url(self):
        file_url = PRODUCTION.file_url(token="42:TEST", path="path")
        assert file_url == "https://api.telegram.org/file/bot42:TEST/path"

    def test_from_base(self):
        local_server = TelegramAPIServer.from_base("http://localhost:8081", is_local=True)

        method_url = local_server.api_url("42:TEST", method="apiMethod")
        file_url = local_server.file_url(token="42:TEST", path="path")

        assert method_url == "http://localhost:8081/bot42:TEST/apiMethod"
        assert file_url == "http://localhost:8081/file/bot42:TEST/path"
        assert local_server.is_local
