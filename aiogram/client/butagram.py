from dataclasses import dataclass, field
from typing import Any

from aiogram.client.telegram import (
    BareFilesPathWrapper,
    FilesPathWrapper,
    TelegramAPIServer,
)


@dataclass(frozen=True)
class ButagramAPIServer(TelegramAPIServer):
    """
    Base config for Butagram SuperApp Bot API endpoints (by NeonXprime).
    Defaults to https://api.butagram.com
    """

    base: str = "https://api.butagram.com/bot{token}/{method}"
    """Base URL for Butagram Bot API"""
    file: str = "https://api.butagram.com/file/bot{token}/{path}"
    """Files URL for Butagram Bot API"""
    is_local: bool = False
    """Mark if server is in local mode"""
    wrap_local_file: FilesPathWrapper = field(default_factory=BareFilesPathWrapper)

    @classmethod
    def from_base(cls, base: str = "https://api.butagram.com", **kwargs: Any) -> "ButagramAPIServer":
        """
        Auto-generate ButagramAPIServer instance from base URL.
        Defaults to https://api.butagram.com
        """
        base = base.rstrip("/")
        return cls(
            base=f"{base}/bot{{token}}/{{method}}",
            file=f"{base}/file/bot{{token}}/{{path}}",
            **kwargs,
        )


PRODUCTION = ButagramAPIServer(
    base="https://api.butagram.com/bot{token}/{method}",
    file="https://api.butagram.com/file/bot{token}/{path}",
)
TEST = ButagramAPIServer(
    base="https://api.butagram.com/bot{token}/test/{method}",
    file="https://api.butagram.com/file/bot{token}/test/{path}",
)
