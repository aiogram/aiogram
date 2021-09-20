from dataclasses import dataclass
from typing import Any, Protocol


class WrapLocalFileCallbackCallbackProtocol(Protocol):  # pragma: no cover
    def __call__(self, value: str) -> str:
        pass


@dataclass(frozen=True)
class TelegramAPIServer:
    """
    Base config for API Endpoints
    """

    base: str
    """Base URL"""
    file: str
    """Files URL"""
    is_local: bool = False
    """Mark this server is in `local mode <https://core.telegram.org/bots/api#using-a-local-bot-api-server>`_."""
    wrap_local_file: WrapLocalFileCallbackCallbackProtocol = lambda v: v
    """Callback to wrap files path in local mode"""

    def api_url(self, token: str, method: str) -> str:
        """
        Generate URL for API methods

        :param token: Bot token
        :param method: API method name (case insensitive)
        :return: URL
        """
        return self.base.format(token=token, method=method)

    def file_url(self, token: str, path: str) -> str:
        """
        Generate URL for downloading files

        :param token: Bot token
        :param path: file path
        :return: URL
        """
        return self.file.format(token=token, path=path)

    @classmethod
    def from_base(cls, base: str, **kwargs: Any) -> "TelegramAPIServer":
        """
        Use this method to auto-generate TelegramAPIServer instance from base URL

        :param base: Base URL
        :return: instance of :class:`TelegramAPIServer`
        """
        base = base.rstrip("/")
        return cls(
            base=f"{base}/bot{{token}}/{{method}}",
            file=f"{base}/file/bot{{token}}/{{path}}",
            **kwargs,
        )


# Main API server
PRODUCTION = TelegramAPIServer.from_base("https://api.telegram.org")
