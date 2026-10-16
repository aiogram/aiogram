"""
Telegram's text formatting, parsed the way the Bot API parses it.

A bot sends ``<b>Night</b>`` with ``parse_mode="HTML"`` and Telegram
stores ``Night`` with a bold entity; a stray ``<`` fails the send.
The fake used to store the markup as it came, so a test read literal
tags and an escaping bug passed. This module turns marked-up text into
plain text and :class:`~aiogram.types.MessageEntity` objects, offsets
counted in UTF-16 code units as the Bot API counts them.

The parsers are ports of TDLib's, in ``td/telegram/MessageEntity.cpp``
(``parse_html``, ``parse_markdown_v2``, ``parse_markdown``), which the
Bot API server calls through ``parseTextEntities``. Their error texts
are TDLib's own. TDLib prefixes them with ``Can't parse entities:``
(``Td::do_static_request``), and the Bot API server lowercases the
first letter, so a bot reads ``Bad Request: can't parse entities:
Unsupported start tag "x" at byte offset 3``. Links are checked as
``LinkManager::check_link`` and ``get_link_user_id`` check them.

What happens after parsing is narrower than TDLib's
``fix_formatted_text``: ``\\r`` and trailing whitespace are removed,
and entities the Bot API's formatting rules forbid inside ``code``
and ``pre`` are dropped. Leading whitespace stays, and URLs, mentions
or commands are not detected.
"""

from __future__ import annotations

import re
import string
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from aiogram.enums import MessageEntityType
from aiogram.methods import (
    EditEphemeralMessageText,
    EditMessageText,
    SendMessage,
    TelegramMethod,
)
from aiogram.types import MessageEntity, TelegramObject, User

from .errors import ApiRejection

__all__ = ("UserLookup", "apply_parse_modes", "bot_command_entities", "parse_entities")

#: Finds the user a ``tg://user?id=`` link mentions, or ``None``.
UserLookup = Callable[[int], User | None]

#: TDLib's ``is_space``; the end of the text reads as ``\\0``.
_SPACES = frozenset(b" \t\r\n\0\v")

_HTML_TAGS = frozenset(
    {
        "a",
        "b",
        "strong",
        "i",
        "em",
        "s",
        "strike",
        "del",
        "u",
        "ins",
        "tg-spoiler",
        "tg-emoji",
        "tg-time",
        "span",
        "pre",
        "code",
        "blockquote",
    },
)

_HTML_TYPES = {
    "b": "Bold",
    "strong": "Bold",
    "i": "Italic",
    "em": "Italic",
    "s": "Strikethrough",
    "strike": "Strikethrough",
    "del": "Strikethrough",
    "u": "Underline",
    "ins": "Underline",
    "tg-spoiler": "Spoiler",
    "span": "Spoiler",
}

#: TDLib's entity type names, as its errors print them, to the Bot
#: API's.
_BOT_API_TYPES = {
    "Bold": MessageEntityType.BOLD,
    "Italic": MessageEntityType.ITALIC,
    "Underline": MessageEntityType.UNDERLINE,
    "Strikethrough": MessageEntityType.STRIKETHROUGH,
    "Spoiler": MessageEntityType.SPOILER,
    "Code": MessageEntityType.CODE,
    "Pre": MessageEntityType.PRE,
    "PreCode": MessageEntityType.PRE,
    "TextUrl": MessageEntityType.TEXT_LINK,
    "MentionName": MessageEntityType.TEXT_MENTION,
    "CustomEmoji": MessageEntityType.CUSTOM_EMOJI,
    "BlockQuote": MessageEntityType.BLOCKQUOTE,
    "ExpandableBlockQuote": MessageEntityType.EXPANDABLE_BLOCKQUOTE,
    "DateTime": MessageEntityType.DATE_TIME,
}

#: TDLib's ``get_type_priority``: entities at one offset and of one
#: length are ordered by it, lowest first. Date and time is a guess.
_PRIORITY = {
    "BlockQuote": 0,
    "ExpandableBlockQuote": 0,
    "PreCode": 10,
    "Pre": 11,
    "Code": 20,
    "TextUrl": 49,
    "MentionName": 49,
    "DateTime": 50,
    "Bold": 90,
    "Italic": 91,
    "Underline": 92,
    "Strikethrough": 93,
    "Spoiler": 94,
    "CustomEmoji": 99,
}

_CODE_TYPES = frozenset({"Code", "Pre", "PreCode"})

_V2_RESERVED = b"_*[]()~`>#+-=|{}.!"

#: The highest byte a ``\\`` escapes in MarkdownV2.
_LAST_ESCAPABLE = 126
#: The highest code point in the Basic Multilingual Plane, the last
#: one UTF-16 takes a single unit for.
_BMP_LAST = 0xFFFF
#: Where TDLib stops reading a numeric character reference.
_CODE_POINT_LIMIT = 0x10FFFF
#: The longest numeric character reference TDLib reads.
_REFERENCE_LIMIT = 10
_SURROGATES = range(0xD800, 0xE000)
#: UTF-8: a continuation byte is ``10xxxxxx``, a four-byte lead
#: ``11110xxx``.
_CONTINUATION_MASK = 0b1100_0000
_CONTINUATION = 0b1000_0000
_FOUR_BYTE_LEAD = 0b1111_0000
_ASCII_LETTERS = string.ascii_letters.encode()
_ASCII_ALNUM = (string.ascii_letters + string.digits).encode()


@dataclass
class _Entity:
    """An entity as TDLib's parsers build it, in UTF-16 units."""

    type: str
    offset: int
    length: int
    argument: str = ""
    user_id: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class _Text:
    """
    The input as TDLib reads it: UTF-8 bytes, ``\\0`` past the end.

    Byte offsets in errors are into this encoding, as TDLib's are.
    """

    def __init__(self, text: str) -> None:
        self.data = text.encode("utf-8")
        self.size = len(self.data)

    def __getitem__(self, index: int) -> int:
        return self.data[index] if index < self.size else 0

    def slice(self, start: int, end: int) -> str:
        return self.data[start:end].decode("utf-8", errors="replace")


def _utf16_units(byte: int) -> int:
    """UTF-16 units a character starting with ``byte`` takes, or 0."""
    if byte & _CONTINUATION_MASK == _CONTINUATION:
        return 0
    # A four-byte character is a surrogate pair.
    return 2 if byte >= _FOUR_BYTE_LEAD else 1


def _error(message: str) -> ApiRejection:
    return ApiRejection(f"can't parse entities: {message}")


# -- links -------------------------------------------------------------


def _link_user_id(url: str) -> int | None:
    """``LinkManager::get_link_user_id``: ``tg://user?id=N``."""
    rest = url.lower()
    if not rest.startswith("tg:"):
        return None
    rest = rest[3:].removeprefix("//")
    if not rest.startswith("user"):
        return None
    rest = rest[4:].removeprefix("/")
    if not rest.startswith("?"):
        return None
    for parameter in rest[1:].split("#", 1)[0].split("&"):
        key, _, value = parameter.partition("=")
        if key == "id":
            return _int64(value)
    return None


def _int64(value: str) -> int | None:
    """
    TDLib's ``to_integer_safe<int64>``, or None for a malformed one.

    It parses and prints the number back, and anything that does not
    round-trip is no integer: ``--5``, ``+5``, ``05``, ``-0`` and a
    value out of range all fail (tdutils/td/utils/misc.h).
    """
    if _INTEGER.fullmatch(value) is None:
        return None
    number = int(value)
    if str(number) != value or not -(2**63) <= number < 2**63:
        return None
    return number


#: The shape ``to_integer_safe`` reads: an optional minus and digits.
_INTEGER = re.compile(r"-?[0-9]+")


def _check_link(url: str) -> str | None:
    """
    ``LinkManager::check_link``: the URL Telegram stores, or None.

    A link without a scheme is HTTP, and an HTTP link without a path
    gets ``/``, as TDLib's ``HttpUrl::get_url`` renders it. Only
    ``http``, ``https``, ``tg`` and ``ton`` pass, and an HTTP host
    needs a dot. A link that fails is not an error: TDLib drops its
    entity.
    """
    if not url or any(char.isspace() for char in url):
        return None
    lowered = url.lower()
    for scheme in ("tg", "ton"):
        if lowered.startswith(f"{scheme}:"):
            host, tail = _split_host(url[len(scheme) + 1 :].removeprefix("//"))
            if not host or not all(c.isascii() and (c.isalnum() or c in "-_") for c in host):
                return None
            if tail.startswith("/?"):
                tail = tail[1:]
            return f"{scheme}://{host.lower()}{tail}"
    scheme, sep, rest = url.partition("://")
    if not sep:
        scheme, rest = "http", url
    if scheme.lower() not in {"http", "https"}:
        return None
    authority, tail = _split_host(rest)
    host, colon, port = authority.partition(":")
    if "@" in authority or "." not in host or (colon and not port.isdigit()):
        return None
    if not tail.startswith("/"):
        tail = f"/{tail}"
    return f"{scheme.lower()}://{authority.lower()}{tail}"


def _split_host(rest: str) -> tuple[str, str]:
    """Split ``host/path?query`` after the host."""
    for index, char in enumerate(rest):
        if char in "/?#":
            return rest[:index], rest[index:]
    return rest, ""


def _custom_emoji_id(url: str) -> str:
    """``LinkManager::get_link_custom_emoji_id``, raising its errors."""
    rest = url.lower()
    if not rest.startswith("tg:"):
        raise _error("Custom emoji URL must have scheme tg")
    rest = rest[3:].removeprefix("//")
    if not _has_host(rest, "emoji"):
        raise _error('Custom emoji URL must have host "emoji"')
    rest = rest[len("emoji") :].removeprefix("/")
    if not rest.startswith("?"):
        raise _error("Custom emoji URL must have an emoji identifier")
    for parameter in rest[1:].split("#", 1)[0].split("&"):
        key, _, value = parameter.partition("=")
        if key == "id":
            return _emoji_id(value)
    raise _error("Custom emoji URL must have an emoji identifier")


def _emoji_id(value: str) -> str:
    number = _int64(value)
    if not number:
        raise _error("Invalid custom emoji identifier specified")
    return str(number)


def _date_time(unix: str | None, date_format: str | None) -> dict[str, Any]:
    """
    The fields of a date and time entity.

    TDLib's texts for these refusals are not known to the toolkit, so
    these are its own, worded like TDLib's custom emoji ones.
    """
    unix_time = None if unix is None else _int64(unix)
    if unix_time is None or unix_time < 0:
        raise _error("Invalid Unix time specified")
    if date_format and not _valid_date_format(date_format):
        raise _error("Invalid date and time format specified")
    return {"unix_time": unix_time, "date_time_format": date_format or None}


def _valid_date_format(value: str) -> bool:
    """``r|w?[dD]?[tT]?``, the formats the Bot API documents."""
    if value == "r":
        return True
    rest = value.removeprefix("w")
    if rest[:1] in {"d", "D"}:
        rest = rest[1:]
    if rest[:1] in {"t", "T"}:
        rest = rest[1:]
    return rest == ""


def _time_link(url: str) -> dict[str, Any]:
    """``tg://time?unix=N&format=F`` from a MarkdownV2 ``![...]``."""
    query = url.partition("?")[2].split("#", 1)[0]
    values = dict(parameter.partition("=")[::2] for parameter in query.split("&"))
    return _date_time(values.get("unix"), values.get("format"))


def _is_time_link(url: str) -> bool:
    rest = url.lower()
    if not rest.startswith("tg:"):
        return False
    return _has_host(rest[3:].removeprefix("//"), "time")


def _has_host(rest: str, host: str) -> bool:
    """Whether ``rest`` starts with ``host`` as a whole host."""
    return rest.startswith(host) and rest[len(host) : len(host) + 1] in {"", "/", "?", "#"}


def _link_entity(
    offset: int,
    length: int,
    url: str,
) -> _Entity | None:
    """A text link or a mention, or nothing for a bad URL."""
    user_id = _link_user_id(url)
    if user_id is not None:
        return _Entity("MentionName", offset, length, user_id=user_id)
    checked = _check_link(url)
    if checked is None:
        return None
    return _Entity("TextUrl", offset, length, argument=checked)


# -- HTML --------------------------------------------------------------


def _decode_html_entity(text: _Text, pos: int) -> tuple[int, int]:
    """TDLib's ``decode_html_entity``: (code point or 0, next pos)."""
    end = pos + 1
    code = 0
    if text[pos + 1] == ord("#"):
        end += 1
        if text[pos + 2] == ord("x"):
            end += 1
            while text[end] in b"0123456789abcdefABCDEF":
                code = code * 16 + int(chr(text[end]), 16)
                end += 1
                if code >= _CODE_POINT_LIMIT:
                    return 0, pos
        else:
            while text[end] in b"0123456789":
                code = code * 10 + text[end] - ord("0")
                end += 1
                if code >= _CODE_POINT_LIMIT:
                    return 0, pos
        if code == 0 or end - pos >= _REFERENCE_LIMIT or code in _SURROGATES:
            return 0, pos
    else:
        while text[end] in _ASCII_LETTERS:
            end += 1
        name = text.slice(pos + 1, end)
        code = {"lt": 0x3C, "gt": 0x3E, "amp": 0x26, "quot": 0x22}.get(name, 0)
        if not code:
            return 0, pos
    if text[end] == ord(";"):
        end += 1
    return code, end


@dataclass
class _OpenTag:
    name: str
    offset: int
    begin: int
    argument: str = ""
    attributes: dict[str, str] = field(default_factory=dict)


def _parse_html(source: str) -> tuple[bytes, list[_Entity]]:
    text = _Text(source)
    result = bytearray()
    entities: list[_Entity] = []
    offset = 0
    stack: list[_OpenTag] = []
    i = 0
    while i < text.size:
        c = text[i]
        if c == ord("&"):
            code, end = _decode_html_entity(text, i)
            if code:
                offset += 2 if code > _BMP_LAST else 1
                result += chr(code).encode("utf-8")
                i = end
                continue
        if c != ord("<"):
            offset += _utf16_units(c)
            result.append(c)
            i += 1
            continue
        begin = i
        i += 1
        if text[i] != ord("/"):
            i = _html_start_tag(text, begin, i, stack, offset, len(result))
        else:
            i = _html_end_tag(text, begin, i, stack, entities, offset, result)
        i += 1
    if stack:
        msg = f'Can\'t find end tag corresponding to start tag "{stack[-1].name}"'
        raise _error(msg)
    for entity in entities:
        if entity.type == "Code":
            entity.argument = ""
    return bytes(result), entities


def _html_start_tag(
    text: _Text,
    begin: int,
    i: int,
    stack: list[_OpenTag],
    offset: int,
    result_size: int,
) -> int:
    """Read a start tag from ``<`` at ``begin``; return its ``>``."""
    while text[i] not in _SPACES and text[i] != ord(">"):
        i += 1
    if text[i] == 0:
        raise _error(f"Unclosed start tag at byte offset {begin}")
    name = text.slice(begin + 1, i).lower()
    if name not in _HTML_TAGS:
        raise _error(f'Unsupported start tag "{name}" at byte offset {begin}')
    tag = _OpenTag(name, offset, result_size)
    while text[i] != ord(">"):
        while text[i] and text[i] in _SPACES:
            i += 1
        if text[i] == ord(">"):
            break
        attribute_begin = i
        while text[i] not in _SPACES and text[i] not in b"=>":
            i += 1
        attribute = text.slice(attribute_begin, i)
        if not attribute:
            msg = f'Empty attribute name in the tag "{name}" at byte offset {begin}'
            raise _error(msg)
        while text[i] and text[i] in _SPACES:
            i += 1
        if text[i] != ord("="):
            if name == "blockquote" and attribute == "expandable":
                tag.argument = "1"
                continue
            msg = (
                f"Expected equal sign in declaration of an attribute of the tag "
                f'"{name}" at byte offset {begin}'
            )
            raise _error(msg)
        i += 1
        while text[i] and text[i] in _SPACES:
            i += 1
        if text[i] == 0:
            raise _error(f'Unclosed start tag "{name}" at byte offset {begin}')
        value, i = _html_attribute_value(text, i)
        if text[i] == 0:
            raise _error(f"Unclosed start tag at byte offset {begin}")
        _html_attribute(tag, attribute, value)
    if name == "span" and tag.argument != "spoiler":
        msg = f'Tag "span" must have class "tg-spoiler" at byte offset {begin}'
        raise _error(msg)
    stack.append(tag)
    return i


def _html_attribute_value(text: _Text, i: int) -> tuple[str, int]:
    """An attribute value, quoted or a name token, and its end."""
    if text[i] not in b"'\"":
        start = i
        while text[i] and text[i] in _ASCII_ALNUM + b".-":
            i += 1
        if text[i] not in _SPACES and text[i] != ord(">"):
            raise _error(f"Unexpected end of name token at byte offset {start}")
        return text.slice(start, i).lower(), i
    quote = text[i]
    i += 1
    value = bytearray()
    while text[i] != quote and text[i]:
        if text[i] == ord("&"):
            code, end = _decode_html_entity(text, i)
            if code:
                value += chr(code).encode("utf-8")
                i = end
                continue
        value.append(text[i])
        i += 1
    if text[i] == quote:
        i += 1
    return value.decode("utf-8", errors="replace"), i


def _html_attribute(tag: _OpenTag, attribute: str, value: str) -> None:
    """Keep what an attribute means for its tag; ignore the rest."""
    if tag.name == "a" and attribute == "href":
        tag.argument = value
    elif tag.name == "code" and attribute == "class" and value.startswith("language-"):
        tag.argument = value[len("language-") :]
    elif tag.name == "span" and attribute == "class" and value.startswith("tg-"):
        tag.argument = value[len("tg-") :]
    elif tag.name == "tg-emoji" and attribute == "emoji-id":
        tag.argument = value
    elif tag.name == "tg-time" and attribute in {"unix", "format"}:
        tag.attributes[attribute] = value


def _html_end_tag(
    text: _Text,
    begin: int,
    i: int,
    stack: list[_OpenTag],
    entities: list[_Entity],
    offset: int,
    result: bytearray,
) -> int:
    """Read an end tag from ``<`` at ``begin``; return its ``>``."""
    if not stack:
        raise _error(f"Unexpected end tag at byte offset {begin}")
    while text[i] not in _SPACES and text[i] != ord(">"):
        i += 1
    end_name = text.slice(begin + 2, i).lower()
    while text[i] and text[i] in _SPACES:
        i += 1
    if text[i] != ord(">"):
        raise _error(f"Unclosed end tag at byte offset {begin}")
    tag = stack.pop()
    if end_name and end_name != tag.name:
        msg = (
            f'Unmatched end tag at byte offset {begin}, expected "</{tag.name}>", '
            f'found "</{end_name}>"'
        )
        raise _error(msg)
    length = offset - tag.offset
    if length > 0:
        _close_html_tag(tag, length, entities, result)
    return i


def _close_html_tag(
    tag: _OpenTag,
    length: int,
    entities: list[_Entity],
    result: bytearray,
) -> None:
    """Turn a closed tag into its entity, as TDLib does."""
    offset = tag.offset
    previous = entities[-1] if entities else None
    if previous is not None and (previous.offset, previous.length) != (offset, length):
        previous = None
    if tag.name in _HTML_TYPES:
        entities.append(_Entity(_HTML_TYPES[tag.name], offset, length))
    elif tag.name == "tg-emoji":
        entities.append(_Entity("CustomEmoji", offset, length, argument=_emoji_id(tag.argument)))
    elif tag.name == "tg-time":
        extra = _date_time(tag.attributes.get("unix"), tag.attributes.get("format"))
        entities.append(_Entity("DateTime", offset, length, extra=extra))
    elif tag.name == "a":
        url = tag.argument or result[tag.begin :].decode("utf-8", errors="replace")
        entity = _link_entity(offset, length, url)
        if entity is not None:
            entities.append(entity)
    elif tag.name == "pre":
        if previous is not None and previous.type == "Code" and previous.argument:
            previous.type = "PreCode"
        else:
            entities.append(_Entity("Pre", offset, length))
    elif tag.name == "code":
        if previous is not None and previous.type == "Pre" and tag.argument:
            previous.type = "PreCode"
            previous.argument = tag.argument
        else:
            entities.append(_Entity("Code", offset, length, argument=tag.argument))
    else:
        kind = "ExpandableBlockQuote" if tag.argument else "BlockQuote"
        entities.append(_Entity(kind, offset, length))


# -- MarkdownV2 --------------------------------------------------------


@dataclass
class _OpenMark:
    type: str
    offset: int
    byte: int
    begin: int
    argument: str = ""


def _v2_closes(open_type: str, text: _Text, i: int) -> bool:
    """Whether the reserved character at ``i`` ends ``open_type``."""
    c = text[i]
    if open_type == "Bold":
        return c == ord("*")
    if open_type == "Italic":
        return c == ord("_") and text[i + 1] != ord("_")
    if open_type == "Code":
        return c == ord("`")
    if open_type in {"Pre", "PreCode"}:
        return c == text[i + 1] == text[i + 2] == ord("`")
    if open_type in {"TextUrl", "CustomEmoji"}:
        return c == ord("]")
    if open_type == "Underline":
        return c == ord("_") and text[i + 1] == ord("_")
    if open_type == "Strikethrough":
        return c == ord("~")
    return c == ord("|") and text[i + 1] == ord("|")


def _reserved(c: int) -> ApiRejection:
    msg = f"Character '{chr(c)}' is reserved and must be escaped with the preceding '\\'"
    return _error(msg)


def _v2_url(text: _Text, i: int, kind: str) -> tuple[str, int]:
    """Read ``(...)`` from its ``(`` at ``i``; return the ``)``."""
    i += 1
    start = i
    url = bytearray()
    while i < text.size and text[i] != ord(")"):
        if text[i] == ord("\\") and 0 < text[i + 1] <= _LAST_ESCAPABLE:
            url.append(text[i + 1])
            i += 2
            continue
        url.append(text[i])
        i += 1
    if text[i] != ord(")"):
        raise _error(f"Can't find end of {kind} at byte offset {start}")
    return url.decode("utf-8", errors="replace"), i


class _Quote:
    """A ``>`` block quotation of MarkdownV2 being read."""

    def __init__(self) -> None:
        self.start: int | None = None

    def close(self, end: int, entities: list[_Entity], *, expandable: bool) -> None:
        if self.start is None:
            return
        if end > self.start:
            kind = "ExpandableBlockQuote" if expandable else "BlockQuote"
            entities.append(_Entity(kind, self.start, end - self.start))
        self.start = None


def _parse_markdown_v2(source: str) -> tuple[bytes, list[_Entity]]:
    text = _Text(source)
    result = bytearray()
    entities: list[_Entity] = []
    offset = 0
    stack: list[_OpenMark] = []
    quote = _Quote()
    # Where the last ">" was read, so one line takes one.
    marker = -1
    i = 0
    while i < text.size:
        c = text[i]
        in_code = bool(stack) and stack[-1].type in _CODE_TYPES
        # Judged on the output, as TDLib does, so the empty bold of
        # "**>" still lets the ">" start a line.
        line_start = (not result or result[-1] == ord("\n")) and marker != len(result)
        if line_start and not in_code:
            if c == ord(">"):
                marker = len(result)
                if quote.start is None:
                    quote.start = offset
                i += 1
                continue
            # A line that does not start with ">" ends the quote, short
            # of the newline before it.
            quote.close(offset - 1, entities, expandable=False)
        if c == ord("\\") and 0 < text[i + 1] <= _LAST_ESCAPABLE:
            i += 1
            offset += 1
            result.append(text[i])
            i += 1
            continue
        if (
            quote.start is not None
            and not in_code
            and c == text[i + 1] == ord("|")
            and text[i + 2] in b"\n\0"
            and not (stack and stack[-1].type == "Spoiler")
        ):
            quote.close(offset, entities, expandable=True)
            i += 2
            continue
        if c not in (b"`" if in_code else _V2_RESERVED):
            offset += _utf16_units(c)
            result.append(c)
            i += 1
            continue
        if stack and _v2_closes(stack[-1].type, text, i):
            i = _v2_close(text, i, stack.pop(), entities, offset, result)
        else:
            i = _v2_open(text, i, stack, offset, len(result))
        i += 1
    if quote.start is not None:
        end = offset - 1 if result.endswith(b"\n") else offset
        quote.close(end, entities, expandable=False)
    if stack:
        mark = stack[-1]
        raise _error(f"Can't find end of {mark.type} entity at byte offset {mark.byte}")
    return bytes(result), entities


def _read_fence(text: _Text, i: int) -> tuple[int, str]:
    """
    Read what follows an opening fence of three backticks at ``i``.

    Returns where the code starts and its language, if a word right
    after the fence is followed by more than the fence's end. One
    newline after the fence is not part of the code.
    """
    language = ""
    end = i
    while text[end] not in _SPACES and text[end] != ord("`"):
        end += 1
    if end != i and end < text.size and text[end] != ord("`"):
        language = text.slice(i, end)
        i = end
    if text[i] in b"\n\r":
        pair = text[i + 1] in b"\n\r" and text[i] != text[i + 1]
        i += 2 if pair else 1
    return i, language


def _v2_open(
    text: _Text,
    i: int,
    stack: list[_OpenMark],
    offset: int,
    result_size: int,
) -> int:
    """Open the entity a reserved character starts; return its end."""
    c = text[i]
    byte = i
    argument = ""
    if c == ord("_"):
        kind = "Underline" if text[i + 1] == ord("_") else "Italic"
        i += kind == "Underline"
    elif c == ord("*"):
        kind = "Bold"
    elif c == ord("~"):
        kind = "Strikethrough"
    elif c == ord("|") and text[i + 1] == ord("|"):
        kind = "Spoiler"
        i += 1
    elif c == ord("["):
        kind = "TextUrl"
    elif c == ord("!") and text[i + 1] == ord("["):
        kind = "CustomEmoji"
        i += 1
    elif c == ord("`") and text[i + 1] == text[i + 2] == ord("`"):
        i, argument = _read_fence(text, i + 3)
        kind = "PreCode" if argument else "Pre"
        i -= 1
    elif c == ord("`"):
        kind = "Code"
    else:
        raise _reserved(c)
    stack.append(_OpenMark(kind, offset, byte, result_size, argument))
    return i


def _v2_close(
    text: _Text,
    i: int,
    mark: _OpenMark,
    entities: list[_Entity],
    offset: int,
    result: bytearray,
) -> int:
    """Close ``mark`` at ``i``; return where its closing ends."""
    kind = mark.type
    length = offset - mark.offset
    entity: _Entity | None = _Entity(kind, mark.offset, length, argument=mark.argument)
    if kind in {"Underline", "Spoiler"}:
        i += 1
    elif kind in {"Pre", "PreCode"}:
        i += 2
    elif kind == "TextUrl":
        if text[i + 1] == ord("("):
            url, i = _v2_url(text, i + 1, "a URL")
        else:
            url = result[mark.begin :].decode("utf-8", errors="replace")
        entity = _link_entity(mark.offset, length, url)
    elif kind == "CustomEmoji":
        if text[i + 1] != ord("("):
            raise _error("Custom emoji entity must contain a tg://emoji URL")
        url, i = _v2_url(text, i + 1, "a custom emoji URL")
        if _is_time_link(url):
            entity = _Entity("DateTime", mark.offset, length, extra=_time_link(url))
        else:
            entity = _Entity(kind, mark.offset, length, argument=_custom_emoji_id(url))
    if entity is not None and length > 0:
        entities.append(entity)
    return i


# -- Markdown ----------------------------------------------------------


def _parse_markdown(source: str) -> tuple[bytes, list[_Entity]]:
    """The legacy ``Markdown`` mode, TDLib's ``parse_markdown``."""
    text = _Text(source)
    result = bytearray()
    entities: list[_Entity] = []
    offset = 0
    i = 0
    while i < text.size:
        c = text[i]
        if c == ord("\\") and text[i + 1] in b"_*`[":
            i += 1
            result.append(text[i])
            offset += 1
            i += 1
            continue
        if c not in b"_*`[":
            offset += _utf16_units(c)
            result.append(c)
            i += 1
            continue
        begin = i
        end_character = ord("]") if c == ord("[") else c
        i += 1
        is_pre = c == ord("`") and text[i] == text[i + 1] == ord("`")
        language = ""
        if is_pre:
            i, language = _read_fence(text, i + 2)
        start = offset
        while i < text.size and (
            text[i] != end_character or (is_pre and not (text[i + 1] == text[i + 2] == ord("`")))
        ):
            offset += _utf16_units(text[i])
            result.append(text[i])
            i += 1
        if i == text.size:
            msg = f"Can't find end of the entity starting at byte offset {begin}"
            raise _error(msg)
        length = offset - start
        entity: _Entity | None
        if c == ord("["):
            entity, i = _markdown_link(text, begin, i, start, length)
        elif c == ord("`"):
            kind = ("PreCode" if language else "Pre") if is_pre else "Code"
            entity = _Entity(kind, start, length, argument=language)
        else:
            entity = _Entity("Italic" if c == ord("_") else "Bold", start, length)
        if entity is not None and length:
            entities.append(entity)
        if is_pre:
            i += 2
        i += 1
    return bytes(result), entities


def _markdown_link(
    text: _Text,
    begin: int,
    i: int,
    start: int,
    length: int,
) -> tuple[_Entity | None, int]:
    """
    A legacy link closing at the ``]`` at ``i``, and where it ends.

    Its URL is the ``(...)`` after it, or its own text. An empty one
    makes no entity and leaves the ``(...)`` as text, as in TDLib.
    """
    if not length:
        return None, i
    if text[i + 1] != ord("("):
        return _link_entity(start, length, text.slice(begin + 1, i)), i
    close = text.data.find(b")", i + 2)
    close = text.size if close < 0 else close
    return _link_entity(start, length, text.slice(i + 2, close)), close


# -- after parsing -----------------------------------------------------


def _remove_carriage_returns(text: str, entities: list[_Entity]) -> str:
    """Drop ``\\r`` as TDLib's ``clean_input_string`` does."""
    if "\r" not in text:
        return text
    removed: list[int] = []
    units = 0
    for char in text:
        if char == "\r":
            removed.append(units)
        units += 2 if ord(char) > _BMP_LAST else 1

    def moved(position: int) -> int:
        return position - sum(1 for at in removed if at < position)

    for entity in entities:
        end = moved(entity.offset + entity.length)
        entity.offset = moved(entity.offset)
        entity.length = end - entity.offset
    return text.replace("\r", "")


def _trim_end(text: str, entities: list[_Entity]) -> str:
    """
    Drop trailing whitespace, as ``fix_formatted_text`` trims it.

    Only for a parsed text: the toolkit stores a text sent without a
    parse mode as it came.
    """
    trimmed = text.rstrip(" \t\n\v\f")
    if trimmed == text:
        return text
    limit = len(trimmed.encode("utf-16-le")) // 2
    for entity in entities:
        entity.length = min(entity.offset + entity.length, limit) - entity.offset
    return trimmed


def _trim_start(text: str, entities: list[_Entity]) -> str:
    """
    Drop leading spaces and newlines, as ``fix_formatted_text`` does.

    Only before the first entity, which keeps its own whitespace, and
    after the end is trimmed (MessageEntity.cpp). The entities move
    back by what was dropped.
    """
    first = min((entity.offset for entity in entities if entity.length > 0), default=len(text))
    count = 0
    while count < min(first, len(text)) and text[count] in " \n":
        count += 1
    if not count:
        return text
    for entity in entities:
        entity.offset = max(entity.offset - count, 0)
    return text[count:]


def _sorted(entities: list[_Entity]) -> list[_Entity]:
    """TDLib's order, without what may not be nested in code."""
    ordered = sorted(
        (entity for entity in entities if entity.length > 0),
        key=lambda item: (item.offset, -item.length, _PRIORITY[item.type]),
    )
    kept: list[_Entity] = []
    code_end = -1
    for entity in ordered:
        # The Bot API's formatting rules: nothing nests in code or pre.
        if entity.offset + entity.length <= code_end:
            continue
        kept.append(entity)
        if entity.type in _CODE_TYPES:
            code_end = entity.offset + entity.length
    return kept


def _as_message_entity(entity: _Entity, find_user: UserLookup) -> MessageEntity | None:
    values: dict[str, Any] = {
        "type": _BOT_API_TYPES[entity.type],
        "offset": entity.offset,
        "length": entity.length,
    }
    if entity.type == "TextUrl":
        values["url"] = entity.argument
    elif entity.type == "MentionName":
        user = find_user(entity.user_id)  # type: ignore[arg-type]
        if user is None:
            # TDLib skips a mention of a user it cannot reach.
            return None
        values["user"] = user
    elif entity.type == "PreCode":
        values["language"] = entity.argument
    elif entity.type == "CustomEmoji":
        values["custom_emoji_id"] = entity.argument
    values.update(entity.extra)
    return MessageEntity(**values)


_PARSERS = {
    "html": _parse_html,
    "markdownv2": _parse_markdown_v2,
    "markdown": _parse_markdown,
}


def parse_entities(
    text: str,
    parse_mode: str,
    find_user: UserLookup = lambda user_id: None,
) -> tuple[str, list[MessageEntity]]:
    """
    Parse ``text`` in ``parse_mode`` into plain text and entities.

    ``parse_mode`` is ``HTML``, ``MarkdownV2`` or ``Markdown``, in any
    case. ``find_user`` resolves a ``tg://user?id=`` link; a user it
    does not know gets no entity.

    :raises aiogram.test.ApiRejection: with Telegram's description,
        for markup Telegram cannot parse.
    """
    parser = _PARSERS.get(parse_mode.lower())
    if parser is None:
        raise ApiRejection("unsupported parse_mode")
    data, entities = parser(text)
    plain = _remove_carriage_returns(data.decode("utf-8", errors="replace"), entities)
    plain = _trim_start(_trim_end(plain, entities), entities)
    converted = (_as_message_entity(entity, find_user) for entity in _sorted(entities))
    return plain, [entity for entity in converted if entity is not None]


# -- methods -----------------------------------------------------------


def _formatted_fields(model: TelegramObject | TelegramMethod[Any]) -> list[tuple[str, str, str]]:
    """
    Each (parse mode, text, entities) field triple ``model`` has.

    ``parse_mode`` formats ``text``, ``caption`` or ``title``, and an
    ``x_parse_mode`` formats ``x``; the entities are ``x_entities``,
    or ``entities`` for a message's text.
    """
    names = type(model).model_fields
    triples = []
    for name in names:
        if not name.endswith("parse_mode"):
            continue
        if name == "parse_mode":
            candidates = ("text", "message_text", "caption", "title")
            found = [field for field in candidates if field in names]
            if not found:  # pragma: no cover - every such type has one
                continue
            text = found[0]
        else:
            text = name.removesuffix("_parse_mode")
        entities = f"{text}_entities" if f"{text}_entities" in names else "entities"
        triples.append((name, text, entities))
    return triples


# -- bot commands --------------------------------------------------

#: What, besides a word character, may not precede a command's
#: slash or follow the command.
_COMMAND_NEIGHBOURS = "/<>"
#: The longest command and the username lengths TDLib accepts.
_COMMAND_LENGTH = range(1, 65)
_USERNAME_LENGTH = range(3, 33)


def _is_word_character(char: str) -> bool:
    """TDLib's ``is_word_character``: a letter, a number or ``_``."""
    return char == "_" or unicodedata.category(char)[0] in "LN"


def _is_ascii_word(char: str) -> bool:
    """TDLib's ``is_alpha_digit_or_underscore``."""
    return char == "_" or (char.isascii() and char.isalnum())


def _command_ranges(text: str) -> list[tuple[int, int]]:
    """
    The code point ranges of the commands in ``text``.

    As TDLib's ``match_bot_commands`` finds them. A slash starts one
    at the start of the text or after anything but a word character,
    ``/``, ``<`` or ``>``. One to 64 ASCII letters, digits or
    underscores follow, then optionally ``@`` and three to 32 of them
    for the bot. The next character may not be a word character,
    ``/``, ``<`` or ``>``. A command that breaks a rule is no
    command, and neither is the ``/cmd`` before an ``@name`` that
    does.
    """
    found: list[tuple[int, int]] = []
    size = len(text)
    index = 0
    while (index := text.find("/", index)) != -1:
        if index and (
            _is_word_character(text[index - 1]) or text[index - 1] in _COMMAND_NEIGHBOURS
        ):
            index += 1
            continue
        index += 1
        begin = index
        while index < size and _is_ascii_word(text[index]):
            index += 1
        end = index
        if end - begin not in _COMMAND_LENGTH:
            continue
        if index < size and text[index] == "@":
            index += 1
            username = index
            while index < size and _is_ascii_word(text[index]):
                index += 1
            if index - username not in _USERNAME_LENGTH:
                continue
            end = index
        if index < size and (
            _is_word_character(text[index]) or text[index] in _COMMAND_NEIGHBOURS
        ):
            continue
        found.append((begin - 1, end))
    return found


def _utf16_length(text: str) -> int:
    """The length of ``text`` in UTF-16 code units."""
    return sum(2 if ord(char) > _BMP_LAST else 1 for char in text)


def bot_command_entities(text: str | None) -> list[MessageEntity]:
    """
    The ``bot_command`` entities a client attaches to ``text``.

    Telegram finds the commands in a message itself: ``/start``, and
    ``/start@my_bot`` with the bot's username, wherever they stand as
    :func:`_command_ranges` says, not only at the start. Offsets and
    lengths are in UTF-16 code units. Mentions, hashtags and links get
    entities too, which this does not add.
    """
    if not text:
        return []
    found = []
    # A running offset, so a long text is measured once.
    position = units = 0
    for begin, end in _command_ranges(text):
        units += _utf16_length(text[position:begin])
        length = _utf16_length(text[begin:end])
        found.append(
            MessageEntity(type=MessageEntityType.BOT_COMMAND, offset=units, length=length)
        )
        units += length
        position = end
    return found


#: The fields whose text a message cannot do without.
_MESSAGE_TEXT_FIELDS = frozenset({"text", "message_text"})

#: The methods whose ``text`` is a message's whole text.
_TEXT_METHODS = (SendMessage, EditMessageText, EditEphemeralMessageText)


def _blank(text: str) -> bool:
    """
    Whether ``text`` is nothing but whitespace, as TDLib reads it.

    ``clean_input_string`` turns every control character into a space
    and drops ``\r``, and only spaces and newlines are whitespace
    after (MessageEntity.cpp, ``remove_invalid_entities``). TDLib
    refuses a text of zero-width characters too, which is not
    modeled.
    """
    return all(ord(char) <= ord(" ") for char in text)


def refuse_empty_text(method: Any) -> None:
    """
    Refuse a text message whose text is empty or blank.

    An empty one is the Bot API server's ``message text is empty``;
    a blank one TDLib trims to nothing and refuses with ``text must
    be non-empty``. A caption is not refused: TDLib clears it.
    """
    text = method.text if isinstance(method, _TEXT_METHODS) else None
    if text is None:
        # Not a text message, or one carrying other content instead.
        return
    if not text:
        raise ApiRejection("message text is empty")
    if _blank(text):
        raise ApiRejection("text must be non-empty")


def apply_parse_modes(value: Any, find_user: UserLookup) -> Any:
    """
    Apply every parse mode in a call, as the Bot API server does.

    Walks the method and what it carries, such as a media group's
    items or a poll's options, and returns a copy whose texts are
    plain, with their entities and no parse mode. The server's
    ``Client::get_formatted_text`` decides: a parse mode other than
    ``None`` or ``"none"`` on a non-empty text is applied and any
    explicit entities are ignored; otherwise the explicit entities
    stand. ``value`` itself is not changed.
    """
    if isinstance(value, list):
        items = [apply_parse_modes(item, find_user) for item in value]
        changed = any(new is not old for new, old in zip(items, value, strict=True))
        return items if changed else value
    if not isinstance(value, (TelegramObject, TelegramMethod)):
        return value
    changes: dict[str, Any] = {}
    for name in type(value).model_fields:
        current = getattr(value, name, None)
        if isinstance(current, (list, TelegramObject)):
            nested = apply_parse_modes(current, find_user)
            if nested is not current:
                changes[name] = nested
    for mode_field, text_field, entities_field in _formatted_fields(value):
        mode = getattr(value, mode_field, None)
        if mode is None:
            continue
        if isinstance(mode, Enum):
            mode = mode.value
        changes[mode_field] = None
        text = getattr(value, text_field, None)
        if not text or str(mode).lower() in {"", "none"}:
            continue
        plain, entities = parse_entities(text, str(mode), find_user)
        if not plain and text_field in _MESSAGE_TEXT_FIELDS:
            raise ApiRejection("text must be non-empty")
        # A caption that parses to nothing is cleared, as TDLib
        # clears it.
        changes[text_field] = None if not plain and text_field == "caption" else plain
        changes[entities_field] = entities or None
    return value.model_copy(update=changes) if changes else value
