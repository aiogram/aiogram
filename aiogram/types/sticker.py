from . import base
from . import fields
from . import mixins
from .mask_position import MaskPosition
from .photo_size import PhotoSize


class Sticker(base.TelegramObject, mixins.Downloadable):
    """
    This object represents a sticker.

    https://core.telegram.org/bots/api#sticker
    """
    file_id: base.String = fields.Field()
    file_unique_id: base.String = fields.Field()
    width: base.Integer = fields.Field()
    height: base.Integer = fields.Field()
    is_animated: base.Boolean = fields.Field()
    is_video: base.Boolean = fields.Field()
    thumb: PhotoSize = fields.Field(base=PhotoSize)
    emoji: base.String = fields.Field()
    set_name: base.String = fields.Field()
    mask_position: MaskPosition = fields.Field(base=MaskPosition)
    file_size: base.Integer = fields.Field()

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
