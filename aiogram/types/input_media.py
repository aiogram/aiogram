import io
import secrets
import typing

from . import base
from . import fields
from .input_file import InputFile
from .message_entity import MessageEntity

ATTACHMENT_PREFIX = 'attach://'


class InputMedia(base.TelegramObject):
    """
    This object represents the content of a media message to be sent. It should be one of
     - InputMediaAnimation
     - InputMediaDocument
     - InputMediaAudio
     - InputMediaPhoto
     - InputMediaVideo

    That is only base class.

    https://core.telegram.org/bots/api#inputmedia
    """
    type: base.String = fields.Field(default='photo')
    media: base.String = fields.Field(alias='media', on_change='_media_changed')
    thumb: typing.Union[base.InputFile, base.String] = fields.Field(alias='thumb', on_change='_thumb_changed')
    caption: base.String = fields.Field()
    parse_mode: base.String = fields.Field()

    def __init__(self, *args, **kwargs):
        self._thumb_file = None
        self._media_file = None

        media = kwargs.pop('media', None)
        if isinstance(media, (io.IOBase, InputFile)):
            self.file = media
        elif media is not None:
            self.media = media

        thumb = kwargs.pop('thumb', None)
        if isinstance(thumb, (io.IOBase, InputFile)):
            self.thumb_file = thumb
        elif thumb is not None:
            self.thumb = thumb

        super(InputMedia, self).__init__(*args, **kwargs)

        try:
            if self.parse_mode is None and self.bot and self.bot.parse_mode:
                self.parse_mode = self.bot.parse_mode
        except RuntimeError:
            pass

    @property
    def file(self):
        return self._media_file

    @file.setter
    def file(self, file: io.IOBase):
        self.media = 'attach://' + secrets.token_urlsafe(16)
        self._media_file = file

    @file.deleter
    def file(self):
        self.media = None
        self._media_file = None

    def _media_changed(self, value):
        if value is None or isinstance(value, str) and not value.startswith('attach://'):
            self._media_file = None

    @property
    def thumb_file(self):
        return self._thumb_file

    @thumb_file.setter
    def thumb_file(self, file: io.IOBase):
        self.thumb = 'attach://' + secrets.token_urlsafe(16)
        self._thumb_file = file

    @thumb_file.deleter
    def thumb_file(self):
        self.thumb = None
        self._thumb_file = None

    def _thumb_changed(self, value):
        if value is None or isinstance(value, str) and not value.startswith('attach://'):
            self._thumb_file = None

    def get_files(self):
        if self._media_file:
            yield self.media[9:], self._media_file
        if self._thumb_file:
            yield self.thumb[9:], self._thumb_file


class InputMediaAnimation(InputMedia):
    """
    Represents an animation file (GIF or H.264/MPEG-4 AVC video without sound) to be sent.

    https://core.telegram.org/bots/api#inputmediaanimation
    """

    width: base.Integer = fields.Field()
    height: base.Integer = fields.Field()
    duration: base.Integer = fields.Field()

    def __init__(
            self,
            media: base.InputFile,
            thumb: typing.Union[base.InputFile, base.String] = None,
            caption: base.String = None,
            width: base.Integer = None,
            height: base.Integer = None,
            duration: base.Integer = None,
            parse_mode: base.String = None,
            caption_entities: typing.Optional[typing.List[MessageEntity]] = None,
            **kwargs,
    ):
        super().__init__(
            type='animation', media=media, thumb=thumb, caption=caption, width=width,
            height=height, duration=duration, parse_mode=parse_mode,
            caption_entities=caption_entities, conf=kwargs,
        )


class InputMediaDocument(InputMedia):
    """
    Represents a general file to be sent.

    https://core.telegram.org/bots/api#inputmediadocument
    """

    def __init__(
            self,
            media: base.InputFile,
            thumb: typing.Union[base.InputFile, base.String, None] = None,
            caption: base.String = None,
            parse_mode: base.String = None,
            caption_entities: typing.Optional[typing.List[MessageEntity]] = None,
            disable_content_type_detection: typing.Optional[base.Boolean] = None,
            **kwargs,
    ):
        super().__init__(
            type='document', media=media, thumb=thumb, caption=caption,
            parse_mode=parse_mode, caption_entities=caption_entities,
            disable_content_type_detection=disable_content_type_detection,
            conf=kwargs,
        )


class InputMediaAudio(InputMedia):
    """
    Represents an audio file to be treated as music to be sent.

    https://core.telegram.org/bots/api#inputmediaaudio
    """

    duration: base.Integer = fields.Field()
    performer: base.String = fields.Field()
    title: base.String = fields.Field()

    def __init__(
            self,
            media: base.InputFile,
            thumb: typing.Union[base.InputFile, base.String] = None,
            caption: base.String = None,
            duration: base.Integer = None,
            performer: base.String = None,
            title: base.String = None,
            parse_mode: base.String = None,
            caption_entities: typing.Optional[typing.List[MessageEntity]] = None,
            **kwargs,
    ):
        super().__init__(
            type='audio', media=media, thumb=thumb, caption=caption,
            duration=duration, performer=performer, title=title,
            parse_mode=parse_mode, caption_entities=caption_entities, conf=kwargs,
        )


class InputMediaPhoto(InputMedia):
    """
    Represents a photo to be sent.

    https://core.telegram.org/bots/api#inputmediaphoto
    """

    def __init__(
            self,
            media: base.InputFile,
            caption: base.String = None,
            parse_mode: base.String = None,
            caption_entities: typing.Optional[typing.List[MessageEntity]] = None,
            **kwargs,
    ):
        super().__init__(
            type='photo', media=media, caption=caption, parse_mode=parse_mode,
            caption_entities=caption_entities, conf=kwargs,
        )


class InputMediaVideo(InputMedia):
    """
    Represents a video to be sent.

    https://core.telegram.org/bots/api#inputmediavideo
    """
    width: base.Integer = fields.Field()
    height: base.Integer = fields.Field()
    duration: base.Integer = fields.Field()
    supports_streaming: base.Boolean = fields.Field()

    def __init__(
            self,
            media: base.InputFile,
            thumb: typing.Union[base.InputFile, base.String] = None,
            caption: base.String = None,
            width: base.Integer = None,
            height: base.Integer = None,
            duration: base.Integer = None,
            parse_mode: base.String = None,
            caption_entities: typing.Optional[typing.List[MessageEntity]] = None,
            supports_streaming: base.Boolean = None,
            **kwargs,
    ):
        super().__init__(
            type='video', media=media, thumb=thumb, caption=caption,
            width=width, height=height, duration=duration,
            parse_mode=parse_mode, caption_entities=caption_entities,
            supports_streaming=supports_streaming, conf=kwargs
        )


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
            # elif media_type == 'document':
            #     media = InputMediaDocument(**media)
            # elif media_type == 'audio':
            #     media = InputMediaAudio(**media)
            # elif media_type == 'animation':
            #     media = InputMediaAnimation(**media)
            else:
                raise TypeError(f"Invalid media type '{media_type}'!")

        elif not isinstance(media, InputMedia):
            raise TypeError(f"Media must be an instance of InputMedia or dict, not {type(media).__name__}")

        elif media.type in ('document', 'audio', 'animation'):
            raise ValueError(f"This type of media is not supported by media groups!")

        self.media.append(media)

    '''
    def attach_animation(self, animation: base.InputFile,
                         thumb: typing.Union[base.InputFile, base.String] = None,
                         caption: base.String = None,
                         width: base.Integer = None, height: base.Integer = None, duration: base.Integer = None,
                         parse_mode: base.Boolean = None):
        """
        Attach animation

        :param animation:
        :param thumb:
        :param caption:
        :param width:
        :param height:
        :param duration:
        :param parse_mode:
        """
        if not isinstance(animation, InputMedia):
            animation = InputMediaAnimation(media=animation, thumb=thumb, caption=caption,
                                            width=width, height=height, duration=duration,
                                            parse_mode=parse_mode)
        self.attach(animation)

    def attach_audio(self, audio: base.InputFile,
                     thumb: typing.Union[base.InputFile, base.String] = None,
                     caption: base.String = None,
                     width: base.Integer = None, height: base.Integer = None,
                     duration: base.Integer = None,
                     performer: base.String = None,
                     title: base.String = None,
                     parse_mode: base.String = None):
        """
        Attach animation

        :param audio:
        :param thumb:
        :param caption:
        :param width:
        :param height:
        :param duration:
        :param performer:
        :param title:
        :param parse_mode:
        """
        if not isinstance(audio, InputMedia):
            audio = InputMediaAudio(media=audio, thumb=thumb, caption=caption,
                                    width=width, height=height, duration=duration,
                                    performer=performer, title=title,
                                    parse_mode=parse_mode)
        self.attach(audio)

    def attach_document(self, document: base.InputFile, thumb: typing.Union[base.InputFile, base.String] = None,
                        caption: base.String = None, parse_mode: base.String = None):
        """
        Attach document

        :param parse_mode:
        :param caption:
        :param thumb:
        :param document:
        """
        if not isinstance(document, InputMedia):
            document = InputMediaDocument(media=document, thumb=thumb, caption=caption, parse_mode=parse_mode)
        self.attach(document)
    '''

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
                     thumb: typing.Union[base.InputFile, base.String] = None,
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
            video = InputMediaVideo(media=video, thumb=thumb, caption=caption,
                                    width=width, height=height, duration=duration)
        self.attach(video)

    def to_python(self) -> typing.List:
        """
        Get object as JSON serializable

        :return:
        """
        # self.clean()
        result = []
        for obj in self.media:
            if isinstance(obj, base.TelegramObject):
                obj = obj.to_python()
            result.append(obj)
        return result

    def get_files(self):
        for inputmedia in self.media:
            if not isinstance(inputmedia, InputMedia) or not inputmedia.file:
                continue
            yield from inputmedia.get_files()
