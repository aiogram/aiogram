from .base import Serializable
from .inline_keyboard import InlineKeyboardMarkup


class InputMessageContent(Serializable):
    """
    This object represents the content of a message to be sent as a result of an inline query. 
    
    Telegram clients currently support the following 4 types:

        :class:`aiogram.types.InputTextMessageContent`
        :class:`aiogram.types.InputLocationMessageContent`
        :class:`aiogram.types.InputVenueMessageContent`
        :class:`aiogram.types.InputContactMessageContent`
    """
    def to_json(self):
        return {k: v.to_json() if hasattr(v, 'to_json') else v for k, v in self.__dict__.items() if
                v is not None and not k.startswith('_')}


class InlineQueryResult(InputMessageContent):
    """
    This object represents one result of an inline query.
    
    Telegram clients currently support results of the following 20 types:

        :class:`aiogram.types.InlineQueryResultCachedAudio`

        :class:`aiogram.types.InlineQueryResultCachedDocument`

        :class:`aiogram.types.InlineQueryResultCachedGif`

        :class:`aiogram.types.InlineQueryResultCachedMpeg4Gif`

        :class:`aiogram.types.InlineQueryResultCachedPhoto`

        :class:`aiogram.types.InlineQueryResultCachedSticker`

        :class:`aiogram.types.InlineQueryResultCachedVideo`

        :class:`aiogram.types.InlineQueryResultCachedVoice`

        :class:`aiogram.types.InlineQueryResultArticle`

        :class:`aiogram.types.InlineQueryResultAudio`

        :class:`aiogram.types.InlineQueryResultContact`

        :class:`aiogram.types.InlineQueryResultGame`

        :class:`aiogram.types.InlineQueryResultDocument`

        :class:`aiogram.types.InlineQueryResultGif`

        :class:`aiogram.types.InlineQueryResultLocation`

        :class:`aiogram.types.InlineQueryResultMpeg4Gif`

        :class:`aiogram.types.InlineQueryResultPhoto`

        :class:`aiogram.types.InlineQueryResultVenue`

        :class:`aiogram.types.InlineQueryResultVideo`

        :class:`aiogram.types.InlineQueryResultVoice`

    """
    pass


class InlineQueryResultArticle(InlineQueryResult):
    """
    Represents a link to an article or web page.
    
    https://core.telegram.org/bots/api#inlinequeryresultarticle
    """
    def __init__(self, id: str, title: str, input_message_content: InputMessageContent,
                 reply_markup: InlineKeyboardMarkup = None, url: str = None, hide_url: bool = None,
                 description: str = None, thumb_url: str = None, thumb_width: int = None, thumb_height: int = None):
        self.type = 'article'
        self.id: str = id
        self.title: str = title
        self.input_message_content: InputMessageContent = input_message_content
        self.reply_markup: InlineKeyboardMarkup = reply_markup
        self.url: str = url
        self.hide_url: bool = hide_url
        self.description: str = description
        self.thumb_url: str = thumb_url
        self.thumb_width: int = thumb_width
        self.thumb_height: int = thumb_height


class InlineQueryResultPhoto(InlineQueryResult):
    """
    Represents a link to a photo. By default, this photo will be sent by the user with optional caption. 
    
    Alternatively, you can use input_message_content to send a message with the specified content instead 
    of the photo.
    
    https://core.telegram.org/bots/api#inlinequeryresultphoto
    """
    def __init__(self, id: str, photo_url: str, thumb_url: str, photo_width: int = None,
                 photo_height: int = None, title: str = None, description: str = None, caption: str = None,
                 reply_markup: InlineKeyboardMarkup = None, input_message_content: InputMessageContent = None):
        self.type = 'photo'
        self.id: str = id
        self.photo_url: str = photo_url
        self.thumb_url: str = thumb_url
        self.photo_width: int = photo_width
        self.photo_height: int = photo_height
        self.title: str = title
        self.description: str = description
        self.caption: str = caption
        self.reply_markup: InlineKeyboardMarkup = reply_markup
        self.input_message_content: InputMessageContent = input_message_content


class InlineQueryResultGif(InlineQueryResult):
    """
    Represents a link to an animated GIF file.
     
    By default, this animated GIF file will be sent by the user with optional caption. 
    
    Alternatively, you can use input_message_content to send a message with the specified 
    content instead of the animation.
    
    https://core.telegram.org/bots/api#inlinequeryresultgif
    """
    def __init__(self, id: str, gif_url: str, thumb_url: str, gif_width: int = None, gif_height: int = None,
                 gif_duration: int = None, title: str = None, caption: str = None,
                 reply_markup: InlineKeyboardMarkup = None, input_message_content: InputMessageContent = None):
        self.type = 'gif'
        self.id: str = id
        self.gif_url: str = gif_url
        self.gif_width: int = gif_width
        self.gif_height: int = gif_height
        self.gif_duration: int = gif_duration
        self.thumb_url: str = thumb_url
        self.title: str = title
        self.caption: str = caption
        self.reply_markup: InlineKeyboardMarkup = reply_markup
        self.input_message_content: InputMessageContent = input_message_content


class InlineQueryResultMpeg4Gif(InlineQueryResult):
    """
    Represents a link to a video animation (H.264/MPEG-4 AVC video without sound). 
    
    By default, this animated MPEG-4 file will be sent by the user with optional caption. 
    
    Alternatively, you can use input_message_content to send a message with the specified content 
    instead of the animation.
    
    https://core.telegram.org/bots/api#inlinequeryresultmpeg4gif
    """
    def __init__(self, id: str, mpeg4_url: str, thumb_url: str, mpeg4_width: int = None,
                 mpeg4_height: int = None, mpeg4_duration: int = None, title: str = None, caption: str = None,
                 reply_markup: InlineKeyboardMarkup = None, input_message_content: InputMessageContent = None):
        self.type = 'mpeg4_gif'
        self.id: str = id
        self.mpeg4_url: str = mpeg4_url
        self.mpeg4_width: int = mpeg4_width
        self.mpeg4_height: int = mpeg4_height
        self.mpeg4_duration: int = mpeg4_duration
        self.thumb_url: str = thumb_url
        self.title: str = title
        self.caption: str = caption
        self.reply_markup: InlineKeyboardMarkup = reply_markup
        self.input_message_content: InputMessageContent = input_message_content


class InlineQueryResultVideo(InlineQueryResult):
    """
    Represents a link to a page containing an embedded video player or a video file. 
    By default, this video file will be sent by the user with an optional caption. 
    Alternatively, you can use input_message_content to send a message with the specified content 
    instead of the video.
    
    https://core.telegram.org/bots/api#inlinequeryresultvideo
    """
    def __init__(self, id: str, video_url: str, mime_type: str, thumb_url: str, title: str,
                 caption: str = None, video_width: int = None, video_height: int = None, video_duration: int = None,
                 description: str = None, reply_markup: InlineKeyboardMarkup = None,
                 input_message_content: InputMessageContent = None):
        self.type = 'video'
        self.id: str = id
        self.video_url: str = video_url
        self.mime_type: str = mime_type
        self.thumb_url: str = thumb_url
        self.title: str = title
        self.caption: str = caption
        self.video_width: int = video_width
        self.video_height: int = video_height
        self.video_duration: int = video_duration
        self.description: str = description
        self.reply_markup: InlineKeyboardMarkup = reply_markup
        self.input_message_content: InputMessageContent = input_message_content


class InlineQueryResultAudio(InlineQueryResult):
    """
    Represents a link to an mp3 audio file. By default, this audio file will be sent by the user. Alternatively, 
    you can use input_message_content to send a message with the specified content instead of the audio.
    
    https://core.telegram.org/bots/api#inlinequeryresultaudio
    """
    def __init__(self, id: str, audio_url: str, title: str, caption: str = None, performer: str = None,
                 audio_duration: int = None, reply_markup: InlineKeyboardMarkup = None,
                 input_message_content: InputMessageContent = None):
        self.type = 'audio'
        self.id: str = id
        self.audio_url: str = audio_url
        self.title: str = title
        self.caption: str = caption
        self.performer: str = performer
        self.audio_duration: int = audio_duration
        self.reply_markup: InlineKeyboardMarkup = reply_markup
        self.input_message_content: InputMessageContent = input_message_content


class InlineQueryResultVoice(InlineQueryResult):
    """
    Represents a link to a voice recording in an .ogg container encoded with OPUS. 
    
    By default, this voice recording will be sent by the user. 
    
    Alternatively, you can use input_message_content to send a message with the specified content 
    instead of the the voice message.
    
    https://core.telegram.org/bots/api#inlinequeryresultvoice
    """
    def __init__(self, id: str, voice_url: str, title: str, caption: str = None, voice_duration: int = None,
                 reply_markup: InlineKeyboardMarkup = None, input_message_content: InputMessageContent = None):
        self.type = 'voice'
        self.id: str = id
        self.voice_url: str = voice_url
        self.title: str = title
        self.caption: str = caption
        self.voice_duration: int = voice_duration
        self.reply_markup: InlineKeyboardMarkup = reply_markup
        self.input_message_content: InputMessageContent = input_message_content


class InlineQueryResultDocument(InlineQueryResult):
    """
    Represents a link to a file. By default, this file will be sent by the user with an optional caption. 
    
    Alternatively, you can use input_message_content to send a message with the specified content 
    instead of the file. Currently, only .PDF and .ZIP files can be sent using this method.
    
    https://core.telegram.org/bots/api#inlinequeryresultdocument
    """
    def __init__(self, id: str, title: str, document_url: str, mime_type: str, caption: str = None,
                 description: str = None, reply_markup: InlineKeyboardMarkup = None,
                 input_message_content: InputMessageContent = None, thumb_url: str = None, thumb_width: int = None,
                 thumb_height: int = None):
        self.type = 'document'
        self.id: str = id
        self.title: str = title
        self.caption: str = caption
        self.document_url: str = document_url
        self.mime_type: str = mime_type
        self.description: str = description
        self.reply_markup: InlineKeyboardMarkup = reply_markup
        self.input_message_content: InputMessageContent = input_message_content
        self.thumb_url: str = thumb_url
        self.thumb_width: int = thumb_width
        self.thumb_height: int = thumb_height


class InlineQueryResultLocation(InlineQueryResult):
    """
    Represents a location on a map. By default, the location will be sent by the user. 
    Alternatively, you can use input_message_content to send a message with the specified content 
    instead of the location.
    
    https://core.telegram.org/bots/api#inlinequeryresultlocation
    """
    def __init__(self, id: str, latitude: float, longitude: float, title: str,
                 reply_markup: InlineKeyboardMarkup = None, input_message_content: InputMessageContent = None,
                 thumb_url: str = None, thumb_width: int = None, thumb_height: int = None):
        self.type = 'location'
        self.id: str = id
        self.latitude: float = latitude
        self.longitude: float = longitude
        self.title: str = title
        self.reply_markup: InlineKeyboardMarkup = reply_markup
        self.input_message_content: InputMessageContent = input_message_content
        self.thumb_url: str = thumb_url
        self.thumb_width: int = thumb_width
        self.thumb_height: int = thumb_height


class InlineQueryResultVenue(InlineQueryResult):
    """
    Represents a venue. By default, the venue will be sent by the user. 
    Alternatively, you can use input_message_content to send a message with the specified 
    content instead of the venue.
    
    https://core.telegram.org/bots/api#inlinequeryresultvenue
    """
    def __init__(self, id: str, latitude: float, longitude: float, title: str, address: str,
                 foursquare_id: str = None, reply_markup: InlineKeyboardMarkup = None,
                 input_message_content: InputMessageContent = None, thumb_url: str = None, thumb_width: int = None,
                 thumb_height: int = None):
        self.type = 'venue'
        self.id: str = id
        self.latitude: float = latitude
        self.longitude: float = longitude
        self.title: str = title
        self.address: str = address
        self.foursquare_id: str = foursquare_id
        self.reply_markup: InlineKeyboardMarkup = reply_markup
        self.input_message_content: InputMessageContent = input_message_content
        self.thumb_url: str = thumb_url
        self.thumb_width: int = thumb_width
        self.thumb_height: int = thumb_height


class InlineQueryResultContact(InlineQueryResult):
    """
    Represents a contact with a phone number. 
    
    By default, this contact will be sent by the user. 
    
    Alternatively, you can use input_message_content to send a message with the specified content instead 
    of the contact.
    
    https://core.telegram.org/bots/api#inlinequeryresultcontact
    """
    def __init__(self, id: str, phone_number: str, first_name: str, last_name: str = None,
                 reply_markup: InlineKeyboardMarkup = None, input_message_content: InputMessageContent = None,
                 thumb_url: str = None, thumb_width: int = None, thumb_height: int = None):
        self.type = 'contact'
        self.id: str = id
        self.phone_number: str = phone_number
        self.first_name: str = first_name
        self.last_name: str = last_name
        self.reply_markup: InlineKeyboardMarkup = reply_markup
        self.input_message_content: InputMessageContent = input_message_content
        self.thumb_url: str = thumb_url
        self.thumb_width: int = thumb_width
        self.thumb_height: int = thumb_height


class InlineQueryResultGame(InlineQueryResult):
    """
    Represents a Game.
    
    https://core.telegram.org/bots/api#inlinequeryresultgame
    """
    def __init__(self, id: str, game_short_name: str, reply_markup: InlineKeyboardMarkup = None):
        self.type = 'game'
        self.id: str = id
        self.game_short_name: str = game_short_name
        self.reply_markup: InlineKeyboardMarkup = reply_markup


class InlineQueryResultCachedPhoto(InlineQueryResult):
    """
    Represents a link to a photo stored on the Telegram servers. 
    
    By default, this photo will be sent by the user with an optional caption. 
    
    Alternatively, you can use input_message_content to send a message with the specified 
    content instead of the photo.
    
    https://core.telegram.org/bots/api#inlinequeryresultcachedphoto
    """
    def __init__(self, id: str, photo_file_id: str, title: str = None, description: str = None,
                 caption: str = None, reply_markup: InlineKeyboardMarkup = None,
                 input_message_content: InputMessageContent = None):
        self.type = 'photo'
        self.id: str = id
        self.photo_file_id: str = photo_file_id
        self.title: str = title
        self.description: str = description
        self.caption: str = caption
        self.reply_markup: InlineKeyboardMarkup = reply_markup
        self.input_message_content: InputMessageContent = input_message_content


class InlineQueryResultCachedGif(InlineQueryResult):
    """
    Represents a link to an animated GIF file stored on the Telegram servers. 
    
    By default, this animated GIF file will be sent by the user with an optional caption. 
    
    Alternatively, you can use input_message_content to send a message with specified content 
    instead of the animation.
    
    https://core.telegram.org/bots/api#inlinequeryresultcachedgif
    """
    def __init__(self, id: str, gif_file_id: str, title: str = None, caption: str = None,
                 reply_markup: InlineKeyboardMarkup = None, input_message_content: InputMessageContent = None):
        self.type = 'gif'
        self.id: str = id
        self.gif_file_id: str = gif_file_id
        self.title: str = title
        self.caption: str = caption
        self.reply_markup: InlineKeyboardMarkup = reply_markup
        self.input_message_content: InputMessageContent = input_message_content


class InlineQueryResultCachedMpeg4Gif(InlineQueryResult):
    """
    Represents a link to a video animation (H.264/MPEG-4 AVC video without sound) stored on the Telegram servers. 
    
    By default, this animated MPEG-4 file will be sent by the user with an optional caption. 
    
    Alternatively, you can use input_message_content to send a message with the specified content 
    instead of the animation.
    
    https://core.telegram.org/bots/api#inlinequeryresultcachedmpeg4gif
    """
    def __init__(self, id: str, mpeg4_file_id: str, title: str = None, caption: str = None,
                 reply_markup: InlineKeyboardMarkup = None, input_message_content: InputMessageContent = None):
        self.type = 'mpeg4_gif'
        self.id: str = id
        self.mpeg4_file_id: str = mpeg4_file_id
        self.title: str = title
        self.caption: str = caption
        self.reply_markup: InlineKeyboardMarkup = reply_markup
        self.input_message_content: InputMessageContent = input_message_content


class InlineQueryResultCachedSticker(InlineQueryResult):
    """
    Represents a link to a sticker stored on the Telegram servers. 
    
    By default, this sticker will be sent by the user. 
    
    Alternatively, you can use input_message_content to send a message with the specified content 
    instead of the sticker.
    
    https://core.telegram.org/bots/api#inlinequeryresultcachedsticker
    """
    def __init__(self, id: str, sticker_file_id: str, reply_markup: InlineKeyboardMarkup = None,
                 input_message_content: InputMessageContent = None):
        self.type = 'sticker'
        self.id: str = id
        self.sticker_file_id: str = sticker_file_id
        self.reply_markup: InlineKeyboardMarkup = reply_markup
        self.input_message_content: InputMessageContent = input_message_content


class InlineQueryResultCachedDocument(InlineQueryResult):
    """
    Represents a link to a file stored on the Telegram servers. 
    
    By default, this file will be sent by the user with an optional caption. 
    
    Alternatively, you can use input_message_content to send a message with the specified content 
    instead of the file.
    
    https://core.telegram.org/bots/api#inlinequeryresultcacheddocument
    """
    def __init__(self, id: str, title: str, document_file_id: str, description: str = None,
                 caption: str = None, reply_markup: InlineKeyboardMarkup = None,
                 input_message_content: InputMessageContent = None):
        self.type = 'document'
        self.id: str = id
        self.title: str = title
        self.document_file_id: str = document_file_id
        self.description: str = description
        self.caption: str = caption
        self.reply_markup: InlineKeyboardMarkup = reply_markup
        self.input_message_content: InputMessageContent = input_message_content


class InlineQueryResultCachedVideo(InlineQueryResult):
    """
    Represents a link to a video file stored on the Telegram servers. 
    By default, this video file will be sent by the user with an optional caption. 
    Alternatively, you can use input_message_content to send a message with the specified content instead 
    of the video.
    
    https://core.telegram.org/bots/api#inlinequeryresultcachedvideo
    """
    def __init__(self, id: str, video_file_id: str, title: str, description: str = None, caption: str = None,
                 reply_markup: InlineKeyboardMarkup = None, input_message_content: InputMessageContent = None):
        self.type = 'video'
        self.id: str = id
        self.video_file_id: str = video_file_id
        self.title: str = title
        self.description: str = description
        self.caption: str = caption
        self.reply_markup: InlineKeyboardMarkup = reply_markup
        self.input_message_content: InputMessageContent = input_message_content


class InlineQueryResultCachedVoice(InlineQueryResult):
    """
    Represents a link to a voice message stored on the Telegram servers. 
    
    By default, this voice message will be sent by the user. 
    
    Alternatively, you can use input_message_content to send a message with the specified content 
    instead of the voice message.
    
    https://core.telegram.org/bots/api#inlinequeryresultcachedvoice
    """
    def __init__(self, id: str, voice_file_id: str, title: str, caption: str = None,
                 reply_markup: InlineKeyboardMarkup = None, input_message_content: InputMessageContent = None):
        self.type = 'voice'
        self.id: str = id
        self.voice_file_id: str = voice_file_id
        self.title: str = title
        self.caption: str = caption
        self.reply_markup: InlineKeyboardMarkup = reply_markup
        self.input_message_content: InputMessageContent = input_message_content


class InlineQueryResultCachedAudio(InlineQueryResult):
    """
    Represents a link to an mp3 audio file stored on the Telegram servers. 
    
    By default, this audio file will be sent by the user. 
    Alternatively, you can use input_message_content to send a message with the specified content 
    instead of the audio.
    
    https://core.telegram.org/bots/api#inlinequeryresultcachedaudio
    """
    def __init__(self, id: str, audio_file_id: str, caption: str = None,
                 reply_markup: InlineKeyboardMarkup = None, input_message_content: InputMessageContent = None):
        self.type = 'audio'
        self.id: str = id
        self.audio_file_id: str = audio_file_id
        self.caption: str = caption
        self.reply_markup: InlineKeyboardMarkup = reply_markup
        self.input_message_content: InputMessageContent = input_message_content


class InputTextMessageContent(InputMessageContent):
    """
    Represents the content of a text message to be sent as the result of an inline query.
    
    https://core.telegram.org/bots/api#inputtextmessagecontent
    """
    def __init__(self, message_text: str, parse_mode: str = None, disable_web_page_preview: bool = None):
        self.message_text: str = message_text
        self.parse_mode: str = parse_mode
        self.disable_web_page_preview: bool = disable_web_page_preview


class InputLocationMessageContent(InputMessageContent):
    """
    Represents the content of a location message to be sent as the result of an inline query.

    https://core.telegram.org/bots/api#inputlocationmessagecontent
    """
    def __init__(self, latitude: float, longitude: float):
        self.latitude: float = latitude
        self.longitude: float = longitude


class InputVenueMessageContent(InputMessageContent):
    """
    Represents the content of a venue message to be sent as the result of an inline query.
    
    https://core.telegram.org/bots/api#inputvenuemessagecontent
    """
    def __init__(self, latitude: float, longitude: float, title: str, address: str, foursquare_id: str = None):
        self.latitude: float = latitude
        self.longitude: float = longitude
        self.title: str = title
        self.address: str = address
        self.foursquare_id: str = foursquare_id


class InputContactMessageContent(InputMessageContent):
    """
    Represents the content of a contact message to be sent as the result of an inline query.
    
    https://core.telegram.org/bots/api#inputcontactmessagecontent
    """
    def __init__(self, phone_number: str, first_name: str, last_name: str = None):
        self.phone_number: str = phone_number
        self.first_name: str = first_name
        self.last_name: str = last_name
