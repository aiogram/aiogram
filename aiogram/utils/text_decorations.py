from __future__ import annotations

import html
import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generator, List, Optional, Pattern, cast

from aiogram.enums import MessageEntityType

if TYPE_CHECKING:
    from aiogram.types import MessageEntity

__all__ = (
    "HtmlDecoration",
    "MarkdownDecoration",
    "TextDecoration",
    "html_decoration",
    "markdown_decoration",
    "add_surrogates",
    "remove_surrogates",
)


def add_surrogates(text: str) -> bytes:
    return text.encode("utf-16-le")


def remove_surrogates(text: bytes) -> str:
    return text.decode("utf-16-le")


class TextDecoration(ABC):
    def apply_entity(self, entity: MessageEntity, text: str) -> str:
        """
        Apply single entity to text

        :param entity:
        :param text:
        :return:
        """
        if entity.type in {
            MessageEntityType.BOT_COMMAND,
            MessageEntityType.URL,
            MessageEntityType.MENTION,
            MessageEntityType.PHONE_NUMBER,
            MessageEntityType.HASHTAG,
            MessageEntityType.CASHTAG,
            MessageEntityType.EMAIL,
        }:
            # These entities should not be changed
            return text
        if entity.type in {
            MessageEntityType.BOLD,
            MessageEntityType.ITALIC,
            MessageEntityType.CODE,
            MessageEntityType.UNDERLINE,
            MessageEntityType.STRIKETHROUGH,
            MessageEntityType.SPOILER,
        }:
            return cast(str, getattr(self, entity.type)(value=text))
        if entity.type == MessageEntityType.PRE:
            return (
                self.pre_language(value=text, language=entity.language)
                if entity.language
                else self.pre(value=text)
            )
        if entity.type == MessageEntityType.TEXT_MENTION:
            from aiogram.types import User

            user = cast(User, entity.user)
            return self.link(value=text, link=f"tg://user?id={user.id}")
        if entity.type == MessageEntityType.TEXT_LINK:
            return self.link(value=text, link=cast(str, entity.url))
        if entity.type == MessageEntityType.CUSTOM_EMOJI:
            return self.custom_emoji(value=text, custom_emoji_id=cast(str, entity.custom_emoji_id))

        # This case is not possible because of `if` above, but if any new entity is added to
        # API it will be here too
        return self.quote(text)

    def unparse(self, text: str, entities: Optional[List[MessageEntity]] = None) -> str:
        """
        Unparse message entities

        :param text: raw text
        :param entities: Array of MessageEntities
        :return:
        """
        return "".join(
            self._unparse_entities(
                add_surrogates(text),
                sorted(entities, key=lambda item: item.offset) if entities else [],
            )
        )

    def _unparse_entities(
        self,
        text: bytes,
        entities: List[MessageEntity],
        offset: Optional[int] = None,
        length: Optional[int] = None,
    ) -> Generator[str, None, None]:
        if offset is None:
            offset = 0
        length = length or len(text)

        for index, entity in enumerate(entities):
            if entity.offset * 2 < offset:
                continue
            if entity.offset * 2 > offset:
                yield self.quote(remove_surrogates(text[offset : entity.offset * 2]))
            start = entity.offset * 2
            offset = entity.offset * 2 + entity.length * 2

            sub_entities = list(
                filter(lambda e: e.offset * 2 < (offset or 0), entities[index + 1 :])
            )
            yield self.apply_entity(
                entity,
                "".join(self._unparse_entities(text, sub_entities, offset=start, length=offset)),
            )

        if offset < length:
            yield self.quote(remove_surrogates(text[offset:length]))

    @abstractmethod
    def link(self, value: str, link: str) -> str:
        pass

    @abstractmethod
    def bold(self, value: str) -> str:
        pass

    @abstractmethod
    def italic(self, value: str) -> str:
        pass

    @abstractmethod
    def code(self, value: str) -> str:
        pass

    @abstractmethod
    def pre(self, value: str) -> str:
        pass

    @abstractmethod
    def pre_language(self, value: str, language: str) -> str:
        pass

    @abstractmethod
    def underline(self, value: str) -> str:
        pass

    @abstractmethod
    def strikethrough(self, value: str) -> str:
        pass

    @abstractmethod
    def spoiler(self, value: str) -> str:
        pass

    @abstractmethod
    def quote(self, value: str) -> str:
        pass

    @abstractmethod
    def custom_emoji(self, value: str, custom_emoji_id: str) -> str:
        pass


class HtmlDecoration(TextDecoration):
    BOLD_TAG = "b"
    ITALIC_TAG = "i"
    UNDERLINE_TAG = "u"
    STRIKETHROUGH_TAG = "s"
    SPOILER_TAG = "tg-spoiler"
    EMOJI_TAG = "tg-emoji"

    def link(self, value: str, link: str) -> str:
        return f'<a href="{link}">{value}</a>'

    def bold(self, value: str) -> str:
        return f"<{self.BOLD_TAG}>{value}</{self.BOLD_TAG}>"

    def italic(self, value: str) -> str:
        return f"<{self.ITALIC_TAG}>{value}</{self.ITALIC_TAG}>"

    def code(self, value: str) -> str:
        return f"<code>{value}</code>"

    def pre(self, value: str) -> str:
        return f"<pre>{value}</pre>"

    def pre_language(self, value: str, language: str) -> str:
        return f'<pre><code class="language-{language}">{value}</code></pre>'

    def underline(self, value: str) -> str:
        return f"<{self.UNDERLINE_TAG}>{value}</{self.UNDERLINE_TAG}>"

    def strikethrough(self, value: str) -> str:
        return f"<{self.STRIKETHROUGH_TAG}>{value}</{self.STRIKETHROUGH_TAG}>"

    def spoiler(self, value: str) -> str:
        return f"<{self.SPOILER_TAG}>{value}</{self.SPOILER_TAG}>"

    def quote(self, value: str) -> str:
        return html.escape(value, quote=False)

    def custom_emoji(self, value: str, custom_emoji_id: str) -> str:
        return f'<{self.EMOJI_TAG} emoji-id="{custom_emoji_id}">{value}</tg-emoji>'


class MarkdownDecoration(TextDecoration):
    MARKDOWN_QUOTE_PATTERN: Pattern[str] = re.compile(r"([_*\[\]()~`>#+\-=|{}.!\\])")

    def link(self, value: str, link: str) -> str:
        return f"[{value}]({link})"

    def bold(self, value: str) -> str:
        return f"*{value}*"

    def italic(self, value: str) -> str:
        return f"_\r{value}_\r"

    def code(self, value: str) -> str:
        return f"`{value}`"

    def pre(self, value: str) -> str:
        return f"```\n{value}\n```"

    def pre_language(self, value: str, language: str) -> str:
        return f"```{language}\n{value}\n```"

    def underline(self, value: str) -> str:
        return f"__\r{value}__\r"

    def strikethrough(self, value: str) -> str:
        return f"~{value}~"

    def spoiler(self, value: str) -> str:
        return f"||{value}||"

    def quote(self, value: str) -> str:
        return re.sub(pattern=self.MARKDOWN_QUOTE_PATTERN, repl=r"\\\1", string=value)

    def custom_emoji(self, value: str, custom_emoji_id: str) -> str:
        return self.link(value=value, link=f"tg://emoji?id={custom_emoji_id}")


html_decoration = HtmlDecoration()
markdown_decoration = MarkdownDecoration()
