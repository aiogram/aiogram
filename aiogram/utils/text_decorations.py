import html
import re
from dataclasses import dataclass
from struct import unpack
from typing import AnyStr, Callable, Generator, Iterable, List, Optional

from aiogram.api.types import MessageEntity

__all__ = ("TextDecoration", "html", "markdown", "add_surrogates", "remove_surrogates")


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
        if entity.type in ("bold", "italic", "code", "pre", "underline", "strikethrough"):
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
        text = add_surrogates(text)
        result = "".join(self._unparse_entities(text, entities))
        return remove_surrogates(result)

    def _unparse_entities(
        self,
        text: str,
        entities: Iterable[MessageEntity],
        offset: Optional[int] = None,
        length: Optional[int] = None,
    ) -> Generator[str, None, None]:
        offset = offset or 0
        length = length or len(text)

        for index, entity in enumerate(entities or []):
            if entity.offset < offset:
                continue
            if entity.offset > offset:
                yield self.quote(text[offset : entity.offset])
            start = entity.offset
            end = entity.offset + entity.length

            sub_entities = list(
                filter(lambda e: entity.offset <= e.offset < end, entities[index + 1 :])
            )
            yield self.apply_entity(
                entity,
                "".join(self._unparse_entities(text, sub_entities, offset=start, length=end)),
            )
            offset = entity.offset + entity.length

        if offset < length:
            yield self.quote(text[offset:length])


html = TextDecoration(
    link='<a href="{link}">{value}</a>',
    bold="<b>{value}</b>",
    italic="<i>{value}</i>",
    code="<code>{value}</code>",
    pre="<pre>{value}</pre>",
    underline="<u>{value}</u>",
    strikethrough="<s>{value}</s>",
    quote=html.escape,
)

markdown = TextDecoration(
    link="[{value}]({link})",
    bold="*{value}*",
    italic="_{value}_",
    code="`{value}`",
    pre="```{value}```",
    underline="--{value}--",  # Is not supported
    strikethrough="~~{value}~~",  # Is not supported
    quote=lambda text: re.sub(
        pattern=r"([*_`\[])", repl=r"\\\1", string=text
    ),  # Is not always helpful
)  # Markdown is not recommended for usage. Use HTML instead

# Surrogates util was copied form Pyrogram code it under GPL v3 License.
# Source: https://github.com/pyrogram/pyrogram/blob/c5cc85f0076149fc6f3a6fc1d482affb01eeab21/pyrogram/client/parser/utils.py#L19-L37

# SMP = Supplementary Multilingual Plane: https://en.wikipedia.org/wiki/Plane_(Unicode)#Overview
SMP_RE = re.compile(r"[\U00010000-\U0010FFFF]")


def add_surrogates(text):
    # Replace each SMP code point with a surrogate pair
    return SMP_RE.sub(
        lambda match: "".join(  # Split SMP in two surrogates
            chr(i) for i in unpack("<HH", match.group().encode("utf-16le"))
        ),
        text,
    )


def remove_surrogates(text):
    # Replace each surrogate pair with a SMP code point
    return text.encode("utf-16", "surrogatepass").decode("utf-16")
