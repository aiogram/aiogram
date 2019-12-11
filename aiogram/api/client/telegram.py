from dataclasses import dataclass


@dataclass
class TelegramAPIServer:
    base: str
    file: str

    def api_url(self, token: str, method: str) -> str:
        return self.base.format(token=token, method=method)

    def file_url(self, token: str, path: str) -> str:
        return self.file.format(token=token, path=path)


PRODUCTION = TelegramAPIServer(
    base="https://api.telegram.org/bot{token}/{method}",
    file="https://api.telegram.org/file/bot{token}/{path}",
)
