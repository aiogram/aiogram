from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydantic import Field

from .inline_query_result import InlineQueryResult

if TYPE_CHECKING:  # pragma: no cover
    from .input_message_content import InputMessageContent
    from .inline_keyboard_markup import InlineKeyboardMarkup


class InlineQueryResultAudio(InlineQueryResult):
    """
    Represents a link to an MP3 audio file. By default, this audio file will be sent by the user.
    Alternatively, you can use input_message_content to send a message with the specified content
    instead of the audio.
    Note: This will only work in Telegram versions released after 9 April, 2016. Older clients
    will ignore them.

    Source: https://core.telegram.org/bots/api#inlinequeryresultaudio
    """

    type: str = Field("audio", const=True)
    """Type of the result, must be audio"""
    id: str
    """Unique identifier for this result, 1-64 bytes"""
    audio_url: str
    """A valid URL for the audio file"""
    title: str
    """Title"""
    caption: Optional[str] = None
    """Caption, 0-1024 characters"""
    parse_mode: Optional[str] = None
    """Send Markdown or HTML, if you want Telegram apps to show bold, italic, fixed-width text or
    inline URLs in the media caption."""
    performer: Optional[str] = None
    """Performer"""
    audio_duration: Optional[int] = None
    """Audio duration in seconds"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """Inline keyboard attached to the message"""
    input_message_content: Optional[InputMessageContent] = None
    """Content of the message to be sent instead of the audio"""
