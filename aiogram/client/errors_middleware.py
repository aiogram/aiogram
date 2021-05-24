from __future__ import annotations

import re
from typing import TYPE_CHECKING, List, Type

from aiogram.methods import Response, TelegramMethod
from aiogram.types import TelegramObject
from aiogram.utils.exceptions.base import TelegramAPIError
from aiogram.utils.exceptions.exceptions import (
    CantParseEntitiesStartTag,
    CantParseEntitiesUnclosed,
    CantParseEntitiesUnmatchedTags,
    CantParseEntitiesUnsupportedTag,
    DetailedTelegramAPIError,
)

if TYPE_CHECKING:
    from aiogram.client.bot import Bot
    from aiogram.client.session.base import NextRequestMiddlewareType


class RequestErrorMiddleware:
    def __init__(self) -> None:
        self._registry: List[Type[DetailedTelegramAPIError]] = [
            CantParseEntitiesStartTag,
            CantParseEntitiesUnmatchedTags,
            CantParseEntitiesUnclosed,
            CantParseEntitiesUnsupportedTag,
        ]

    def mount(self, error: Type[DetailedTelegramAPIError]) -> Type[DetailedTelegramAPIError]:
        if error in self:
            raise ValueError(f"{error!r} is already registered")
        if not hasattr(error, "patterns"):
            raise ValueError(f"{error!r} has no attribute 'patterns'")
        self._registry.append(error)
        return error

    def detect_error(self, err: TelegramAPIError) -> TelegramAPIError:
        message = err.message
        for variant in self._registry:
            for pattern in variant.patterns:
                if match := re.match(pattern, message):
                    return variant(
                        method=err.method,
                        message=err.message,
                        match=match,
                    )
        return err

    def __contains__(self, item: Type[DetailedTelegramAPIError]) -> bool:
        return item in self._registry

    async def __call__(
        self,
        bot: Bot,
        method: TelegramMethod[TelegramObject],
        make_request: NextRequestMiddlewareType,
    ) -> Response[TelegramObject]:
        try:
            return await make_request(bot, method)
        except TelegramAPIError as e:
            detected_err = self.detect_error(err=e)
            raise detected_err from e
