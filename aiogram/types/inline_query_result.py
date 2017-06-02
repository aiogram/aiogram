from .base import Serializable
from .inline_keyboard import InlineKeyboardMarkup


class InputMessageContent(Serializable):
    def to_json(self):
        return {k: v.to_json() if hasattr(v, 'to_json') else v for k, v in self.__dict__.items() if
                not k.startswith('_')}


class InlineQueryResult(InputMessageContent):
    pass


class InlineQueryResultArticle(InlineQueryResult):
    def __init__(self, type: str, id: str, title: str, input_message_content: InputMessageContent,
                 reply_markup: InlineKeyboardMarkup = None, url: str = None, hide_url: bool = None,
                 description: str = None, thumb_url: str = None, thumb_width: int = None, thumb_height: int = None):
        self.type: str = type
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
    def __init__(self, type: str, id: str, photo_url: str, thumb_url: str, photo_width: int = None,
                 photo_height: int = None, title: str = None, description: str = None, caption: str = None,
                 reply_markup: InlineKeyboardMarkup = None, input_message_content: InputMessageContent = None):
        self.type: str = type
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
    def __init__(self, type: str, id: str, gif_url: str, thumb_url: str, gif_width: int = None, gif_height: int = None,
                 gif_duration: int = None, title: str = None, caption: str = None,
                 reply_markup: InlineKeyboardMarkup = None, input_message_content: InputMessageContent = None):
        self.type: str = type
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
    def __init__(self, type: str, id: str, mpeg4_url: str, thumb_url: str, mpeg4_width: int = None,
                 mpeg4_height: int = None, mpeg4_duration: int = None, title: str = None, caption: str = None,
                 reply_markup: InlineKeyboardMarkup = None, input_message_content: InputMessageContent = None):
        self.type: str = type
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
    def __init__(self, type: str, id: str, video_url: str, mime_type: str, thumb_url: str, title: str,
                 caption: str = None, video_width: int = None, video_height: int = None, video_duration: int = None,
                 description: str = None, reply_markup: InlineKeyboardMarkup = None,
                 input_message_content: InputMessageContent = None):
        self.type: str = type
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
    def __init__(self, type: str, id: str, audio_url: str, title: str, caption: str = None, performer: str = None,
                 audio_duration: int = None, reply_markup: InlineKeyboardMarkup = None,
                 input_message_content: InputMessageContent = None):
        self.type: str = type
        self.id: str = id
        self.audio_url: str = audio_url
        self.title: str = title
        self.caption: str = caption
        self.performer: str = performer
        self.audio_duration: int = audio_duration
        self.reply_markup: InlineKeyboardMarkup = reply_markup
        self.input_message_content: InputMessageContent = input_message_content


class InlineQueryResultVoice(InlineQueryResult):
    def __init__(self, type: str, id: str, voice_url: str, title: str, caption: str = None, voice_duration: int = None,
                 reply_markup: InlineKeyboardMarkup = None, input_message_content: InputMessageContent = None):
        self.type: str = type
        self.id: str = id
        self.voice_url: str = voice_url
        self.title: str = title
        self.caption: str = caption
        self.voice_duration: int = voice_duration
        self.reply_markup: InlineKeyboardMarkup = reply_markup
        self.input_message_content: InputMessageContent = input_message_content


class InlineQueryResultDocument(InlineQueryResult):
    def __init__(self, type: str, id: str, title: str, document_url: str, mime_type: str, caption: str = None,
                 description: str = None, reply_markup: InlineKeyboardMarkup = None,
                 input_message_content: InputMessageContent = None, thumb_url: str = None, thumb_width: int = None,
                 thumb_height: int = None):
        self.type: str = type
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
    def __init__(self, type: str, id: str, latitude: float, longitude: float, title: str,
                 reply_markup: InlineKeyboardMarkup = None, input_message_content: InputMessageContent = None,
                 thumb_url: str = None, thumb_width: int = None, thumb_height: int = None):
        self.type: str = type
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
    def __init__(self, type: str, id: str, latitude: float, longitude: float, title: str, address: str,
                 foursquare_id: str = None, reply_markup: InlineKeyboardMarkup = None,
                 input_message_content: InputMessageContent = None, thumb_url: str = None, thumb_width: int = None,
                 thumb_height: int = None):
        self.type: str = type
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
    def __init__(self, type: str, id: str, phone_number: str, first_name: str, last_name: str = None,
                 reply_markup: InlineKeyboardMarkup = None, input_message_content: InputMessageContent = None,
                 thumb_url: str = None, thumb_width: int = None, thumb_height: int = None):
        self.type: str = type
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
    def __init__(self, type: str, id: str, game_short_name: str, reply_markup: InlineKeyboardMarkup = None):
        self.type: str = type
        self.id: str = id
        self.game_short_name: str = game_short_name
        self.reply_markup: InlineKeyboardMarkup = reply_markup


class InlineQueryResultCachedPhoto(InlineQueryResult):
    def __init__(self, type: str, id: str, photo_file_id: str, title: str = None, description: str = None,
                 caption: str = None, reply_markup: InlineKeyboardMarkup = None,
                 input_message_content: InputMessageContent = None):
        self.type: str = type
        self.id: str = id
        self.photo_file_id: str = photo_file_id
        self.title: str = title
        self.description: str = description
        self.caption: str = caption
        self.reply_markup: InlineKeyboardMarkup = reply_markup
        self.input_message_content: InputMessageContent = input_message_content


class InlineQueryResultCachedGif(InlineQueryResult):
    def __init__(self, type: str, id: str, gif_file_id: str, title: str = None, caption: str = None,
                 reply_markup: InlineKeyboardMarkup = None, input_message_content: InputMessageContent = None):
        self.type: str = type
        self.id: str = id
        self.gif_file_id: str = gif_file_id
        self.title: str = title
        self.caption: str = caption
        self.reply_markup: InlineKeyboardMarkup = reply_markup
        self.input_message_content: InputMessageContent = input_message_content


class InlineQueryResultCachedMpeg4Gif(InlineQueryResult):
    def __init__(self, type: str, id: str, mpeg4_file_id: str, title: str = None, caption: str = None,
                 reply_markup: InlineKeyboardMarkup = None, input_message_content: InputMessageContent = None):
        self.type: str = type
        self.id: str = id
        self.mpeg4_file_id: str = mpeg4_file_id
        self.title: str = title
        self.caption: str = caption
        self.reply_markup: InlineKeyboardMarkup = reply_markup
        self.input_message_content: InputMessageContent = input_message_content


class InlineQueryResultCachedSticker(InlineQueryResult):
    def __init__(self, type: str, id: str, sticker_file_id: str, reply_markup: InlineKeyboardMarkup = None,
                 input_message_content: InputMessageContent = None):
        self.type: str = type
        self.id: str = id
        self.sticker_file_id: str = sticker_file_id
        self.reply_markup: InlineKeyboardMarkup = reply_markup
        self.input_message_content: InputMessageContent = input_message_content


class InlineQueryResultCachedDocument(InlineQueryResult):
    def __init__(self, type: str, id: str, title: str, document_file_id: str, description: str = None,
                 caption: str = None, reply_markup: InlineKeyboardMarkup = None,
                 input_message_content: InputMessageContent = None):
        self.type: str = type
        self.id: str = id
        self.title: str = title
        self.document_file_id: str = document_file_id
        self.description: str = description
        self.caption: str = caption
        self.reply_markup: InlineKeyboardMarkup = reply_markup
        self.input_message_content: InputMessageContent = input_message_content


class InlineQueryResultCachedVideo(InlineQueryResult):
    def __init__(self, type: str, id: str, video_file_id: str, title: str, description: str = None, caption: str = None,
                 reply_markup: InlineKeyboardMarkup = None, input_message_content: InputMessageContent = None):
        self.type: str = type
        self.id: str = id
        self.video_file_id: str = video_file_id
        self.title: str = title
        self.description: str = description
        self.caption: str = caption
        self.reply_markup: InlineKeyboardMarkup = reply_markup
        self.input_message_content: InputMessageContent = input_message_content


class InlineQueryResultCachedVoice(InlineQueryResult):
    def __init__(self, type: str, id: str, voice_file_id: str, title: str, caption: str = None,
                 reply_markup: InlineKeyboardMarkup = None, input_message_content: InputMessageContent = None):
        self.type: str = type
        self.id: str = id
        self.voice_file_id: str = voice_file_id
        self.title: str = title
        self.caption: str = caption
        self.reply_markup: InlineKeyboardMarkup = reply_markup
        self.input_message_content: InputMessageContent = input_message_content


class InlineQueryResultCachedAudio(InlineQueryResult):
    def __init__(self, type: str, id: str, audio_file_id: str, caption: str = None,
                 reply_markup: InlineKeyboardMarkup = None, input_message_content: InputMessageContent = None):
        self.type: str = type
        self.id: str = id
        self.audio_file_id: str = audio_file_id
        self.caption: str = caption
        self.reply_markup: InlineKeyboardMarkup = reply_markup
        self.input_message_content: InputMessageContent = input_message_content


class InputTextMessageContent(InputMessageContent):
    def __init__(self, message_text: str, parse_mode: str = None, disable_web_page_preview: bool = None):
        self.message_text: str = message_text
        self.parse_mode: str = parse_mode
        self.disable_web_page_preview: bool = disable_web_page_preview


class InputLocationMessageContent(InputMessageContent):
    def __init__(self, latitude: float, longitude: float):
        self.latitude: float = latitude
        self.longitude: float = longitude


class InputVenueMessageContent(InputMessageContent):
    def __init__(self, latitude: float, longitude: float, title: str, address: str, foursquare_id: str = None):
        self.latitude: float = latitude
        self.longitude: float = longitude
        self.title: str = title
        self.address: str = address
        self.foursquare_id: str = foursquare_id


class InputContactMessageContent(InputMessageContent):
    def __init__(self, phone_number: str, first_name: str, last_name: str = None):
        self.phone_number: str = phone_number
        self.first_name: str = first_name
        self.last_name: str = last_name
