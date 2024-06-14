from typing import Any, Dict, List, Literal, Optional, Union, overload

from aiogram.enums import InputMediaType
from aiogram.types import (
    UNSET_PARSE_MODE,
    InputFile,
    InputMedia,
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    MessageEntity,
)

MediaType = Union[
    InputMediaAudio,
    InputMediaPhoto,
    InputMediaVideo,
    InputMediaDocument,
]

MAX_MEDIA_GROUP_SIZE = 10


class MediaGroupBuilder:
    # Animated media is not supported yet in Bot API to send as a media group

    def __init__(
        self,
        media: Optional[List[MediaType]] = None,
        caption: Optional[str] = None,
        caption_entities: Optional[List[MessageEntity]] = None,
    ) -> None:
        """
        Helper class for building media groups.

        :param media: A list of media elements to add to the media group. (optional)
        :param caption: Caption for the media group. (optional)
        :param caption_entities: List of special entities in the caption,
            like usernames, URLs, etc. (optional)
        """
        self._media: List[MediaType] = []
        self.caption = caption
        self.caption_entities = caption_entities

        self._extend(media or [])

    def _add(self, media: MediaType) -> None:
        if not isinstance(media, InputMedia):
            raise ValueError("Media must be instance of InputMedia")

        if len(self._media) >= MAX_MEDIA_GROUP_SIZE:
            raise ValueError("Media group can't contain more than 10 elements")

        self._media.append(media)

    def _extend(self, media: List[MediaType]) -> None:
        for m in media:
            self._add(m)

    @overload
    def add(
        self,
        *,
        type: Literal[InputMediaType.AUDIO],
        media: Union[str, InputFile],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET_PARSE_MODE,
        caption_entities: Optional[List[MessageEntity]] = None,
        duration: Optional[int] = None,
        performer: Optional[str] = None,
        title: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        pass

    @overload
    def add(
        self,
        *,
        type: Literal[InputMediaType.PHOTO],
        media: Union[str, InputFile],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET_PARSE_MODE,
        caption_entities: Optional[List[MessageEntity]] = None,
        has_spoiler: Optional[bool] = None,
        **kwargs: Any,
    ) -> None:
        pass

    @overload
    def add(
        self,
        *,
        type: Literal[InputMediaType.VIDEO],
        media: Union[str, InputFile],
        thumbnail: Optional[Union[InputFile, str]] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET_PARSE_MODE,
        caption_entities: Optional[List[MessageEntity]] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        duration: Optional[int] = None,
        supports_streaming: Optional[bool] = None,
        has_spoiler: Optional[bool] = None,
        **kwargs: Any,
    ) -> None:
        pass

    @overload
    def add(
        self,
        *,
        type: Literal[InputMediaType.DOCUMENT],
        media: Union[str, InputFile],
        thumbnail: Optional[Union[InputFile, str]] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET_PARSE_MODE,
        caption_entities: Optional[List[MessageEntity]] = None,
        disable_content_type_detection: Optional[bool] = None,
        **kwargs: Any,
    ) -> None:
        pass

    def add(self, **kwargs: Any) -> None:
        """
        Add a media object to the media group.

        :param kwargs: Keyword arguments for the media object.
                The available keyword arguments depend on the media type.
        :return: None
        """
        type_ = kwargs.pop("type", None)
        if type_ == InputMediaType.AUDIO:
            self.add_audio(**kwargs)
        elif type_ == InputMediaType.PHOTO:
            self.add_photo(**kwargs)
        elif type_ == InputMediaType.VIDEO:
            self.add_video(**kwargs)
        elif type_ == InputMediaType.DOCUMENT:
            self.add_document(**kwargs)
        else:
            raise ValueError(f"Unknown media type: {type_!r}")

    def add_audio(
        self,
        media: Union[str, InputFile],
        thumbnail: Optional[InputFile] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET_PARSE_MODE,
        caption_entities: Optional[List[MessageEntity]] = None,
        duration: Optional[int] = None,
        performer: Optional[str] = None,
        title: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Add an audio file to the media group.

        :param media: File to send. Pass a file_id to send a file that exists on the
            Telegram servers (recommended), pass an HTTP URL for Telegram to get a file from
            the Internet, or pass 'attach://<file_attach_name>' to upload a new one using
            multipart/form-data under <file_attach_name> name.
             :ref:`More information on Sending Files » <sending-files>`
        :param thumbnail: *Optional*. Thumbnail of the file sent; can be ignored if
            thumbnail generation for the file is supported server-side. The thumbnail should
            be in JPEG format and less than 200 kB in size. A thumbnail's width and height
            should not exceed 320.
        :param caption: *Optional*. Caption of the audio to be sent, 0-1024 characters
            after entities parsing
        :param parse_mode: *Optional*. Mode for parsing entities in the audio caption.
            See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_
            for more details.
        :param caption_entities: *Optional*. List of special entities that appear in the caption,
            which can be specified instead of *parse_mode*
        :param duration: *Optional*. Duration of the audio in seconds
        :param performer: *Optional*. Performer of the audio
        :param title: *Optional*. Title of the audio
        :return: None
        """
        self._add(
            InputMediaAudio(
                media=media,
                thumbnail=thumbnail,
                caption=caption,
                parse_mode=parse_mode,
                caption_entities=caption_entities,
                duration=duration,
                performer=performer,
                title=title,
                **kwargs,
            )
        )

    def add_photo(
        self,
        media: Union[str, InputFile],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET_PARSE_MODE,
        caption_entities: Optional[List[MessageEntity]] = None,
        has_spoiler: Optional[bool] = None,
        **kwargs: Any,
    ) -> None:
        """
        Add a photo to the media group.

        :param media: File to send. Pass a file_id to send a file that exists on the
            Telegram servers (recommended), pass an HTTP URL for Telegram to get a file
            from the Internet, or pass 'attach://<file_attach_name>' to upload a new
            one using multipart/form-data under <file_attach_name> name.
             :ref:`More information on Sending Files » <sending-files>`
        :param caption: *Optional*. Caption of the photo to be sent, 0-1024 characters
            after entities parsing
        :param parse_mode: *Optional*. Mode for parsing entities in the photo caption.
            See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_
            for more details.
        :param caption_entities: *Optional*. List of special entities that appear in the caption,
            which can be specified instead of *parse_mode*
        :param has_spoiler: *Optional*. Pass :code:`True` if the photo needs to be covered
            with a spoiler animation
        :return: None
        """
        self._add(
            InputMediaPhoto(
                media=media,
                caption=caption,
                parse_mode=parse_mode,
                caption_entities=caption_entities,
                has_spoiler=has_spoiler,
                **kwargs,
            )
        )

    def add_video(
        self,
        media: Union[str, InputFile],
        thumbnail: Optional[InputFile] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET_PARSE_MODE,
        caption_entities: Optional[List[MessageEntity]] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        duration: Optional[int] = None,
        supports_streaming: Optional[bool] = None,
        has_spoiler: Optional[bool] = None,
        **kwargs: Any,
    ) -> None:
        """
        Add a video to the media group.

        :param media: File to send. Pass a file_id to send a file that exists on the
            Telegram servers (recommended), pass an HTTP URL for Telegram to get a file
            from the Internet, or pass 'attach://<file_attach_name>' to upload a new one
            using multipart/form-data under <file_attach_name> name.
            :ref:`More information on Sending Files » <sending-files>`
        :param thumbnail: *Optional*. Thumbnail of the file sent; can be ignored if thumbnail
            generation for the file is supported server-side. The thumbnail should be in JPEG
            format and less than 200 kB in size. A thumbnail's width and height should
            not exceed 320. Ignored if the file is not uploaded using multipart/form-data.
            Thumbnails can't be reused and can be only uploaded as a new file, so you
            can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using
            multipart/form-data under <file_attach_name>.
            :ref:`More information on Sending Files » <sending-files>`
        :param caption: *Optional*. Caption of the video to be sent,
            0-1024 characters after entities parsing
        :param parse_mode: *Optional*. Mode for parsing entities in the video caption.
            See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_
            for more details.
        :param caption_entities: *Optional*. List of special entities that appear in the caption,
            which can be specified instead of *parse_mode*
        :param width: *Optional*. Video width
        :param height: *Optional*. Video height
        :param duration: *Optional*. Video duration in seconds
        :param supports_streaming: *Optional*. Pass :code:`True` if the uploaded video is
            suitable for streaming
        :param has_spoiler: *Optional*. Pass :code:`True` if the video needs to be covered
            with a spoiler animation
        :return: None
        """
        self._add(
            InputMediaVideo(
                media=media,
                thumbnail=thumbnail,
                caption=caption,
                parse_mode=parse_mode,
                caption_entities=caption_entities,
                width=width,
                height=height,
                duration=duration,
                supports_streaming=supports_streaming,
                has_spoiler=has_spoiler,
                **kwargs,
            )
        )

    def add_document(
        self,
        media: Union[str, InputFile],
        thumbnail: Optional[InputFile] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET_PARSE_MODE,
        caption_entities: Optional[List[MessageEntity]] = None,
        disable_content_type_detection: Optional[bool] = None,
        **kwargs: Any,
    ) -> None:
        """
        Add a document to the media group.

        :param media: File to send. Pass a file_id to send a file that exists on the
            Telegram servers (recommended), pass an HTTP URL for Telegram to get a file
            from the Internet, or pass 'attach://<file_attach_name>' to upload a new one using
            multipart/form-data under <file_attach_name> name.
            :ref:`More information on Sending Files » <sending-files>`
        :param thumbnail: *Optional*. Thumbnail of the file sent; can be ignored
            if thumbnail generation for the file is supported server-side.
            The thumbnail should be in JPEG format and less than 200 kB in size.
            A thumbnail's width and height should not exceed 320.
            Ignored if the file is not uploaded using multipart/form-data.
            Thumbnails can't be reused and can be only uploaded as a new file,
            so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded
            using multipart/form-data under <file_attach_name>.
            :ref:`More information on Sending Files » <sending-files>`
        :param caption: *Optional*. Caption of the document to be sent,
            0-1024 characters after entities parsing
        :param parse_mode: *Optional*. Mode for parsing entities in the document caption.
            See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_
            for more details.
        :param caption_entities: *Optional*. List of special entities that appear
            in the caption, which can be specified instead of *parse_mode*
        :param disable_content_type_detection: *Optional*. Disables automatic server-side
            content type detection for files uploaded using multipart/form-data.
            Always :code:`True`, if the document is sent as part of an album.
        :return: None

        """
        self._add(
            InputMediaDocument(
                media=media,
                thumbnail=thumbnail,
                caption=caption,
                parse_mode=parse_mode,
                caption_entities=caption_entities,
                disable_content_type_detection=disable_content_type_detection,
                **kwargs,
            )
        )

    def build(self) -> List[MediaType]:
        """
        Builds a list of media objects for a media group.

        Adds the caption to the first media object if it is present.

        :return: List of media objects.
        """
        update_first_media: Dict[str, Any] = {"caption": self.caption}
        if self.caption_entities is not None:
            update_first_media["caption_entities"] = self.caption_entities
            update_first_media["parse_mode"] = None

        return [
            (
                media.model_copy(update=update_first_media)
                if index == 0 and self.caption is not None
                else media
            )
            for index, media in enumerate(self._media)
        ]
