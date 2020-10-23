# Implementation inspired on the similar one from telethon
# Credits to https://github.com/LonamiWebs/Telethon

from typing import Tuple, List, Dict, Deque, Optional
import struct
from collections import deque
from html.parser import HTMLParser

from aiogram.types.message_entity import (
    MessageEntity,
    MessageEntityType,
)


# region Unicode surrogates
def add_surrogate(text: str) -> str:
    return ''.join(
        # SMP -> Surrogate Pairs (Telegram offsets are calculated with these).
        # See https://en.wikipedia.org/wiki/Plane_(Unicode)#Overview for more.
        ''.join(chr(y) for y in struct.unpack('<HH', x.encode('utf-16le')))
        if (0x10000 <= ord(x) <= 0x10FFFF) else x for x in text
    )


def del_surrogate(text: str) -> str:
    return text.encode('utf-16', 'surrogatepass').decode('utf-16')
# endregion


def strip_text(text: str, entities: List[MessageEntity]) -> str:
    if not entities:
        return text.strip()

    while text and text[-1].isspace():
        e = entities[-1]
        if e.offset + e.length == len(text):
            if e.length == 1:
                del entities[-1]
                if not entities:
                    return text.strip()
            else:
                e.length -= 1
        text = text[:-1]

    while text and text[0].isspace():
        for i in reversed(range(len(entities))):
            e = entities[i]
            if e.offset != 0:
                e.offset -= 1
                continue

            if e.length == 1:
                del entities[0]
                if not entities:
                    return text.lstrip()
            else:
                e.length -= 1

        text = text[1:]

    return text


# region HTML parser
class _HTMLToTelegramParser(HTMLParser):
    def __init__(self):
        super(_HTMLToTelegramParser, self).__init__(convert_charrefs=False)

        self.text = ''

        self.entities: List[MessageEntity] = []
        self._building_entities: Dict[str, MessageEntity] = {}

        self._open_tags: Deque[MessageEntity] = deque()
        self._open_tags_meta: Deque[Optional[MessageEntity]] = deque()

    def handle_starttag(self, tag, attrs):
        self._open_tags.appendleft(tag)
        self._open_tags_meta.appendleft(None)

        attrs = dict(attrs)
        entity_type = None
        args = {}
        if tag == 'strong' or tag == 'b':
            entity_type = MessageEntityType.BOLD
        elif tag == 'em' or tag == 'i':
            entity_type = MessageEntityType.ITALIC
        elif tag == 'u':
            entity_type = MessageEntityType.UNDERLINE
        elif tag == 'del' or tag == 's':
            entity_type = MessageEntityType.STRIKETHROUGH
        elif tag == 'code':
            try:
                pre = self._building_entities['pre']
                try:
                    pre.language = attrs['class'][len('language-'):]
                except KeyError:
                    pass
            except KeyError:
                entity_type = MessageEntityType.CODE
        elif tag == 'pre':
            entity_type = MessageEntityType.PRE
            args['language'] = ''
        elif tag == 'a':
            try:
                url = attrs['href']
            except KeyError:
                return
            if url.startswith('mailto:'):
                url = url[len('mailto:'):]
                entity_type = MessageEntityType.EMAIL
            else:
                if self.get_starttag_text() == url:
                    entity_type = MessageEntityType.URL
                else:
                    entity_type = MessageEntityType.TEXT_LINK
                    args['url'] = url
                    url = None
            self._open_tags_meta.popleft()
            self._open_tags_meta.appendleft(url)

        if entity_type and tag not in self._building_entities:
            self._building_entities[tag] = MessageEntity(
                type=entity_type,
                offset=len(self.text),
                length=0,
                **args,)

    def handle_data(self, text):
        previous_tag = self._open_tags[0] if len(self._open_tags) > 0 else ''
        if previous_tag == 'a':
            url = self._open_tags_meta[0]
            if url:
                text = url

        for tag, entity in self._building_entities.items():
            entity.length += len(text)

        self.text += text

    def handle_endtag(self, tag):
        try:
            self._open_tags.popleft()
            self._open_tags_meta.popleft()
        except IndexError:
            pass
        entity = self._building_entities.pop(tag, None)
        if entity:
            self.entities.append(entity)

    def error(self, message):
        raise ValueError(message)


def parse_html(html: str) -> Tuple[str, List[MessageEntity]]:
    if not html:
        return html, []

    parser = _HTMLToTelegramParser()
    parser.feed(add_surrogate(html))
    text = strip_text(parser.text, parser.entities)
    return del_surrogate(text), parser.entities

# endregion

