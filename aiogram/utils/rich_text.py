from __future__ import annotations

import html
from typing import TYPE_CHECKING, Any, cast

from aiogram.utils.text_decorations import (
    HtmlDecoration,
    MarkdownDecoration,
)

if TYPE_CHECKING:
    from aiogram.types import RichMessage

__all__ = (
    "rich_message_to_html",
    "rich_message_to_markdown",
)

MAX_DEPTH = 16


class _HtmlStyle(HtmlDecoration):
    """Rich HTML style.

    Reuses the base :class:`HtmlDecoration` for the tags shared with the classic
    parse mode and adds the tags that are specific to rich messages.
    """

    def marked(self, value: str) -> str:
        return self._tag("mark", value)

    def subscript(self, value: str) -> str:
        return self._tag("sub", value)

    def superscript(self, value: str) -> str:
        return self._tag("sup", value)

    def math(self, value: str) -> str:
        return self._tag("tg-math", value)

    def math_block(self, value: str) -> str:
        return self._tag("tg-math-block", value)

    def pre_language(self, value: str, language: str) -> str:
        return self._tag(
            self.PRE_TAG,
            self._tag(self.CODE_TAG, value, attrs={"class": f"language-{language}"}),
        )

    def anchor(self, name: str) -> str:
        return self._tag("a", "", attrs={"name": name})

    def anchor_link(self, value: str, name: str) -> str:
        return self._tag("a", value, attrs={"href": f"#{name}"})

    def reference(self, value: str, name: str) -> str:
        return self._tag("tg-reference", value, attrs={"name": name})

    def reference_link(self, value: str, name: str) -> str:
        return self._tag("a", value, attrs={"href": f"#{name}"})

    def email(self, value: str, address: str) -> str:
        return self._tag("a", value, attrs={"href": f"mailto:{address}"})

    def phone(self, value: str, number: str) -> str:
        return self._tag("a", value, attrs={"href": f"tel:{number}"})

    def mention(self, value: str, username: str) -> str:
        return self._tag("a", value, attrs={"href": f"https://t.me/{username}"})

    def text_mention(self, value: str, user_id: int) -> str:
        return self.link(value, f"tg://user?id={user_id}")

    def heading(self, value: str, size: int) -> str:
        return self._tag(f"h{size}", value)

    def paragraph(self, value: str) -> str:
        return self._tag("p", value)

    def footer(self, value: str) -> str:
        return self._tag("footer", value)

    def blockquote(self, value: str, credit: str) -> str:  # type: ignore[override]
        cite = self._tag("cite", credit) if credit else ""
        return self._tag("blockquote", f"{value}{cite}")

    def pullquote(self, value: str, credit: str) -> str:
        cite = self._tag("cite", credit) if credit else ""
        return self._tag("aside", f"{value}{cite}")

    def table(self, value: str, *, bordered: bool = False, striped: bool = False) -> str:
        flags: list[str] = []
        if bordered:
            flags.append("bordered")
        if striped:
            flags.append("striped")
        return self._tag("table", value, flags=flags)

    def table_cell(
        self, value: str, *, is_header: bool, align: str, valign: str, colspan: int, rowspan: int
    ) -> str:
        attrs: dict[str, str] = {"align": align, "valign": valign}
        if colspan > 1:
            attrs["colspan"] = str(colspan)
        if rowspan > 1:
            attrs["rowspan"] = str(rowspan)
        return self._tag("th" if is_header else "td", value, attrs=attrs)

    def table_caption(self, value: str) -> str:
        return self._tag("caption", value)

    def list(self, value: str, *, ordered: bool = False) -> str:
        return self._tag("ol" if ordered else "ul", value)

    def list_item(self, value: str, *, value_: int | None = None, type_: str | None = None) -> str:
        attrs: dict[str, str] = {}
        if value_ is not None:
            attrs["value"] = str(value_)
        if type_ is not None:
            attrs["type"] = type_
        return self._tag("li", value, attrs=attrs or None)

    def checkbox_item(self, value: str, checked: bool) -> str:
        input_ = f'<input type="checkbox"{" checked" if checked else ""}>'
        return self._tag("li", f"{input_}{value}")

    def details(self, value: str, summary: str, *, is_open: bool) -> str:
        open_attr = "open" if is_open else None
        return self._tag(
            "details",
            f"<summary>{summary}</summary>{value}",
            flags=[open_attr] if open_attr else None,
        )

    def caption(self, value: str, credit: str) -> str:
        return self._tag("figcaption", f"{value}<cite>{credit}</cite>" if credit else value)

    def thinking(self, value: str) -> str:
        return self._tag("tg-thinking", value)


class _MarkdownStyle(MarkdownDecoration):
    """Rich Markdown style (GitHub-flavored).

    Reuses the base :class:`MarkdownDecoration` for the constructs that are shared
    with the classic parse mode and overrides the inline formatting to use the rich
    markdown syntax.
    """

    def bold(self, value: str) -> str:
        return f"**{value}**"

    def italic(self, value: str) -> str:
        return f"*{value}*"

    def underline(self, value: str) -> str:
        return f"<u>{value}</u>"

    def strikethrough(self, value: str) -> str:
        return f"~~{value}~~"

    def marked(self, value: str) -> str:
        return f"=={value}=="

    def subscript(self, value: str) -> str:
        return f"<sub>{value}</sub>"

    def superscript(self, value: str) -> str:
        return f"<sup>{value}</sup>"

    def math(self, value: str) -> str:
        return f"${value}$"

    def math_block(self, value: str) -> str:
        return f"$${value}$$"

    def custom_emoji(self, value: str, custom_emoji_id: str) -> str:
        return f"![{value}](tg://emoji?id={custom_emoji_id})"

    def anchor(self, name: str) -> str:
        return f'<a name="{name}"></a>'

    def anchor_link(self, value: str, name: str) -> str:
        return f'<a href="#{name}">{value}</a>'

    def reference(self, value: str, name: str) -> str:
        return f"[^{name}]: {value}"

    def reference_link(self, value: str, name: str) -> str:
        return f"{value}[^{name}]"

    def email(self, value: str, address: str) -> str:
        return self.link(value, f"mailto:{address}")

    def phone(self, value: str, number: str) -> str:
        return self.link(value, f"tel:{number}")

    def mention(self, value: str, username: str) -> str:
        return self.link(value, f"https://t.me/{username}")

    def text_mention(self, value: str, user_id: int) -> str:
        return self.link(value, f"tg://user?id={user_id}")

    def heading(self, value: str, size: int) -> str:
        return f"{'#' * size} {value}"

    def paragraph(self, value: str) -> str:
        return value

    def footer(self, value: str) -> str:
        return value

    def blockquote(self, value: str, credit: str) -> str:  # type: ignore[override]
        quoted = "\n".join(f"> {line}" if line else ">" for line in value.splitlines())
        if credit:
            quoted += f"\n> {credit}"
        return quoted

    def pullquote(self, value: str, credit: str) -> str:
        cite = f"<cite>{credit}</cite>" if credit else ""
        return f"<aside>{value}{cite}</aside>"

    def table(self, value: str, *, bordered: bool = False, striped: bool = False) -> str:
        return value

    def list(self, value: str, *, ordered: bool = False) -> str:
        return value

    def list_item(self, value: str, *, value_: int | None = None, type_: str | None = None) -> str:
        return value

    def details(self, value: str, summary: str, *, is_open: bool) -> str:
        open_attr = " open" if is_open else ""
        return f"<details{open_attr}><summary>{summary}</summary>\n\n{value}\n</details>"

    def caption(self, value: str, credit: str) -> str:
        if credit:
            return f"{value}\n> {credit}"
        return value

    def thinking(self, value: str) -> str:
        return value


_html_style = _HtmlStyle()
_markdown_style = _MarkdownStyle()


def _render_text(node: Any, style: _HtmlStyle | _MarkdownStyle, depth: int = 0) -> str:
    if depth > MAX_DEPTH:
        raise ValueError(f"Rich message nesting exceeds the maximum of {MAX_DEPTH} levels")
    if isinstance(node, str):
        return style.quote(node)
    if isinstance(node, list):
        return "".join(_render_text(item, style, depth + 1) for item in node)

    from aiogram.types import (
        RichTextAnchor,
        RichTextAnchorLink,
        RichTextBankCardNumber,
        RichTextBold,
        RichTextBotCommand,
        RichTextCashtag,
        RichTextCode,
        RichTextCustomEmoji,
        RichTextDateTime,
        RichTextEmailAddress,
        RichTextHashtag,
        RichTextItalic,
        RichTextMarked,
        RichTextMathematicalExpression,
        RichTextMention,
        RichTextPhoneNumber,
        RichTextReference,
        RichTextReferenceLink,
        RichTextSpoiler,
        RichTextStrikethrough,
        RichTextSubscript,
        RichTextSuperscript,
        RichTextTextMention,
        RichTextUnderline,
        RichTextUrl,
    )

    if isinstance(node, RichTextBold):
        return style.bold(_render_text(node.text, style, depth + 1))
    if isinstance(node, RichTextItalic):
        return style.italic(_render_text(node.text, style, depth + 1))
    if isinstance(node, RichTextUnderline):
        return style.underline(_render_text(node.text, style, depth + 1))
    if isinstance(node, RichTextStrikethrough):
        return style.strikethrough(_render_text(node.text, style, depth + 1))
    if isinstance(node, RichTextSpoiler):
        return style.spoiler(_render_text(node.text, style, depth + 1))
    if isinstance(node, RichTextMarked):
        return style.marked(_render_text(node.text, style, depth + 1))
    if isinstance(node, RichTextSubscript):
        return style.subscript(_render_text(node.text, style, depth + 1))
    if isinstance(node, RichTextSuperscript):
        return style.superscript(_render_text(node.text, style, depth + 1))
    if isinstance(node, RichTextCode):
        return style.code(_plain_text(node.text))
    if isinstance(node, RichTextCustomEmoji):
        return style.custom_emoji(node.alternative_text, node.custom_emoji_id)
    if isinstance(node, RichTextDateTime):
        return style.date_time(
            _render_text(node.text, style, depth + 1),
            node.unix_time,
            node.date_time_format,
        )
    if isinstance(node, RichTextMathematicalExpression):
        return style.math(node.expression)
    if isinstance(node, RichTextUrl):
        return style.link(_render_text(node.text, style, depth + 1), node.url)
    if isinstance(node, RichTextEmailAddress):
        return style.email(_render_text(node.text, style, depth + 1), node.email_address)
    if isinstance(node, RichTextPhoneNumber):
        return style.phone(_render_text(node.text, style, depth + 1), node.phone_number)
    if isinstance(node, RichTextBankCardNumber):
        return _render_text(node.text, style, depth + 1)
    if isinstance(node, RichTextMention):
        return style.mention(_render_text(node.text, style, depth + 1), node.username)
    if isinstance(node, RichTextHashtag):
        return _render_text(node.text, style, depth + 1)
    if isinstance(node, RichTextCashtag):
        return _render_text(node.text, style, depth + 1)
    if isinstance(node, RichTextBotCommand):
        return _render_text(node.text, style, depth + 1)
    if isinstance(node, RichTextTextMention):
        return style.text_mention(_render_text(node.text, style, depth + 1), node.user.id)
    if isinstance(node, RichTextAnchor):
        return style.anchor(node.name)
    if isinstance(node, RichTextAnchorLink):
        return style.anchor_link(_render_text(node.text, style, depth + 1), node.anchor_name)
    if isinstance(node, RichTextReference):
        return style.reference(_render_text(node.text, style, depth + 1), node.name)
    if isinstance(node, RichTextReferenceLink):
        return style.reference_link(
            _render_text(node.text, style, depth + 1),
            node.reference_name,
        )

    raise TypeError(f"Unsupported rich text node: {type(node).__name__}")


def _plain_text(node: Any) -> str:
    """Extract the plain text from a rich text node, ignoring formatting."""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return "".join(_plain_text(item) for item in node)
    for field in ("text", "alternative_text", "expression"):
        value = getattr(node, field, None)
        if value is not None:
            return _plain_text(value)
    return ""


def _render_caption(caption: Any, style: _HtmlStyle | _MarkdownStyle) -> str:
    if caption is None:
        return ""
    credit = _render_text(caption.credit, style) if caption.credit else ""
    return style.caption(_render_text(caption.text, style), credit)


def _render_media(block: Any, style: _HtmlStyle | _MarkdownStyle) -> str:
    """Media blocks can't be represented in the output because received media
    carry `file_id` objects, not URLs. Only the caption is rendered.
    """
    caption = getattr(block, "caption", None)
    if caption is None:
        return ""
    return _render_caption(caption, style)


def _render_list(block: Any, style: _HtmlStyle | _MarkdownStyle) -> str:
    from aiogram.types import RichBlockListItem

    items: list[Any] = block.items
    ordered = any(
        item.value is not None or item.type is not None
        for item in items
        if isinstance(item, RichBlockListItem)
    )
    has_checkbox = any(item.has_checkbox for item in items if isinstance(item, RichBlockListItem))

    if isinstance(style, _HtmlStyle):
        if has_checkbox:
            rendered = "".join(
                style.checkbox_item(
                    _render_list_item_content(item, style),
                    bool(item.is_checked),
                )
                for item in items
            )
            return style.list(rendered, ordered=False)
        if ordered and items:
            first = items[0]
            attrs: dict[str, str] = {}
            if getattr(first, "value", None) is not None:
                attrs["start"] = str(first.value)
            if getattr(first, "type", None) is not None:
                attrs["type"] = str(first.type)
            attrs_str = "".join(f' {k}="{v}"' for k, v in attrs.items())
            tag = f"<ol{attrs_str}>"
            rendered = "".join(
                style.list_item(
                    _render_list_item_content(item, style),
                    value_=getattr(item, "value", None),
                    type_=getattr(item, "type", None),
                )
                for item in items
            )
            return f"{tag}{rendered}</ol>"
        rendered = "".join(
            style.list_item(_render_list_item_content(item, style)) for item in items
        )
        return style.list(rendered, ordered=False)

    if has_checkbox:
        return "\n".join(
            f"- [{'x' if item.is_checked else ' '}] {_render_list_item_content(item, style)}"
            for item in items
        )
    if ordered:
        lines: list[str] = []
        counter = 1
        for item in items:
            value = getattr(item, "value", None)
            if value is not None:
                counter = value
            lines.append(f"{counter}. {_render_list_item_content(item, style)}")
            counter += 1
        return "\n".join(lines)
    return "\n".join(f"- {_render_list_item_content(item, style)}" for item in items)


def _render_list_item_content(item: Any, style: _HtmlStyle | _MarkdownStyle) -> str:
    content = "\n".join(_render_block(block, style) for block in item.blocks)
    return content.strip()


def _render_table(block: Any, style: _HtmlStyle | _MarkdownStyle) -> str:
    from aiogram.types import RichBlockTableCell

    rows = [[cell for cell in row if isinstance(cell, RichBlockTableCell)] for row in block.cells]

    if isinstance(style, _HtmlStyle):
        rendered_rows = []
        for row in rows:
            rendered_cells = "".join(
                style.table_cell(
                    _render_text(cell.text, style) if cell.text else "",
                    is_header=bool(cell.is_header),
                    align=cell.align,
                    valign=cell.valign,
                    colspan=cell.colspan or 1,
                    rowspan=cell.rowspan or 1,
                )
                for cell in row
            )
            rendered_rows.append(f"<tr>{rendered_cells}</tr>")
        caption = style.table_caption(_render_text(block.caption, style)) if block.caption else ""
        return style.table(
            f"{caption}{''.join(rendered_rows)}",
            bordered=bool(block.is_bordered),
            striped=bool(block.is_striped),
        )

    # Markdown table
    if not rows:
        return ""
    max_columns = max(len(row) for row in rows)
    normalized = [
        row + [RichBlockTableCell(align="left", valign="top")] * (max_columns - len(row))
        for row in rows
    ]
    header_cells = normalized[0]
    body = normalized[1:]

    def render_cell(cell: RichBlockTableCell) -> str:
        text = _render_text(cell.text, style) if cell.text else ""
        return text.replace("|", "\\|")

    align_map = {"left": ":---", "center": ":---:", "right": "---:"}
    header = "| " + " | ".join(render_cell(cell) for cell in header_cells) + " |"
    separator = (
        "| " + " | ".join(align_map.get(cell.align, ":---") for cell in header_cells) + " |"
    )
    lines = [header, separator]
    lines.extend("| " + " | ".join(render_cell(cell) for cell in row) + " |" for row in body)
    if block.caption:
        lines.append(_render_text(block.caption, style))
    return "\n".join(lines)


def _render_block(block: Any, style: _HtmlStyle | _MarkdownStyle, depth: int = 0) -> str:
    if depth > MAX_DEPTH:
        raise ValueError(f"Rich message nesting exceeds the maximum of {MAX_DEPTH} levels")

    from aiogram.types import (
        RichBlockAnchor,
        RichBlockAnimation,
        RichBlockAudio,
        RichBlockBlockQuotation,
        RichBlockCollage,
        RichBlockDetails,
        RichBlockDivider,
        RichBlockFooter,
        RichBlockList,
        RichBlockMap,
        RichBlockMathematicalExpression,
        RichBlockParagraph,
        RichBlockPhoto,
        RichBlockPreformatted,
        RichBlockPullQuotation,
        RichBlockSectionHeading,
        RichBlockSlideshow,
        RichBlockTable,
        RichBlockThinking,
        RichBlockVideo,
        RichBlockVoiceNote,
    )

    if isinstance(block, RichBlockParagraph):
        return style.paragraph(_render_text(block.text, style, depth + 1))
    if isinstance(block, RichBlockSectionHeading):
        return style.heading(_render_text(block.text, style, depth + 1), block.size)
    if isinstance(block, RichBlockPreformatted):
        text = _plain_text(block.text)
        if block.language:
            return style.pre_language(text, block.language)
        return style.pre(text)
    if isinstance(block, RichBlockFooter):
        return style.footer(_render_text(block.text, style, depth + 1))
    if isinstance(block, RichBlockDivider):
        return "<hr/>" if isinstance(style, _HtmlStyle) else "---"
    if isinstance(block, RichBlockMathematicalExpression):
        return style.math_block(block.expression)
    if isinstance(block, RichBlockAnchor):
        return style.anchor(block.name)
    if isinstance(block, RichBlockList):
        return _render_list(block, style)
    if isinstance(block, RichBlockBlockQuotation):
        content = "\n".join(_render_block(inner, style, depth + 1) for inner in block.blocks)
        credit = _render_text(block.credit, style) if block.credit else ""
        return style.blockquote(content, credit)
    if isinstance(block, RichBlockPullQuotation):
        content = _render_text(block.text, style, depth + 1)
        credit = _render_text(block.credit, style) if block.credit else ""
        return style.pullquote(content, credit)
    if isinstance(block, RichBlockCollage):
        content = "".join(_render_block(inner, style, depth + 1) for inner in block.blocks)
        caption = _render_caption(block.caption, style)
        tag = "tg-collage"
        return f"<{tag}>{content}</{tag}>{caption}"
    if isinstance(block, RichBlockSlideshow):
        content = "".join(_render_block(inner, style, depth + 1) for inner in block.blocks)
        caption = _render_caption(block.caption, style)
        tag = "tg-slideshow"
        return f"<{tag}>{content}</{tag}>{caption}"
    if isinstance(block, RichBlockTable):
        return _render_table(block, style)
    if isinstance(block, RichBlockDetails):
        summary = _render_text(block.summary, style, depth + 1)
        content = "\n".join(_render_block(inner, style, depth + 1) for inner in block.blocks)
        return style.details(content, summary, is_open=bool(block.is_open))
    if isinstance(block, RichBlockMap):
        lat = f"{html.escape(str(block.location.latitude), quote=True)}"
        long = f"{html.escape(str(block.location.longitude), quote=True)}"
        caption = _render_caption(block.caption, style)
        map_tag = f'<tg-map lat="{lat}" long="{long}" zoom="{block.zoom}"/>'
        return f"{map_tag}{caption}"
    if isinstance(block, RichBlockThinking):
        return style.thinking(_render_text(block.text, style, depth + 1))
    if isinstance(
        block,
        (RichBlockAnimation, RichBlockAudio, RichBlockPhoto, RichBlockVideo, RichBlockVoiceNote),
    ):
        return _render_media(block, style)

    raise TypeError(f"Unsupported rich block: {type(block).__name__}")


def _render_blocks(blocks: list[Any], style: _HtmlStyle | _MarkdownStyle) -> str:
    rendered = [block for block in (_render_block(b, style) for b in blocks) if block]
    return "\n".join(rendered)


def rich_message_to_html(rich_message: RichMessage) -> str:
    """
    Render a rich message to the Rich HTML style.

    Media blocks are rendered as their captions only, because received media
    objects carry ``file_id`` values instead of URLs.

    :param rich_message: The rich message to render
    :return: Rich HTML representation of the message
    """
    return _render_blocks(cast("list[Any]", rich_message.blocks), _html_style)


def rich_message_to_markdown(rich_message: RichMessage) -> str:
    """
    Render a rich message to the Rich Markdown style.

    Media blocks are rendered as their captions only, because received media
    objects carry ``file_id`` values instead of URLs.

    :param rich_message: The rich message to render
    :return: Rich Markdown representation of the message
    """
    return _render_blocks(cast("list[Any]", rich_message.blocks), _markdown_style)
