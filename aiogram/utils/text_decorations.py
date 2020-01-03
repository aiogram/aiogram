from __future__ import annotations
import html
import re
import struct
from dataclasses import dataclass
from typing import TYPE_CHECKING, AnyStr, Callable, Generator, Iterable, List, Optional

if TYPE_CHECKING:
    from aiogram.types import MessageEntity

__all__ = (
    "TextDecoration",
    "html_decoration",
    "markdown_decoration",
    "add_surrogate",
    "remove_surrogate",
)


@dataclass
class TextDecoration:
    link: str
    bold: str
    italic: str
    code: str
    pre: str
    underline: str
    strikethrough: str
    quote: Callable[[AnyStr], AnyStr]

    def apply_entity(self, entity: MessageEntity, text: str) -> str:
        """
        Apply single entity to text

        :param entity:
        :param text:
        :return:
        """
        if entity.type in (
            "bold",
            "italic",
            "code",
            "pre",
            "underline",
            "strikethrough",
        ):
            return getattr(self, entity.type).format(value=text)
        elif entity.type == "text_mention":
            return self.link.format(value=text, link=f"tg://user?id={entity.user.id}")
        elif entity.type == "text_link":
            return self.link.format(value=text, link=entity.url)
        elif entity.type == "url":
            return text
        return self.quote(text)

    def unparse(self, text, entities: Optional[List[MessageEntity]] = None) -> str:
        """
        Unparse message entities

        :param text: raw text
        :param entities: Array of MessageEntities
        :return:
        """
        text = add_surrogate(text)
        result = "".join(
            self._unparse_entities(
                text, sorted(entities, key=lambda item: item.offset) if entities else []
            )
        )
        return remove_surrogate(result)

    def _unparse_entities(
        self,
        text: str,
        entities: Iterable[MessageEntity],
        offset: Optional[int] = None,
        length: Optional[int] = None,
    ) -> Generator[str, None, None]:
        offset = offset or 0
        length = length or len(text)

        for index, entity in enumerate(entities):
            if entity.offset < offset:
                continue
            if entity.offset > offset:
                yield self.quote(text[offset : entity.offset])
            start = entity.offset
            offset = entity.offset + entity.length

            sub_entities = list(
                filter(lambda e: e.offset < offset, entities[index + 1 :])
            )
            yield self.apply_entity(
                entity,
                "".join(
                    self._unparse_entities(
                        text, sub_entities, offset=start, length=offset
                    )
                ),
            )

        if offset < length:
            yield self.quote(text[offset:length])


html_decoration = TextDecoration(
    link='<a href="{link}">{value}</a>',
    bold="<b>{value}</b>",
    italic="<i>{value}</i>",
    code="<code>{value}</code>",
    pre="<pre>{value}</pre>",
    underline="<u>{value}</u>",
    strikethrough="<s>{value}</s>",
    quote=html.escape,
)

MARKDOWN_QUOTE_PATTERN = re.compile(r"([_*\[\]()~`>#+\-=|{}.!])")

markdown_decoration = TextDecoration(
    link="[{value}]({link})",
    bold="*{value}*",
    italic="_{value}_\r",
    code="`{value}`",
    pre="```{value}```",
    underline="__{value}__",
    strikethrough="~{value}~",
    quote=lambda text: re.sub(
        pattern=MARKDOWN_QUOTE_PATTERN, repl=r"\\\1", string=text
    ),
)


def add_surrogate(text: str) -> str:
    return "".join(
        "".join(chr(d) for d in struct.unpack("<HH", s.encode("utf-16-le")))
        if (0x10000 <= ord(s) <= 0x10FFFF)
        else s
        for s in text
    )


def remove_surrogate(text: str) -> str:
    return text.encode("utf-16", "surrogatepass").decode("utf-16")
