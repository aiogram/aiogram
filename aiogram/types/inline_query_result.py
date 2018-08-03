import typing

from . import base
from . import fields
from .inline_keyboard import InlineKeyboardMarkup
from .input_message_content import InputMessageContent


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

    def __init__(self, *,
                 id: base.String,
                 title: base.String,
                 input_message_content: InputMessageContent,
                 reply_markup: typing.Optional[InlineKeyboardMarkup] = None,
                 url: typing.Optional[base.String] = None,
                 hide_url: typing.Optional[base.Boolean] = None,
                 description: typing.Optional[base.String] = None,
                 thumb_url: typing.Optional[base.String] = None,
                 thumb_width: typing.Optional[base.Integer] = None,
                 thumb_height: typing.Optional[base.Integer] = None):
        super(InlineQueryResultArticle, self).__init__(id=id, title=title,
                                                       input_message_content=input_message_content,
                                                       reply_markup=reply_markup, url=url, hide_url=hide_url,
                                                       description=description, thumb_url=thumb_url,
                                                       thumb_width=thumb_width, thumb_height=thumb_height)


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

    def __init__(self, *,
                 id: base.String,
                 photo_url: base.String,
                 thumb_url: base.String,
                 photo_width: typing.Optional[base.Integer] = None,
                 photo_height: typing.Optional[base.Integer] = None,
                 title: typing.Optional[base.String] = None,
                 description: typing.Optional[base.String] = None,
                 caption: typing.Optional[base.String] = None,
                 reply_markup: typing.Optional[InlineKeyboardMarkup] = None,
                 input_message_content: typing.Optional[InputMessageContent] = None):
        super(InlineQueryResultPhoto, self).__init__(id=id, photo_url=photo_url, thumb_url=thumb_url,
                                                     photo_width=photo_width, photo_height=photo_height, title=title,
                                                     description=description, caption=caption,
                                                     reply_markup=reply_markup,
                                                     input_message_content=input_message_content)


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
    title: base.String = fields.Field()
    caption: base.String = fields.Field()
    input_message_content: InputMessageContent = fields.Field(base=InputMessageContent)

    def __init__(self, *,
                 id: base.String,
                 gif_url: base.String,
                 gif_width: typing.Optional[base.Integer] = None,
                 gif_height: typing.Optional[base.Integer] = None,
                 gif_duration: typing.Optional[base.Integer] = None,
                 thumb_url: typing.Optional[base.String] = None,
                 title: typing.Optional[base.String] = None,
                 caption: typing.Optional[base.String] = None,
                 parse_mode: typing.Optional[base.String] = None,
                 reply_markup: typing.Optional[InlineKeyboardMarkup] = None,
                 input_message_content: typing.Optional[InputMessageContent] = None):
        super(InlineQueryResultGif, self).__init__(id=id, gif_url=gif_url, gif_width=gif_width,
                                                   gif_height=gif_height, gif_duration=gif_duration,
                                                   thumb_url=thumb_url, title=title, caption=caption,
                                                   parse_mode=parse_mode, reply_markup=reply_markup,
                                                   input_message_content=input_message_content)


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
    title: base.String = fields.Field()
    caption: base.String = fields.Field()
    input_message_content: InputMessageContent = fields.Field(base=InputMessageContent)

    def __init__(self, *,
                 id: base.String,
                 mpeg4_url: base.String,
                 thumb_url: base.String,
                 mpeg4_width: typing.Optional[base.Integer] = None,
                 mpeg4_height: typing.Optional[base.Integer] = None,
                 mpeg4_duration: typing.Optional[base.Integer] = None,
                 title: typing.Optional[base.String] = None,
                 caption: typing.Optional[base.String] = None,
                 parse_mode: typing.Optional[base.String] = None,
                 reply_markup: typing.Optional[InlineKeyboardMarkup] = None,
                 input_message_content: typing.Optional[InputMessageContent] = None):
        super(InlineQueryResultMpeg4Gif, self).__init__(id=id, mpeg4_url=mpeg4_url, mpeg4_width=mpeg4_width,
                                                        mpeg4_height=mpeg4_height, mpeg4_duration=mpeg4_duration,
                                                        thumb_url=thumb_url, title=title, caption=caption,
                                                        parse_mode=parse_mode, reply_markup=reply_markup,
                                                        input_message_content=input_message_content)


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

    def __init__(self, *,
                 id: base.String,
                 video_url: base.String,
                 mime_type: base.String,
                 thumb_url: base.String,
                 title: base.String,
                 caption: typing.Optional[base.String] = None,
                 parse_mode: typing.Optional[base.String] = None,
                 video_width: typing.Optional[base.Integer] = None,
                 video_height: typing.Optional[base.Integer] = None,
                 video_duration: typing.Optional[base.Integer] = None,
                 description: typing.Optional[base.String] = None,
                 reply_markup: typing.Optional[InlineKeyboardMarkup] = None,
                 input_message_content: typing.Optional[InputMessageContent] = None):
        super(InlineQueryResultVideo, self).__init__(id=id, video_url=video_url, mime_type=mime_type,
                                                     thumb_url=thumb_url, title=title, caption=caption,
                                                     video_width=video_width, video_height=video_height,
                                                     video_duration=video_duration, description=description,
                                                     parse_mode=parse_mode, reply_markup=reply_markup,
                                                     input_message_content=input_message_content)


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

    def __init__(self, *,
                 id: base.String,
                 audio_url: base.String,
                 title: base.String,
                 caption: typing.Optional[base.String] = None,
                 parse_mode: typing.Optional[base.String] = None,
                 performer: typing.Optional[base.String] = None,
                 audio_duration: typing.Optional[base.Integer] = None,
                 reply_markup: typing.Optional[InlineKeyboardMarkup] = None,
                 input_message_content: typing.Optional[InputMessageContent] = None):
        super(InlineQueryResultAudio, self).__init__(id=id, audio_url=audio_url, title=title,
                                                     caption=caption, parse_mode=parse_mode,
                                                     performer=performer, audio_duration=audio_duration,
                                                     reply_markup=reply_markup,
                                                     input_message_content=input_message_content)


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

    def __init__(self, *,
                 id: base.String,
                 voice_url: base.String,
                 title: base.String,
                 caption: typing.Optional[base.String] = None,
                 parse_mode: typing.Optional[base.String] = None,
                 voice_duration: typing.Optional[base.Integer] = None,
                 reply_markup: typing.Optional[InlineKeyboardMarkup] = None,
                 input_message_content: typing.Optional[InputMessageContent] = None):
        super(InlineQueryResultVoice, self).__init__(id=id, voice_url=voice_url, title=title,
                                                     caption=caption, voice_duration=voice_duration,
                                                     parse_mode=parse_mode, reply_markup=reply_markup,
                                                     input_message_content=input_message_content)


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

    def __init__(self, *,
                 id: base.String,
                 title: base.String,
                 caption: typing.Optional[base.String] = None,
                 parse_mode: typing.Optional[base.String] = None,
                 document_url: typing.Optional[base.String] = None,
                 mime_type: typing.Optional[base.String] = None,
                 description: typing.Optional[base.String] = None,
                 reply_markup: typing.Optional[InlineKeyboardMarkup] = None,
                 input_message_content: typing.Optional[InputMessageContent] = None,
                 thumb_url: typing.Optional[base.String] = None,
                 thumb_width: typing.Optional[base.Integer] = None,
                 thumb_height: typing.Optional[base.Integer] = None):
        super(InlineQueryResultDocument, self).__init__(id=id, title=title, caption=caption,
                                                        document_url=document_url, mime_type=mime_type,
                                                        description=description, reply_markup=reply_markup,
                                                        input_message_content=input_message_content,
                                                        thumb_url=thumb_url, thumb_width=thumb_width,
                                                        thumb_height=thumb_height, parse_mode=parse_mode)


class InlineQueryResultLocation(InlineQueryResult):
    """
    Represents a location on a map.

    By default, the location will be sent by the user.
    Alternatively, you can use input_message_content to send a message with the specified content
    instead of the location.

    Note: This will only work in Telegram versions released after 9 April, 2016.
    Older clients will ignore them.

    https://core.telegram.org/bots/api#inlinequeryresultlocation
    """
    type: base.String = fields.Field(alias='type', default='location')
    latitude: base.Float = fields.Field()
    longitude: base.Float = fields.Field()
    title: base.String = fields.Field()
    live_period: base.Integer = fields.Field()
    input_message_content: InputMessageContent = fields.Field(base=InputMessageContent)
    thumb_url: base.String = fields.Field()
    thumb_width: base.Integer = fields.Field()
    thumb_height: base.Integer = fields.Field()

    def __init__(self, *,
                 id: base.String,
                 latitude: base.Float,
                 longitude: base.Float,
                 title: base.String,
                 live_period: typing.Optional[base.Integer] = None,
                 reply_markup: typing.Optional[InlineKeyboardMarkup] = None,
                 input_message_content: typing.Optional[InputMessageContent] = None,
                 thumb_url: typing.Optional[base.String] = None,
                 thumb_width: typing.Optional[base.Integer] = None,
                 thumb_height: typing.Optional[base.Integer] = None):
        super(InlineQueryResultLocation, self).__init__(id=id, latitude=latitude, longitude=longitude,
                                                        title=title, live_period=live_period,
                                                        reply_markup=reply_markup,
                                                        input_message_content=input_message_content,
                                                        thumb_url=thumb_url, thumb_width=thumb_width,
                                                        thumb_height=thumb_height)


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
    input_message_content: InputMessageContent = fields.Field(base=InputMessageContent)
    thumb_url: base.String = fields.Field()
    thumb_width: base.Integer = fields.Field()
    thumb_height: base.Integer = fields.Field()
    foursquare_type: base.String = fields.Field()

    def __init__(self, *,
                 id: base.String,
                 latitude: base.Float,
                 longitude: base.Float,
                 title: base.String,
                 address: base.String,
                 foursquare_id: typing.Optional[base.String] = None,
                 reply_markup: typing.Optional[InlineKeyboardMarkup] = None,
                 input_message_content: typing.Optional[InputMessageContent] = None,
                 thumb_url: typing.Optional[base.String] = None,
                 thumb_width: typing.Optional[base.Integer] = None,
                 thumb_height: typing.Optional[base.Integer] = None,
                 foursquare_type: typing.Optional[base.String] = None):
        super(InlineQueryResultVenue, self).__init__(id=id, latitude=latitude, longitude=longitude,
                                                     title=title, address=address, foursquare_id=foursquare_id,
                                                     reply_markup=reply_markup,
                                                     input_message_content=input_message_content, thumb_url=thumb_url,
                                                     thumb_width=thumb_width, thumb_height=thumb_height,
                                                     foursquare_type=foursquare_type)


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

    def __init__(self, *,
                 id: base.String,
                 phone_number: base.String,
                 first_name: base.String,
                 last_name: typing.Optional[base.String] = None,
                 reply_markup: typing.Optional[InlineKeyboardMarkup] = None,
                 input_message_content: typing.Optional[InputMessageContent] = None,
                 thumb_url: typing.Optional[base.String] = None,
                 thumb_width: typing.Optional[base.Integer] = None,
                 thumb_height: typing.Optional[base.Integer] = None,
                 foursquare_type: typing.Optional[base.String] = None):
        super(InlineQueryResultContact, self).__init__(id=id, phone_number=phone_number,
                                                       first_name=first_name, last_name=last_name,
                                                       reply_markup=reply_markup,
                                                       input_message_content=input_message_content, thumb_url=thumb_url,
                                                       thumb_width=thumb_width, thumb_height=thumb_height,
                                                       foursquare_type=foursquare_type)


class InlineQueryResultGame(InlineQueryResult):
    """
    Represents a Game.

    Note: This will only work in Telegram versions released after October 1, 2016.
    Older clients will not display any inline results if a game result is among them.

    https://core.telegram.org/bots/api#inlinequeryresultgame
    """
    type: base.String = fields.Field(alias='type', default='game')
    game_short_name: base.String = fields.Field()

    def __init__(self, *,
                 id: base.String,
                 game_short_name: base.String,
                 reply_markup: typing.Optional[InlineKeyboardMarkup] = None):
        super(InlineQueryResultGame, self).__init__(id=id, game_short_name=game_short_name,
                                                    reply_markup=reply_markup)


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

    def __init__(self, *,
                 id: base.String,
                 photo_file_id: base.String,
                 title: typing.Optional[base.String] = None,
                 description: typing.Optional[base.String] = None,
                 caption: typing.Optional[base.String] = None,
                 parse_mode: typing.Optional[base.String] = None,
                 reply_markup: typing.Optional[InlineKeyboardMarkup] = None,
                 input_message_content: typing.Optional[InputMessageContent] = None):
        super(InlineQueryResultCachedPhoto, self).__init__(id=id, photo_file_id=photo_file_id, title=title,
                                                           description=description, caption=caption,
                                                           parse_mode=parse_mode, reply_markup=reply_markup,
                                                           input_message_content=input_message_content)


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

    def __init__(self, *,
                 id: base.String,
                 gif_file_id: base.String,
                 title: typing.Optional[base.String] = None,
                 caption: typing.Optional[base.String] = None,
                 parse_mode: typing.Optional[base.String] = None,
                 reply_markup: typing.Optional[InlineKeyboardMarkup] = None,
                 input_message_content: typing.Optional[InputMessageContent] = None):
        super(InlineQueryResultCachedGif, self).__init__(id=id, gif_file_id=gif_file_id,
                                                         title=title, caption=caption,
                                                         parse_mode=parse_mode, reply_markup=reply_markup,
                                                         input_message_content=input_message_content)


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

    def __init__(self, *,
                 id: base.String,
                 mpeg4_file_id: base.String,
                 title: typing.Optional[base.String] = None,
                 caption: typing.Optional[base.String] = None,
                 parse_mode: typing.Optional[base.String] = None,
                 reply_markup: typing.Optional[InlineKeyboardMarkup] = None,
                 input_message_content: typing.Optional[InputMessageContent] = None):
        super(InlineQueryResultCachedMpeg4Gif, self).__init__(id=id, mpeg4_file_id=mpeg4_file_id,
                                                              title=title, caption=caption,
                                                              parse_mode=parse_mode, reply_markup=reply_markup,
                                                              input_message_content=input_message_content)


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

    def __init__(self, *,
                 id: base.String,
                 sticker_file_id: base.String,
                 reply_markup: typing.Optional[InlineKeyboardMarkup] = None,
                 input_message_content: typing.Optional[InputMessageContent] = None):
        super(InlineQueryResultCachedSticker, self).__init__(id=id, sticker_file_id=sticker_file_id,
                                                             reply_markup=reply_markup,
                                                             input_message_content=input_message_content)


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

    def __init__(self, *,
                 id: base.String,
                 title: base.String,
                 document_file_id: base.String,
                 description: typing.Optional[base.String] = None,
                 caption: typing.Optional[base.String] = None,
                 parse_mode: typing.Optional[base.String] = None,
                 reply_markup: typing.Optional[InlineKeyboardMarkup] = None,
                 input_message_content: typing.Optional[InputMessageContent] = None):
        super(InlineQueryResultCachedDocument, self).__init__(id=id, title=title,
                                                              document_file_id=document_file_id,
                                                              description=description, caption=caption,
                                                              parse_mode=parse_mode, reply_markup=reply_markup,
                                                              input_message_content=input_message_content)


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

    def __init__(self, *,
                 id: base.String,
                 video_file_id: base.String,
                 title: base.String,
                 description: typing.Optional[base.String] = None,
                 caption: typing.Optional[base.String] = None,
                 parse_mode: typing.Optional[base.String] = None,
                 reply_markup: typing.Optional[InlineKeyboardMarkup] = None,
                 input_message_content: typing.Optional[InputMessageContent] = None):
        super(InlineQueryResultCachedVideo, self).__init__(id=id, video_file_id=video_file_id, title=title,
                                                           description=description, caption=caption,
                                                           parse_mode=parse_mode, reply_markup=reply_markup,
                                                           input_message_content=input_message_content)


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

    def __init__(self, *,
                 id: base.String,
                 voice_file_id: base.String,
                 title: base.String,
                 caption: typing.Optional[base.String] = None,
                 parse_mode: typing.Optional[base.String] = None,
                 reply_markup: typing.Optional[InlineKeyboardMarkup] = None,
                 input_message_content: typing.Optional[InputMessageContent] = None):
        super(InlineQueryResultCachedVoice, self).__init__(id=id, voice_file_id=voice_file_id,
                                                           title=title, caption=caption,
                                                           parse_mode=parse_mode, reply_markup=reply_markup,
                                                           input_message_content=input_message_content)


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

    def __init__(self, *,
                 id: base.String,
                 audio_file_id: base.String,
                 caption: typing.Optional[base.String] = None,
                 parse_mode: typing.Optional[base.String] = None,
                 reply_markup: typing.Optional[InlineKeyboardMarkup] = None,
                 input_message_content: typing.Optional[InputMessageContent] = None):
        super(InlineQueryResultCachedAudio, self).__init__(id=id, audio_file_id=audio_file_id,
                                                           caption=caption, parse_mode=parse_mode,
                                                           reply_markup=reply_markup,
                                                           input_message_content=input_message_content)
