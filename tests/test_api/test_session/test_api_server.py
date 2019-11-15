from aiogram.api.session.base import PRODUCTION


class TestAPIServer:
    def test_method_url(self):
        method_url = PRODUCTION.api_url(token="TOKEN", method="apiMethod")
        assert method_url == "https://api.telegram.org/botTOKEN/apiMethod"

    def test_file_url(self):
        file_url = PRODUCTION.file_url(token="TOKEN", path="path")
        assert file_url == "https://api.telegram.org/file/botTOKEN/path"
