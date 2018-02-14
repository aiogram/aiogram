import io
import secrets
import typing

from . import base
from . import fields
from .input_file import InputFile

ATTACHMENT_PREFIX = 'attach://'


class InputMedia(base.TelegramObject):
    """
    This object represents the content of a media message to be sent. It should be one of
     - InputMediaPhoto
     - InputMediaVideo

    That is only base class.

    https://core.telegram.org/bots/api#inputmedia
    """
    type: base.String = fields.Field(default='photo')
    media: base.String = fields.Field()
    caption: base.String = fields.Field()
    parse_mode: base.Boolean = fields.Field()

    def __init__(self, *args, **kwargs):
        super(InputMedia, self).__init__(*args, **kwargs)
        try:
            if self.parse_mode is None and self.bot.parse_mode:
                self.parse_mode = self.bot.parse_mode
        except RuntimeError:
            pass

    @property
    def file(self):
        return getattr(self, '_file', None)

    @file.setter
    def file(self, file: io.IOBase):
        setattr(self, '_file', file)
        attachment_key = self.attachment_key = secrets.token_urlsafe(16)
        self.media = ATTACHMENT_PREFIX + attachment_key

    @property
    def attachment_key(self):
        return self.conf.get('attachment_key', None)

    @attachment_key.setter
    def attachment_key(self, value):
        self.conf['attachment_key'] = value


class InputMediaPhoto(InputMedia):
    """
    Represents a photo to be sent.

    https://core.telegram.org/bots/api#inputmediaphoto
    """

    def __init__(self, media: base.InputFile, caption: base.String = None, parse_mode: base.Boolean = None, **kwargs):
        super(InputMediaPhoto, self).__init__(type='photo', media=media, caption=caption, parse_mode=parse_mode,
                                              conf=kwargs)

        if isinstance(media, (io.IOBase, InputFile)):
            self.file = media


class InputMediaVideo(InputMedia):
    """
    Represents a video to be sent.

    https://core.telegram.org/bots/api#inputmediavideo
    """
    width: base.Integer = fields.Field()
    height: base.Integer = fields.Field()
    duration: base.Integer = fields.Field()
    supports_streaming: base.Boolean = fields.Field()

    def __init__(self, media: base.InputFile, caption: base.String = None,
                 width: base.Integer = None, height: base.Integer = None, duration: base.Integer = None,
                 parse_mode: base.Boolean = None,
                 supports_streaming: base.Boolean = None, **kwargs):
        super(InputMediaVideo, self).__init__(type='video', media=media, caption=caption,
                                              width=width, height=height, duration=duration,
                                              parse_mode=parse_mode,
                                              supports_streaming=supports_streaming, conf=kwargs)

        if isinstance(media, (io.IOBase, InputFile)):
            self.file = media


class MediaGroup(base.TelegramObject):
    """
    Helper for sending media group
    """

    def __init__(self, medias: typing.Optional[typing.List[typing.Union[InputMedia, typing.Dict]]] = None):
        super(MediaGroup, self).__init__()
        self.media = []

        if medias:
            self.attach_many(*medias)

    def attach_many(self, *medias: typing.Union[InputMedia, typing.Dict]):
        """
        Attach list of media

        :param medias:
        """
        for media in medias:
            self.attach(media)

    def attach(self, media: typing.Union[InputMedia, typing.Dict]):
        """
        Attach media

        :param media:
        """
        if isinstance(media, dict):
            if 'type' not in media:
                raise ValueError(f"Invalid media!")

            media_type = media['type']
            if media_type == 'photo':
                media = InputMediaPhoto(**media)
            elif media_type == 'video':
                media = InputMediaVideo(**media)
            else:
                raise TypeError(f"Invalid media type '{media_type}'!")

        elif not isinstance(media, InputMedia):
            raise TypeError(f"Media must be an instance of InputMedia or dict, not {type(media).__name__}")

        self.media.append(media)

    def attach_photo(self, photo: typing.Union[InputMediaPhoto, base.InputFile],
                     caption: base.String = None):
        """
        Attach photo

        :param photo:
        :param caption:
        """
        if not isinstance(photo, InputMedia):
            photo = InputMediaPhoto(media=photo, caption=caption)
        self.attach(photo)

    def attach_video(self, video: typing.Union[InputMediaVideo, base.InputFile],
                     caption: base.String = None,
                     width: base.Integer = None, height: base.Integer = None, duration: base.Integer = None):
        """
        Attach video

        :param video:
        :param caption:
        :param width:
        :param height:
        :param duration:
        """
        if not isinstance(video, InputMedia):
            video = InputMediaVideo(media=video, caption=caption,
                                    width=width, height=height, duration=duration)
        self.attach(video)

    def to_python(self) -> typing.List:
        """
        Get object as JSON serializable

        :return:
        """
        self.clean()
        result = []
        for obj in self.media:
            if isinstance(obj, base.TelegramObject):
                obj = obj.to_python()
            result.append(obj)
        return result

    def get_files(self):
        return {inputmedia.attachment_key: inputmedia.file
                for inputmedia in self.media
                if isinstance(inputmedia, InputMedia) and inputmedia.file}
