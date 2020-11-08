import typing

from . import base, fields
from .inline_keyboard import InlineKeyboardMarkup
from .input_message_content import InputMessageContent
from .message_entity import MessageEntity


class InlineQueryResult(base.TelegramObject):
    """
    This object represents one result of an inline query.

    Telegram clients currently support results of the following 20 types

    https://core.telegram.org/bots/api#inlinequeryresult
    """
    id: base.String = fields.Field()
    reply_markup: InlineKeyboardMarkup = fields.Field(base=InlineKeyboardMarkup)

    def safe_get_parse_mode(self):
        try:
            return self.bot.parse_mode
        except RuntimeError:
            pass

    def __init__(self, **kwargs):
        if 'parse_mode' in kwargs and kwargs['parse_mode'] is None:
            kwargs['parse_mode'] = self.safe_get_parse_mode()
        super(InlineQueryResult, self).__init__(**kwargs)


class InlineQueryResultArticle(InlineQueryResult):
    """
    Represents a link to an article or web page.

    https://core.telegram.org/bots/api#inlinequeryresultarticle
    """
    type: base.String = fields.Field(alias='type', default='article')
    title: base.String = fields.Field()
    input_message_content: InputMessageContent = fields.Field(base=InputMessageContent)
    url: base.String = fields.Field()
    hide_url: base.Boolean = fields.Field()
    description: base.String = fields.Field()
    thumb_url: base.String = fields.Field()
    thumb_width: base.Integer = fields.Field()
    thumb_height: base.Integer = fields.Field()


class InlineQueryResultPhoto(InlineQueryResult):
    """
    Represents a link to a photo.

    By default, this photo will be sent by the user with optional caption.
    Alternatively, you can use input_message_content to send a message with the specified content
    instead of the photo.

    https://core.telegram.org/bots/api#inlinequeryresultphoto
    """
    type: base.String = fields.Field(alias='type', default='photo')
    photo_url: base.String = fields.Field()
    thumb_url: base.String = fields.Field()
    photo_width: base.Integer = fields.Field()
    photo_height: base.Integer = fields.Field()
    title: base.String = fields.Field()
    description: base.String = fields.Field()
    caption: base.String = fields.Field()
    input_message_content: InputMessageContent = fields.Field(base=InputMessageContent)


class InlineQueryResultGif(InlineQueryResult):
    """
    Represents a link to an animated GIF file.

    By default, this animated GIF file will be sent by the user with optional caption.
    Alternatively, you can use input_message_content to send a message with the specified content
    instead of the animation.

    https://core.telegram.org/bots/api#inlinequeryresultgif
    """
    type: base.String = fields.Field(alias='type', default='gif')
    gif_url: base.String = fields.Field()
    gif_width: base.Integer = fields.Field()
    gif_height: base.Integer = fields.Field()
    gif_duration: base.Integer = fields.Field()
    thumb_url: base.String = fields.Field()
    thumb_mime_type: base.String = fields.Field()
    title: base.String = fields.Field()
    caption: base.String = fields.Field()
    input_message_content: InputMessageContent = fields.Field(base=InputMessageContent)


class InlineQueryResultMpeg4Gif(InlineQueryResult):
    """
    Represents a link to a video animation (H.264/MPEG-4 AVC video without sound).

    By default, this animated MPEG-4 file will be sent by the user with optional caption.
    Alternatively, you can use input_message_content to send a message with the specified content
    instead of the animation.

    https://core.telegram.org/bots/api#inlinequeryresultmpeg4gif
    """
    type: base.String = fields.Field(alias='type', default='mpeg4_gif')
    mpeg4_url: base.String = fields.Field()
    mpeg4_width: base.Integer = fields.Field()
    mpeg4_height: base.Integer = fields.Field()
    mpeg4_duration: base.Integer = fields.Field()
    thumb_url: base.String = fields.Field()
    thumb_mime_type: base.String = fields.Field()
    title: base.String = fields.Field()
    caption: base.String = fields.Field()
    input_message_content: InputMessageContent = fields.Field(base=InputMessageContent)


class InlineQueryResultVideo(InlineQueryResult):
    """
    Represents a link to a page containing an embedded video player or a video file.

    By default, this video file will be sent by the user with an optional caption.
    Alternatively, you can use input_message_content to send a message with the specified content
    instead of the video.

    If an InlineQueryResultVideo message contains an embedded video (e.g., YouTube),
    you must replace its content using input_message_content.

    https://core.telegram.org/bots/api#inlinequeryresultvideo
    """
    type: base.String = fields.Field(alias='type', default='video')
    video_url: base.String = fields.Field()
    mime_type: base.String = fields.Field()
    thumb_url: base.String = fields.Field()
    title: base.String = fields.Field()
    caption: base.String = fields.Field()
    video_width: base.Integer = fields.Field()
    video_height: base.Integer = fields.Field()
    video_duration: base.Integer = fields.Field()
    description: base.String = fields.Field()
    input_message_content: InputMessageContent = fields.Field(base=InputMessageContent)


class InlineQueryResultAudio(InlineQueryResult):
    """
    Represents a link to an mp3 audio file. By default, this audio file will be sent by the user.
    Alternatively, you can use input_message_content to send a message with the specified content
    instead of the audio.

    Note: This will only work in Telegram versions released after 9 April, 2016.
    Older clients will ignore them.

    https://core.telegram.org/bots/api#inlinequeryresultaudio
    """
    type: base.String = fields.Field(alias='type', default='audio')
    audio_url: base.String = fields.Field()
    title: base.String = fields.Field()
    caption: base.String = fields.Field()
    performer: base.String = fields.Field()
    audio_duration: base.Integer = fields.Field()
    input_message_content: InputMessageContent = fields.Field(base=InputMessageContent)


class InlineQueryResultVoice(InlineQueryResult):
    """
    Represents a link to a voice recording in an .ogg container encoded with OPUS.

    By default, this voice recording will be sent by the user.
    Alternatively, you can use input_message_content to send a message with the specified content
    instead of the the voice message.

    Note: This will only work in Telegram versions released after 9 April, 2016.
    Older clients will ignore them.

    https://core.telegram.org/bots/api#inlinequeryresultvoice
    """
    type: base.String = fields.Field(alias='type', default='voice')
    voice_url: base.String = fields.Field()
    title: base.String = fields.Field()
    caption: base.String = fields.Field()
    voice_duration: base.Integer = fields.Field()
    input_message_content: InputMessageContent = fields.Field(base=InputMessageContent)


class InlineQueryResultDocument(InlineQueryResult):
    """
    Represents a link to a file.

    By default, this file will be sent by the user with an optional caption.
    Alternatively, you can use input_message_content to send a message with the specified content
    instead of the file. Currently, only .PDF and .ZIP files can be sent using this method.

    Note: This will only work in Telegram versions released after 9 April, 2016. Older clients will ignore them.

    https://core.telegram.org/bots/api#inlinequeryresultdocument
    """
    type: base.String = fields.Field(alias='type', default='document')
    title: base.String = fields.Field()
    caption: base.String = fields.Field()
    document_url: base.String = fields.Field()
    mime_type: base.String = fields.Field()
    description: base.String = fields.Field()
    input_message_content: InputMessageContent = fields.Field(base=InputMessageContent)
    thumb_url: base.String = fields.Field()
    thumb_width: base.Integer = fields.Field()
    thumb_height: base.Integer = fields.Field()


class InlineQueryResultLocation(InlineQueryResult):
    """
    Represents a location on a map.

    By default, the location will be sent by the user.
    Alternatively, you can use input_message_content to send a message with the specified content
    instead of the location.

    https://core.telegram.org/bots/api#inlinequeryresultlocation
    """
    type: base.String = fields.Field(alias='type', default='location')
    latitude: base.Float = fields.Field()
    longitude: base.Float = fields.Field()
    title: base.String = fields.Field()
    horizontal_accuracy: typing.Optional[base.Float] = fields.Field()
    live_period: base.Integer = fields.Field()
    heading: typing.Optional[base.Integer] = fields.Field()
    proximity_alert_radius: typing.Optional[base.Integer] = fields.Field()
    input_message_content: InputMessageContent = fields.Field(base=InputMessageContent)
    thumb_url: base.String = fields.Field()
    thumb_width: base.Integer = fields.Field()
    thumb_height: base.Integer = fields.Field()


class InlineQueryResultVenue(InlineQueryResult):
    """
    Represents a venue. By default, the venue will be sent by the user.

    Alternatively, you can use input_message_content to send a message with the specified content
    instead of the venue.

    Note: This will only work in Telegram versions released after 9 April, 2016.
    Older clients will ignore them.

    https://core.telegram.org/bots/api#inlinequeryresultvenue
    """
    type: base.String = fields.Field(alias='type', default='venue')
    latitude: base.Float = fields.Field()
    longitude: base.Float = fields.Field()
    title: base.String = fields.Field()
    address: base.String = fields.Field()
    foursquare_id: base.String = fields.Field()
    foursquare_type: base.String = fields.Field()
    google_place_id: base.String = fields.Field()
    google_place_type: base.String = fields.Field()
    input_message_content: InputMessageContent = fields.Field(base=InputMessageContent)
    thumb_url: base.String = fields.Field()
    thumb_width: base.Integer = fields.Field()
    thumb_height: base.Integer = fields.Field()


class InlineQueryResultContact(InlineQueryResult):
    """
    Represents a contact with a phone number.

    By default, this contact will be sent by the user.
    Alternatively, you can use input_message_content to send a message with the specified content
    instead of the contact.

    Note: This will only work in Telegram versions released after 9 April, 2016. Older clients will ignore them.

    https://core.telegram.org/bots/api#inlinequeryresultcontact
    """
    type: base.String = fields.Field(alias='type', default='contact')
    phone_number: base.String = fields.Field()
    first_name: base.String = fields.Field()
    last_name: base.String = fields.Field()
    vcard: base.String = fields.Field()
    input_message_content: InputMessageContent = fields.Field(base=InputMessageContent)
    thumb_url: base.String = fields.Field()
    thumb_width: base.Integer = fields.Field()
    thumb_height: base.Integer = fields.Field()
    foursquare_type: base.String = fields.Field()


class InlineQueryResultGame(InlineQueryResult):
    """
    Represents a Game.

    Note: This will only work in Telegram versions released after October 1, 2016.
    Older clients will not display any inline results if a game result is among them.

    https://core.telegram.org/bots/api#inlinequeryresultgame
    """
    type: base.String = fields.Field(alias='type', default='game')
    game_short_name: base.String = fields.Field()


class InlineQueryResultCachedPhoto(InlineQueryResult):
    """
    Represents a link to a photo stored on the Telegram servers.

    By default, this photo will be sent by the user with an optional caption.
    Alternatively, you can use input_message_content to send a message with the specified content
    instead of the photo.

    https://core.telegram.org/bots/api#inlinequeryresultcachedphoto
    """
    type: base.String = fields.Field(alias='type', default='photo')
    photo_file_id: base.String = fields.Field()
    title: base.String = fields.Field()
    description: base.String = fields.Field()
    caption: base.String = fields.Field()
    input_message_content: InputMessageContent = fields.Field(base=InputMessageContent)


class InlineQueryResultCachedGif(InlineQueryResult):
    """
    Represents a link to an animated GIF file stored on the Telegram servers.

    By default, this animated GIF file will be sent by the user with an optional caption.
    Alternatively, you can use input_message_content to send a message with specified content
    instead of the animation.

    https://core.telegram.org/bots/api#inlinequeryresultcachedgif
    """
    type: base.String = fields.Field(alias='type', default='gif')
    gif_file_id: base.String = fields.Field()
    title: base.String = fields.Field()
    caption: base.String = fields.Field()
    input_message_content: InputMessageContent = fields.Field(base=InputMessageContent)


class InlineQueryResultCachedMpeg4Gif(InlineQueryResult):
    """
    Represents a link to a video animation (H.264/MPEG-4 AVC video without sound) stored on the Telegram servers.

    By default, this animated MPEG-4 file will be sent by the user with an optional caption.
    Alternatively, you can use input_message_content to send a message with the specified content
    instead of the animation.

    https://core.telegram.org/bots/api#inlinequeryresultcachedmpeg4gif
    """
    type: base.String = fields.Field(alias='type', default='mpeg4_gif')
    mpeg4_file_id: base.String = fields.Field()
    title: base.String = fields.Field()
    caption: base.String = fields.Field()
    input_message_content: InputMessageContent = fields.Field(base=InputMessageContent)


class InlineQueryResultCachedSticker(InlineQueryResult):
    """
    Represents a link to a sticker stored on the Telegram servers.

    By default, this sticker will be sent by the user.
    Alternatively, you can use input_message_content to send a message with the specified content
    instead of the sticker.

    Note: This will only work in Telegram versions released after 9 April, 2016.
    Older clients will ignore them.

    https://core.telegram.org/bots/api#inlinequeryresultcachedsticker
    """
    type: base.String = fields.Field(alias='type', default='sticker')
    sticker_file_id: base.String = fields.Field()
    input_message_content: InputMessageContent = fields.Field(base=InputMessageContent)


class InlineQueryResultCachedDocument(InlineQueryResult):
    """
    Represents a link to a file stored on the Telegram servers.
    By default, this file will be sent by the user with an optional caption.
    Alternatively, you can use input_message_content to send a message with the specified content
    instead of the file.

    Note: This will only work in Telegram versions released after 9 April, 2016.
    Older clients will ignore them.

    https://core.telegram.org/bots/api#inlinequeryresultcacheddocument
    """
    type: base.String = fields.Field(alias='type', default='document')
    title: base.String = fields.Field()
    document_file_id: base.String = fields.Field()
    description: base.String = fields.Field()
    caption: base.String = fields.Field()
    input_message_content: InputMessageContent = fields.Field(base=InputMessageContent)


class InlineQueryResultCachedVideo(InlineQueryResult):
    """
    Represents a link to a video file stored on the Telegram servers.

    By default, this video file will be sent by the user with an optional caption.
    Alternatively, you can use input_message_content to send a message with the specified content
    instead of the video.

    https://core.telegram.org/bots/api#inlinequeryresultcachedvideo
    """
    type: base.String = fields.Field(alias='type', default='video')
    video_file_id: base.String = fields.Field()
    title: base.String = fields.Field()
    description: base.String = fields.Field()
    caption: base.String = fields.Field()
    input_message_content: InputMessageContent = fields.Field(base=InputMessageContent)


class InlineQueryResultCachedVoice(InlineQueryResult):
    """
    Represents a link to a voice message stored on the Telegram servers.

    By default, this voice message will be sent by the user.
    Alternatively, you can use input_message_content to send a message with the specified content
    instead of the voice message.

    Note: This will only work in Telegram versions released after 9 April, 2016. Older clients will ignore them.

    https://core.telegram.org/bots/api#inlinequeryresultcachedvoice
    """
    type: base.String = fields.Field(alias='type', default='voice')
    voice_file_id: base.String = fields.Field()
    title: base.String = fields.Field()
    caption: base.String = fields.Field()
    input_message_content: InputMessageContent = fields.Field(base=InputMessageContent)


class InlineQueryResultCachedAudio(InlineQueryResult):
    """
    Represents a link to an mp3 audio file stored on the Telegram servers.

    By default, this audio file will be sent by the user.
    Alternatively, you can use input_message_content to send a message with
    the specified content instead of the audio.

    Note: This will only work in Telegram versions released after 9 April, 2016.
    Older clients will ignore them.

    https://core.telegram.org/bots/api#inlinequeryresultcachedaudio
    """
    type: base.String = fields.Field(alias='type', default='audio')
    audio_file_id: base.String = fields.Field()
    caption: base.String = fields.Field()
    input_message_content: InputMessageContent = fields.Field(base=InputMessageContent)
