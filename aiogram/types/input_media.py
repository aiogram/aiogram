import io
import secrets
import typing

from . import base
from . import fields

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

    @property
    def file(self):
        return getattr(self, '_file', None)

    @file.setter
    def file(self, file: io.IOBase):
        # File must be not closed before sending media.
        # Read file into BytesIO
        if isinstance(file, io.BufferedIOBase):
            # Go to start of file
            if file.seekable():
                file.seek(0)
            # Read
            temp_file = io.BytesIO(file.read())
            # Reset cursor
            file.seek(0)
            # Replace variable
            file = temp_file

        setattr(self, '_file', file)
        self.media = ATTACHMENT_PREFIX + secrets.token_urlsafe(16)

    @property
    def attachment_key(self):
        if self.media.startswith(ATTACHMENT_PREFIX):
            return self.media[len(ATTACHMENT_PREFIX):]
        return None


class InputMediaPhoto(InputMedia):
    """
    Represents a photo to be sent.

    https://core.telegram.org/bots/api#inputmediaphoto
    """

    def __init__(self, media: base.InputFile, caption: base.String = None):
        super(InputMediaPhoto, self).__init__(type='photo', media=media, caption=caption)

        if isinstance(media, io.IOBase):
            self.file = media


class InputMediaVideo(InputMedia):
    """
    Represents a video to be sent.

    https://core.telegram.org/bots/api#inputmediavideo
    """
    width: base.Integer = fields.Field()
    height: base.Integer = fields.Field()
    duration: base.Integer = fields.Field()

    def __init__(self, media: base.InputFile, caption: base.String = None,
                 width: base.Integer = None, height: base.Integer = None, duration: base.Integer = None):
        super(InputMediaVideo, self).__init__(type='video', media=media, caption=caption,
                                              width=width, height=height, duration=duration)

        if isinstance(media, io.IOBase):
            self.file = media


class MediaGroup(base.TelegramObject):
    """
    Helper for sending media group
    """
    def __init__(self, media: typing.Optional[typing.List] = None):
        super(MediaGroup, self).__init__()
        self.media = []

        if media:
            for item in media:
                self._attach(item)

    def _attach(self, media: InputMedia):
        """
        Attach file

        :param media:
        :return:
        """
        # TODO: Detect media type from dict
        self.media.append(media)

    def attach_photo(self, photo: typing.Union[InputMediaPhoto, base.InputFile],
                     caption: base.String = None):
        """
        Attach photo

        :param photo:
        :param caption:
        :return:
        """
        if not isinstance(photo, InputMedia):
            photo = InputMediaPhoto(media=photo, caption=caption)
        self._attach(photo)

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
        :return:
        """
        if not isinstance(video, InputMedia):
            video = InputMediaVideo(media=video, caption=caption,
                                    width=width, height=height, duration=duration)
        self._attach(video)

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