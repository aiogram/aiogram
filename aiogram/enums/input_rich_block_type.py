from enum import Enum


class InputRichBlockType(str, Enum):
    """
    This object represents a block in a rich formatted message to be sent.

    Source: https://core.telegram.org/bots/api#inputrichblock
    """

    ANCHOR = "anchor"
    ANIMATION = "animation"
    AUDIO = "audio"
    BLOCKQUOTE = "blockquote"
    BUTTONS = "buttons"
    COLLAGE = "collage"
    DETAILS = "details"
    DIVIDER = "divider"
    DOCUMENT = "document"
    EXPANDABLE_BLOCKQUOTE = "expandable_blockquote"
    FOOTER = "footer"
    LIST = "list"
    MAP = "map"
    MATHEMATICAL_EXPRESSION = "mathematical_expression"
    PARAGRAPH = "paragraph"
    PHOTO = "photo"
    PRE = "pre"
    PULLQUOTE = "pullquote"
    HEADING = "heading"
    SLIDESHOW = "slideshow"
    TABLE = "table"
    THINKING = "thinking"
    VIDEO = "video"
    VOICE_NOTE = "voice_note"
