from __future__ import annotations

import html
import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generator, List, Optional, Pattern, cast

if TYPE_CHECKING:  # pragma: no cover
    from aiogram.types import MessageEntity

__all__ = (
    "TextDecoration",
    "HtmlDecoration",
    "MarkdownDecoration",
    "html_decoration",
    "markdown_decoration",
)


class TextDecoration(ABC):
    def apply_entity(self, entity: MessageEntity, text: str) -> str:
        """
        Apply single entity to text

        :param entity:
        :param text:
        :return:
        """
        if entity.type in {"bot_command", "url", "mention", "phone_number"}:
            # This entities should not be changed
            return text
        if entity.type in {"bold", "italic", "code", "underline", "strikethrough"}:
            return cast(str, getattr(self, entity.type)(value=text))
        if entity.type == "pre":
            return (
                self.pre_language(value=text, language=entity.language)
                if entity.language
                else self.pre(value=text)
            )
        if entity.type == "text_mention":
            from aiogram.types import User

            user = cast(User, entity.user)
            return self.link(value=text, link=f"tg://user?id={user.id}")
        if entity.type == "text_link":
            return self.link(value=text, link=cast(str, entity.url))

        return self.quote(text)

    def unparse(self, text: str, entities: Optional[List[MessageEntity]] = None) -> str:
        """
        Unparse message entities

        :param text: raw text
        :param entities: Array of MessageEntities
        :return:
        """
        result = "".join(
            self._unparse_entities(
                text, sorted(entities, key=lambda item: item.offset) if entities else []
            )
        )
        return result

    def _unparse_entities(
        self,
        text: str,
        entities: List[MessageEntity],
        offset: Optional[int] = None,
        length: Optional[int] = None,
    ) -> Generator[str, None, None]:
        if offset is None:
            offset = 0
        length = length or len(text)

        for index, entity in enumerate(entities):
            if entity.offset < offset:
                continue
            if entity.offset > offset:
                yield self.quote(text[offset : entity.offset])
            start = entity.offset
            offset = entity.offset + entity.length

            sub_entities = list(
                filter(lambda e: e.offset < (offset or 0), entities[index + 1 :])
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

    @abstractmethod
    def link(self, value: str, link: str) -> str:  # pragma: no cover
        pass

    @abstractmethod
    def bold(self, value: str) -> str:  # pragma: no cover
        pass

    @abstractmethod
    def italic(self, value: str) -> str:  # pragma: no cover
        pass

    @abstractmethod
    def code(self, value: str) -> str:  # pragma: no cover
        pass

    @abstractmethod
    def pre(self, value: str) -> str:  # pragma: no cover
        pass

    @abstractmethod
    def pre_language(self, value: str, language: str) -> str:  # pragma: no cover
        pass

    @abstractmethod
    def underline(self, value: str) -> str:  # pragma: no cover
        pass

    @abstractmethod
    def strikethrough(self, value: str) -> str:  # pragma: no cover
        pass

    @abstractmethod
    def quote(self, value: str) -> str:  # pragma: no cover
        pass


class HtmlDecoration(TextDecoration):
    def link(self, value: str, link: str) -> str:
        return f'<a href="{link}">{value}</a>'

    def bold(self, value: str) -> str:
        return f"<b>{value}</b>"

    def italic(self, value: str) -> str:
        return f"<i>{value}</i>"

    def code(self, value: str) -> str:
        return f"<code>{value}</code>"

    def pre(self, value: str) -> str:
        return f"<pre>{value}</pre>"

    def pre_language(self, value: str, language: str) -> str:
        return f'<pre><code class="language-{language}">{value}</code></pre>'

    def underline(self, value: str) -> str:
        return f"<u>{value}</u>"

    def strikethrough(self, value: str) -> str:
        return f"<s>{value}</s>"

    def quote(self, value: str) -> str:
        return html.escape(value)


class MarkdownDecoration(TextDecoration):
    MARKDOWN_QUOTE_PATTERN: Pattern[str] = re.compile(r"([_*\[\]()~`>#+\-|{}.!])")

    def link(self, value: str, link: str) -> str:
        return f"[{value}]({link})"

    def bold(self, value: str) -> str:
        return f"*{value}*"

    def italic(self, value: str) -> str:
        return f"_{value}_\r"

    def code(self, value: str) -> str:
        return f"`{value}`"

    def pre(self, value: str) -> str:
        return f"```{value}```"

    def pre_language(self, value: str, language: str) -> str:
        return f"```{language}\n{value}\n```"

    def underline(self, value: str) -> str:
        return f"__{value}__"

    def strikethrough(self, value: str) -> str:
        return f"~{value}~"

    def quote(self, value: str) -> str:
        return re.sub(pattern=self.MARKDOWN_QUOTE_PATTERN, repl=r"\\\1", string=value)


html_decoration = HtmlDecoration()
markdown_decoration = MarkdownDecoration()
