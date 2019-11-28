from aiogram.api.client.telegram import PRODUCTION


class TestAPIServer:
    def test_method_url(self):
        method_url = PRODUCTION.api_url(token="42:TEST", method="apiMethod")
        assert method_url == "https://api.telegram.org/bot42:TEST/apiMethod"

    def test_file_url(self):
        file_url = PRODUCTION.file_url(token="42:TEST", path="path")
        assert file_url == "https://api.telegram.org/file/bot42:TEST/path"
