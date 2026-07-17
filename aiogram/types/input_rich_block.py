from .base import TelegramObject


class InputRichBlock(TelegramObject):
    """
    This object represents a block in a rich formatted message to be sent. Currently, it can be any of the following types:

     - :class:`aiogram.types.input_rich_block_paragraph.InputRichBlockParagraph`
     - :class:`aiogram.types.input_rich_block_section_heading.InputRichBlockSectionHeading`
     - :class:`aiogram.types.input_rich_block_preformatted.InputRichBlockPreformatted`
     - :class:`aiogram.types.input_rich_block_footer.InputRichBlockFooter`
     - :class:`aiogram.types.input_rich_block_divider.InputRichBlockDivider`
     - :class:`aiogram.types.input_rich_block_mathematical_expression.InputRichBlockMathematicalExpression`
     - :class:`aiogram.types.input_rich_block_anchor.InputRichBlockAnchor`
     - :class:`aiogram.types.input_rich_block_list.InputRichBlockList`
     - :class:`aiogram.types.input_rich_block_block_quotation.InputRichBlockBlockQuotation`
     - :class:`aiogram.types.input_rich_block_pull_quotation.InputRichBlockPullQuotation`
     - :class:`aiogram.types.input_rich_block_collage.InputRichBlockCollage`
     - :class:`aiogram.types.input_rich_block_slideshow.InputRichBlockSlideshow`
     - :class:`aiogram.types.input_rich_block_table.InputRichBlockTable`
     - :class:`aiogram.types.input_rich_block_details.InputRichBlockDetails`
     - :class:`aiogram.types.input_rich_block_map.InputRichBlockMap`
     - :class:`aiogram.types.input_rich_block_animation.InputRichBlockAnimation`
     - :class:`aiogram.types.input_rich_block_audio.InputRichBlockAudio`
     - :class:`aiogram.types.input_rich_block_photo.InputRichBlockPhoto`
     - :class:`aiogram.types.input_rich_block_video.InputRichBlockVideo`
     - :class:`aiogram.types.input_rich_block_voice_note.InputRichBlockVoiceNote`
     - :class:`aiogram.types.input_rich_block_thinking.InputRichBlockThinking`

    Source: https://core.telegram.org/bots/api#inputrichblock
    """
