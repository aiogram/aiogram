from textwrap import indent
from typing import Match

from aiogram.methods.base import TelegramMethod, TelegramType
from aiogram.utils.exceptions.base import DetailedTelegramAPIError
from aiogram.utils.exceptions.util import mark_line


class BadRequest(DetailedTelegramAPIError):
    pass


class CantParseEntities(BadRequest):
    pass


class CantParseEntitiesStartTag(CantParseEntities):
    patterns = [
        "Bad Request: can't parse entities: Can't find end tag corresponding to start tag (?P<tag>.+)"
    ]

    def __init__(
        self,
        method: TelegramMethod[TelegramType],
        message: str,
        match: Match[str],
    ) -> None:
        super().__init__(method=method, message=message, match=match)
        self.tag: str = match.group("tag")


class CantParseEntitiesUnmatchedTags(CantParseEntities):
    patterns = [
        r'Bad Request: can\'t parse entities: Unmatched end tag at byte offset (?P<offset>\d), expected "</(?P<expected>\w+)>", found "</(?P<found>\w+)>"'
    ]

    def __init__(
        self,
        method: TelegramMethod[TelegramType],
        message: str,
        match: Match[str],
    ) -> None:
        super().__init__(method=method, message=message, match=match)
        self.offset: int = int(match.group("offset"))
        self.expected: str = match.group("expected")
        self.found: str = match.group("found")


class CantParseEntitiesUnclosed(CantParseEntities):
    patterns = [
        "Bad Request: can't parse entities: Unclosed start tag at byte offset (?P<offset>.+)"
    ]

    def __init__(
        self,
        method: TelegramMethod[TelegramType],
        message: str,
        match: Match[str],
    ) -> None:
        super().__init__(method=method, message=message, match=match)
        self.offset: int = int(match.group("offset"))

    def __str__(self) -> str:
        message = [self.message]
        text = getattr(self.method, "text", None) or getattr(self.method, "caption", None)
        if text:
            message.extend(["Example:", indent(mark_line(text, self.offset), prefix="  ")])
        return "\n".join(message)


class CantParseEntitiesUnsupportedTag(CantParseEntities):
    patterns = [
        r'Bad Request: can\'t parse entities: Unsupported start tag "(?P<tag>.+)" at byte offset (?P<offset>\d+)'
    ]

    def __init__(
        self,
        method: TelegramMethod[TelegramType],
        message: str,
        match: Match[str],
    ) -> None:
        super().__init__(method=method, message=message, match=match)
        self.offset = int(match.group("offset"))
        self.tag = match.group("tag")

    def __str__(self) -> str:
        message = [self.message]
        text = getattr(self.method, "text", None) or getattr(self.method, "caption", None)
        if text:
            message.extend(
                ["Example:", indent(mark_line(text, self.offset, len(self.tag)), prefix="  ")]
            )
        return "\n".join(message)
