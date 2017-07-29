from .base import Deserializable
from .sticker import Sticker


class StickerSet(Deserializable):
    """
    This object represents a sticker set.

    https://core.telegram.org/bots/api#stickerset
    """

    def __init__(self, name, title, is_mask, stickers):
        self.name: str = name
        self.title: str = title
        self.is_mask: bool = is_mask
        self.stickers: [Sticker] = stickers

    @classmethod
    def de_json(cls, raw_data):
        name = raw_data.get('name')
        title = raw_data.get('title')
        is_mask = raw_data.get('is_mask')
        stickers = Sticker.deserialize(raw_data.get('stickers'))

        return StickerSet(name, title, is_mask, stickers)
