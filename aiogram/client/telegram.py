from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from yarl import URL


class FilesPathWrapper(ABC):
    @abstractmethod
    def to_local(self, path: Path | str) -> Path | str:
        pass

    @abstractmethod
    def to_server(self, path: Path | str) -> Path | str:
        pass


class BareFilesPathWrapper(FilesPathWrapper):
    def to_local(self, path: Path | str) -> Path | str:
        return path

    def to_server(self, path: Path | str) -> Path | str:
        return path


class SimpleFilesPathWrapper(FilesPathWrapper):
    def __init__(self, server_path: Path, local_path: Path) -> None:
        self.server_path = server_path
        self.local_path = local_path

    @classmethod
    def _resolve(
        cls,
        base1: Path | str,
        base2: Path | str,
        value: Path | str,
    ) -> Path:
        relative = Path(value).relative_to(base1)
        return base2 / relative

    def to_local(self, path: Path | str) -> Path | str:
        return self._resolve(base1=self.server_path, base2=self.local_path, value=path)

    def to_server(self, path: Path | str) -> Path | str:
        return self._resolve(base1=self.local_path, base2=self.server_path, value=path)


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
    """Mark this server is
    in `local mode <https://core.telegram.org/bots/api#using-a-local-bot-api-server>`_."""
    wrap_local_file: FilesPathWrapper = field(default=BareFilesPathWrapper())
    """Callback to wrap files path in local mode"""

    def api_url(self, token: str, method: str) -> str:
        """
        Generate URL for API methods

        :param token: Bot token
        :param method: API method name (case insensitive)
        :return: URL
        """
        return self.base.format(token=token, method=method)

    def file_url(self, token: str, path: str | Path) -> str:
        """
        Generate URL for downloading files

        :param token: Bot token
        :param path: file path
        :return: URL
        """
        return self.file.format(token=token, path=path)

    def redact_url(self, url: str) -> str:
        """
        Render a URL for error messages and logs without the bot token

        A URL built from :attr:`base` or :attr:`file` keeps everything but the token
        secret (``.../bot123456:***/getMe``). Any other URL is shown as its origin only
        (``https://example.com/...``), because its path or query may carry other secrets.

        :param url: URL to render
        :return: URL safe to show
        """
        for template in (self.base, self.file):
            prefix, found, rest = template.partition("{token}")
            if not found or not url.startswith(prefix):
                continue
            # The token runs up to the character that follows `{token}` in the template
            delimiter = rest[:1]
            remainder = url[len(prefix) :]
            token, sep, tail = remainder.partition(delimiter) if delimiter else (remainder, "", "")
            bot_id, colon, _ = token.partition(":")
            return f"{prefix}{bot_id + ':' if colon else ''}***{sep}{tail}"
        try:
            return f"{URL(url).origin()}/..."
        except ValueError:
            return "<invalid URL>"

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


PRODUCTION = TelegramAPIServer(
    base="https://api.telegram.org/bot{token}/{method}",
    file="https://api.telegram.org/file/bot{token}/{path}",
)
TEST = TelegramAPIServer(
    base="https://api.telegram.org/bot{token}/test/{method}",
    file="https://api.telegram.org/file/bot{token}/test/{path}",
)
