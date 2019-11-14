from __future__ import annotations

from .base import TelegramObject


class InlineQueryResult(TelegramObject):
    """
    This object represents one result of an inline query. Telegram clients currently support
    results of the following 20 types:
     - InlineQueryResultCachedAudio
     - InlineQueryResultCachedDocument
     - InlineQueryResultCachedGif
     - InlineQueryResultCachedMpeg4Gif
     - InlineQueryResultCachedPhoto
     - InlineQueryResultCachedSticker
     - InlineQueryResultCachedVideo
     - InlineQueryResultCachedVoice
     - InlineQueryResultArticle
     - InlineQueryResultAudio
     - InlineQueryResultContact
     - InlineQueryResultGame
     - InlineQueryResultDocument
     - InlineQueryResultGif
     - InlineQueryResultLocation
     - InlineQueryResultMpeg4Gif
     - InlineQueryResultPhoto
     - InlineQueryResultVenue
     - InlineQueryResultVideo
     - InlineQueryResultVoice

    Source: https://core.telegram.org/bots/api#inlinequeryresult
    """
