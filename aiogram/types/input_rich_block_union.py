from typing import Annotated, TypeAlias

from pydantic import Field

from .input_rich_block_anchor import InputRichBlockAnchor
from .input_rich_block_animation import InputRichBlockAnimation
from .input_rich_block_audio import InputRichBlockAudio
from .input_rich_block_block_quotation import InputRichBlockBlockQuotation
from .input_rich_block_collage import InputRichBlockCollage
from .input_rich_block_details import InputRichBlockDetails
from .input_rich_block_divider import InputRichBlockDivider
from .input_rich_block_footer import InputRichBlockFooter
from .input_rich_block_list import InputRichBlockList
from .input_rich_block_map import InputRichBlockMap
from .input_rich_block_mathematical_expression import InputRichBlockMathematicalExpression
from .input_rich_block_paragraph import InputRichBlockParagraph
from .input_rich_block_photo import InputRichBlockPhoto
from .input_rich_block_preformatted import InputRichBlockPreformatted
from .input_rich_block_pull_quotation import InputRichBlockPullQuotation
from .input_rich_block_section_heading import InputRichBlockSectionHeading
from .input_rich_block_slideshow import InputRichBlockSlideshow
from .input_rich_block_table import InputRichBlockTable
from .input_rich_block_thinking import InputRichBlockThinking
from .input_rich_block_video import InputRichBlockVideo
from .input_rich_block_voice_note import InputRichBlockVoiceNote

InputRichBlockUnion: TypeAlias = Annotated[
    InputRichBlockParagraph
    | InputRichBlockSectionHeading
    | InputRichBlockPreformatted
    | InputRichBlockFooter
    | InputRichBlockDivider
    | InputRichBlockMathematicalExpression
    | InputRichBlockAnchor
    | InputRichBlockList
    | InputRichBlockBlockQuotation
    | InputRichBlockPullQuotation
    | InputRichBlockCollage
    | InputRichBlockSlideshow
    | InputRichBlockTable
    | InputRichBlockDetails
    | InputRichBlockMap
    | InputRichBlockAnimation
    | InputRichBlockAudio
    | InputRichBlockPhoto
    | InputRichBlockVideo
    | InputRichBlockVoiceNote
    | InputRichBlockThinking,
    Field(discriminator="type"),
]
