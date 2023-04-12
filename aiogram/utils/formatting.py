"""
Proof of Concept text decoration utility for aiogram 3.0

This part of the code is licensed under MIT as the same as aiogarm

Soon it will be moved into main package

Usage:

>>> formatting = Text("Hello, ", Bold("World"), "!")
>>> await bot.send_message(chat_id=..., **formatting.to_kwargs())
"""
from typing import (
    Any,
    ClassVar,
    Dict,
    Generator,
    Iterator,
    List,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

from aiogram.enums import MessageEntityType
from aiogram.types import MessageEntity, User
from aiogram.utils.text_decorations import (
    add_surrogates,
    html_decoration,
    markdown_decoration,
    remove_surrogates,
)

NodeType = Union[str, "Node"]

NodeT = TypeVar("NodeT", bound=NodeType)


def sizeof(value: str) -> int:
    return len(value.encode("utf-16-le")) // 2


class Node:
    type: ClassVar[Optional[str]] = None

    __slots__ = ("_body", "_params")

    def __init__(
        self,
        *body: NodeType,
        **params: Any,
    ) -> None:
        self._body = body
        self._params = params

    @classmethod
    def from_entities(cls, text: str, entities: List[MessageEntity]) -> "Node":
        return Node(
            *_unparse_entities(
                text=add_surrogates(text),
                entities=sorted(entities, key=lambda item: item.offset) if entities else [],
            )
        )

    def render(
        self,
        *,
        _offset: int = 0,
        _sort: bool = True,
        _collect_entities: bool = True,
    ) -> Tuple[str, List[MessageEntity]]:
        text = ""
        entities = []
        offset = _offset

        for node in self._body:
            if isinstance(node, str):
                text += node
                offset += sizeof(node)
            else:
                node_text, node_entities = node.render(
                    _offset=offset, _sort=False, _collect_entities=_collect_entities
                )
                text += node_text
                offset += sizeof(node_text)
                if _collect_entities:
                    entities.extend(node_entities)

        if _collect_entities and self.type:
            entities.append(self._render_entity(offset=_offset, length=offset - _offset))

        if _collect_entities and _sort:
            entities.sort(key=lambda entity: entity.offset)

        return text, entities

    def _render_entity(self, *, offset: int, length: int) -> MessageEntity:
        return MessageEntity(type=self.type, offset=offset, length=length, **self._params)

    def to_kwargs(
        self,
        *,
        text_key: str = "text",
        entities_key: str = "entities",
        replace_parse_mode: bool = False,
        parse_mode_key: str = "parse_mode",
    ) -> Dict[str, Union[str, List[MessageEntity]]]:
        text_value, entities_value = self.render()
        result = {
            text_key: text_value,
            entities_key: entities_value,
        }
        if replace_parse_mode:
            result[parse_mode_key] = None
        return result

    def to_html(self) -> str:
        text, entities = self.render()
        return html_decoration.unparse(text, entities)

    def to_markdown(self) -> str:
        text, entities = self.render()
        return markdown_decoration.unparse(text, entities)

    def __repr__(self) -> str:
        body = ", ".join(repr(item) for item in self._body)
        params = ", ".join(f"{k}={v!r}" for k, v in self._params.items())

        args = []
        if body:
            args.append(body)
        if params:
            args.append(params)

        return f"{type(self).__name__}({', '.join(args)})"

    def __add__(self, other: NodeType) -> "Node":
        if type(self) == type(other) and self._params == other._params:
            return type(self)(*self._body, *other._body, **self._params)
        if type(self) == Node and isinstance(other, str):
            return type(self)(*self._body, other, **self._params)
        return Node(self, other)

    def line(self: NodeT, *nodes: NodeType) -> NodeT:
        first_node = Text(self) if isinstance(self, str) else self
        return first_node + Text(*nodes, "\n")

    def replace(self: NodeT, *args: Any, **kwargs: Any) -> NodeT:
        return type(self)(*args, **{**self._params, **kwargs})

    def __iter__(self) -> Iterator[NodeT]:
        return iter(self._body)

    def __len__(self) -> int:
        text, _ = self.render(_collect_entities=False)
        return sizeof(text)

    def __getitem__(self, item):
        # FIXME: currently is not always separate text in correct place
        if not isinstance(item, slice):
            raise TypeError("Can only be sliced")
        if (item.start is None or item.start == 0) and item.stop is None:
            return self

        start = item.start or 0
        stop = item.stop or len(self)

        nodes = []
        position = 0

        for node in self._body:
            node_size = len(node)
            current_position = position
            position += node_size
            if position < start:
                continue
            if current_position > stop:
                break
            new_node = node[start - current_position : stop - current_position]
            if not new_node:
                continue
            nodes.append(new_node)

        return self.replace(*nodes)


class HashTag(Node):
    type = MessageEntityType.HASHTAG


class CashTag(Node):
    type = MessageEntityType.CASHTAG


class BotCommand(Node):
    type = MessageEntityType.BOT_COMMAND


class Url(Node):
    type = MessageEntityType.URL


class Email(Node):
    type = MessageEntityType.EMAIL


class PhoneNumber(Node):
    type = MessageEntityType.PHONE_NUMBER


class Bold(Node):
    type = MessageEntityType.BOLD


class Italic(Node):
    type = MessageEntityType.ITALIC


class Underline(Node):
    type = MessageEntityType.UNDERLINE


class Strikethrough(Node):
    type = MessageEntityType.STRIKETHROUGH


class Spoiler(Node):
    type = MessageEntityType.SPOILER


class Code(Node):
    type = MessageEntityType.CODE


class Pre(Node):
    type = MessageEntityType.PRE

    def __init__(self, *body: NodeType, language: str, **params: Any) -> None:
        super().__init__(*body, language=language, **params)


class TextLink(Node):
    type = MessageEntityType.TEXT_LINK

    def __init__(self, *body: NodeType, url: str, **params: Any) -> None:
        super().__init__(*body, url=url, **params)


class TextMention(Node):
    type = MessageEntityType.TEXT_MENTION

    def __init__(self, *body: NodeType, user: User, **params: Any) -> None:
        super().__init__(*body, user=user, **params)


Text = Node
Strong = Bold

NODE_TYPES = {
    HashTag.type: HashTag,
    CashTag.type: CashTag,
    BotCommand.type: BotCommand,
    Url.type: Url,
    Email.type: Email,
    PhoneNumber.type: PhoneNumber,
    Bold.type: Bold,
    Italic.type: Italic,
    Underline.type: Underline,
    Strikethrough.type: Strikethrough,
    Spoiler.type: Spoiler,
    Code.type: Code,
    Pre.type: Pre,
    TextLink.type: TextLink,
    TextMention.type: TextMention,
    Text.type: Text,
}


def _apply_entity(entity: MessageEntity, *nodes: NodeType) -> NodeType:
    """
    Apply single entity to text

    :param entity:
    :param text:
    :return:
    """
    node_type = NODE_TYPES.get(entity.type, Node)
    return node_type(*nodes, **entity.dict(exclude={"type", "offset", "length"}))


def _unparse_entities(
    text: bytes,
    entities: List[MessageEntity],
    offset: Optional[int] = None,
    length: Optional[int] = None,
) -> Generator[NodeType, None, None]:
    if offset is None:
        offset = 0
    length = length or len(text)

    for index, entity in enumerate(entities):
        if entity.offset * 2 < offset:
            continue
        if entity.offset * 2 > offset:
            yield remove_surrogates(text[offset : entity.offset * 2])
        start = entity.offset * 2
        offset = entity.offset * 2 + entity.length * 2

        sub_entities = list(filter(lambda e: e.offset * 2 < (offset or 0), entities[index + 1 :]))
        yield _apply_entity(
            entity,
            *_unparse_entities(text, sub_entities, offset=start, length=offset),
        )

    if offset < length:
        yield remove_surrogates(text[offset:length])


def as_list(*items: NodeType) -> Node:
    nodes = []
    for item in items[:-1]:
        nodes.extend([item, "\n"])
    nodes.append(items[-1])
    return Node(*nodes)


def as_marked_list(*items: NodeType, marker: str = "- ") -> Node:
    return as_list(*(Node(marker, item) for item in items))


def as_numbered_list(*items: NodeType, start: int = 1, fmt: str = "{}. ") -> Node:
    return as_list(*(Node(fmt.format(index), item) for index, item in enumerate(items, start)))
