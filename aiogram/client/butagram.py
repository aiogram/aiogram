from dataclasses import dataclass, field
from typing import Any

from aiogram.client.bot import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.session.base import BaseSession
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


class ButagramBot(Bot):
    """
    Native Bot class for Butagram SuperApp (by NeonXprime).
    Connects to https://api.butagram.com automatically without any session boilerplate.
    """

    def __init__(
        self,
        token: str,
        session: BaseSession | None = None,
        default: DefaultBotProperties | None = None,
        **kwargs: Any,
    ) -> None:
        if session is None:
            session = AiohttpSession(api=PRODUCTION)
        super().__init__(token=token, session=session, default=default, **kwargs)
