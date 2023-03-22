import typing

from . import base
from . import fields
from . import mixins
from .mask_position import MaskPosition
from .photo_size import PhotoSize
from .file import File
from ..utils.deprecated import warn_deprecated


class Sticker(base.TelegramObject, mixins.Downloadable):
    """
    This object represents a sticker.

    https://core.telegram.org/bots/api#sticker
    """
    file_id: base.String = fields.Field()
    file_unique_id: base.String = fields.Field()
    type: base.String = fields.Field()
    width: base.Integer = fields.Field()
    height: base.Integer = fields.Field()
    is_animated: base.Boolean = fields.Field()
    is_video: base.Boolean = fields.Field()
    thumb: PhotoSize = fields.Field(base=PhotoSize)
    thumbnail: PhotoSize = fields.Field(base=PhotoSize)
    emoji: base.String = fields.Field()
    set_name: base.String = fields.Field()
    premium_animation: File = fields.Field(base=File)
    mask_position: MaskPosition = fields.Field(base=MaskPosition)
    custom_emoji_id: base.String = fields.Field()
    needs_repainting: base.Boolean = fields.Field()
    file_size: base.Integer = fields.Field()

    def __init__(
            self,
            file_id: base.String,
            file_unique_id: base.String,
            type: base.String,
            width: base.Integer,
            height: base.Integer,
            is_animated: base.Boolean,
            is_video: base.Boolean,
            thumb: typing.Optional[PhotoSize] = None,
            thumbnail: typing.Optional[PhotoSize] = None,
            emoji: typing.Optional[base.String] = None,
            set_name: typing.Optional[base.String] = None,
            premium_animation: typing.Optional[File] = None,
            mask_position: typing.Optional[MaskPosition] = None,
            custom_emoji_id: typing.Optional[base.String] = None,
            needs_repainting: typing.Optional[base.Boolean] = None,
            file_size: typing.Optional[base.Integer] = None,
    ):
        if thumb is not None:
            warn_deprecated(
                "The 'thumb' parameter is deprecated, use 'thumbnail' instead."
            )
            thumbnail = thumb

        super().__init__(
            file_id=file_id,
            file_unique_id=file_unique_id,
            type=type,
            width=width,
            height=height,
            is_animated=is_animated,
            is_video=is_video,
            thumbnail=thumbnail,
            emoji=emoji,
            set_name=set_name,
            premium_animation=premium_animation,
            mask_position=mask_position,
            custom_emoji_id=custom_emoji_id,
            needs_repainting=needs_repainting,
            file_size=file_size,
        )

    async def set_position_in_set(self, position: base.Integer) -> base.Boolean:
        """
        Use this method to move a sticker in a set created by the bot to a specific position.

        Source: https://core.telegram.org/bots/api#setstickerpositioninset

        :param position: New sticker position in the set, zero-based
        :type position: :obj:`base.Integer`
        :return: Returns True on success
        :rtype: :obj:`base.Boolean`
        """
        return await self.bot.set_sticker_position_in_set(self.file_id, position=position)

    async def delete_from_set(self) -> base.Boolean:
        """
        Use this method to delete a sticker from a set created by the bot.

        Source: https://core.telegram.org/bots/api#deletestickerfromset

        :return: Returns True on success
        :rtype: :obj:`base.Boolean`
        """
        return await self.bot.delete_sticker_from_set(self.file_id)
