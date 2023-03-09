import typing

from . import base, fields
from .input_file import InputFile
from .mask_position import MaskPosition


class InputSticker(base.TelegramObject):
    """
    This object describes a sticker to be added to a sticker set.

    https://core.telegram.org/bots/api#inputsticker
    """
    sticker: typing.Union[InputFile, base.String] = fields.Field()
    emoji_list: typing.List[base.String] = fields.ListField(base=base.String)
    mask_position: MaskPosition = fields.Field(base=MaskPosition)
    keywords: typing.Optional[typing.List[base.String]] = fields.ListField(base=base.String)

    def __init__(
        self,
        *,
        sticker: typing.Union[InputFile, base.String],
        emoji_list: typing.List[base.String],
        mask_position: typing.Optional[MaskPosition] = None,
        keywords: typing.Optional[typing.List[base.String]] = None,
    ):
        super().__init__(
            sticker=sticker,
            emoji_list=emoji_list,
            mask_position=mask_position,
            keywords=keywords,
        )
