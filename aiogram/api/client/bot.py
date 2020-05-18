from __future__ import annotations

import datetime
import io
import pathlib
from contextlib import asynccontextmanager
from typing import (
    Any,
    AsyncGenerator,
    AsyncIterator,
    BinaryIO,
    List,
    Optional,
    TypeVar,
    Union,
    cast,
)

import aiofiles
from async_lru import alru_cache

from ...utils.mixins import ContextInstanceMixin
from ...utils.token import extract_bot_id, validate_token
from ..methods import (
    AddStickerToSet,
    AnswerCallbackQuery,
    AnswerInlineQuery,
    AnswerPreCheckoutQuery,
    AnswerShippingQuery,
    CreateNewStickerSet,
    DeleteChatPhoto,
    DeleteChatStickerSet,
    DeleteMessage,
    DeleteStickerFromSet,
    DeleteWebhook,
    EditMessageCaption,
    EditMessageLiveLocation,
    EditMessageMedia,
    EditMessageReplyMarkup,
    EditMessageText,
    ExportChatInviteLink,
    ForwardMessage,
    GetChat,
    GetChatAdministrators,
    GetChatMember,
    GetChatMembersCount,
    GetFile,
    GetGameHighScores,
    GetMe,
    GetMyCommands,
    GetStickerSet,
    GetUpdates,
    GetUserProfilePhotos,
    GetWebhookInfo,
    KickChatMember,
    LeaveChat,
    PinChatMessage,
    PromoteChatMember,
    RestrictChatMember,
    SendAnimation,
    SendAudio,
    SendChatAction,
    SendContact,
    SendDice,
    SendDocument,
    SendGame,
    SendInvoice,
    SendLocation,
    SendMediaGroup,
    SendMessage,
    SendPhoto,
    SendPoll,
    SendSticker,
    SendVenue,
    SendVideo,
    SendVideoNote,
    SendVoice,
    SetChatAdministratorCustomTitle,
    SetChatDescription,
    SetChatPermissions,
    SetChatPhoto,
    SetChatStickerSet,
    SetChatTitle,
    SetGameScore,
    SetMyCommands,
    SetPassportDataErrors,
    SetStickerPositionInSet,
    SetStickerSetThumb,
    SetWebhook,
    StopMessageLiveLocation,
    StopPoll,
    TelegramMethod,
    UnbanChatMember,
    UnpinChatMessage,
    UploadStickerFile,
)
from ..types import (
    BotCommand,
    Chat,
    ChatMember,
    ChatPermissions,
    Downloadable,
    File,
    ForceReply,
    GameHighScore,
    InlineKeyboardMarkup,
    InlineQueryResult,
    InputFile,
    InputMedia,
    InputMediaPhoto,
    InputMediaVideo,
    LabeledPrice,
    MaskPosition,
    Message,
    PassportElementError,
    Poll,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    ShippingOption,
    StickerSet,
    Update,
    User,
    UserProfilePhotos,
    WebhookInfo,
)
from .session.aiohttp import AiohttpSession
from .session.base import BaseSession

T = TypeVar("T")


class Bot(ContextInstanceMixin["Bot"]):
    """
    Main bot class
    """

    def __init__(
        self, token: str, session: Optional[BaseSession] = None, parse_mode: Optional[str] = None,
    ) -> None:
        validate_token(token)

        if session is None:
            session = AiohttpSession()

        self.session = session
        self.parse_mode = parse_mode
        self.__token = token

    @property
    def id(self) -> int:
        """
        Get bot ID from token

        :return:
        """
        return extract_bot_id(self.__token)

    @asynccontextmanager
    async def context(self, auto_close: bool = True) -> AsyncIterator[Bot]:
        """
        Generate bot context

        :param auto_close:
        :return:
        """
        token = self.set_current(self)
        try:
            yield self
        finally:
            if auto_close:
                await self.close()
            self.reset_current(token)

    @alru_cache()  # type: ignore
    async def me(self) -> User:
        return await self.get_me()

    async def close(self) -> None:
        """
        Close bot session
        """
        await self.session.close()

    @classmethod
    async def __download_file_binary_io(
        cls, destination: BinaryIO, seek: bool, stream: AsyncGenerator[bytes, None]
    ) -> BinaryIO:
        async for chunk in stream:
            destination.write(chunk)
            destination.flush()
        if seek is True:
            destination.seek(0)
        return destination

    @classmethod
    async def __download_file(
        cls, destination: Union[str, pathlib.Path], stream: AsyncGenerator[bytes, None]
    ) -> None:
        async with aiofiles.open(destination, "wb") as f:
            async for chunk in stream:
                await f.write(chunk)

    async def download_file(
        self,
        file_path: str,
        destination: Optional[Union[BinaryIO, pathlib.Path, str]] = None,
        timeout: int = 30,
        chunk_size: int = 65536,
        seek: bool = True,
    ) -> Optional[BinaryIO]:
        """
        Download file by file_path to destination.

        If you want to automatically create destination (:class:`io.BytesIO`) use default
        value of destination and handle result of this method.

        :param file_path: File path on Telegram server (You can get it from :obj:`aiogram.types.File`)
        :param destination: Filename, file path or instance of :class:`io.IOBase`. For e.g. :class:`io.BytesIO`, defaults to None
        :param timeout: Total timeout in seconds, defaults to 30
        :param chunk_size: File chunks size, defaults to 64 kb
        :param seek: Go to start of file when downloading is finished. Used only for destination with :class:`typing.BinaryIO` type, defaults to True
        """
        if destination is None:
            destination = io.BytesIO()

        url = self.session.api.file_url(self.__token, file_path)
        stream = self.session.stream_content(url=url, timeout=timeout, chunk_size=chunk_size)

        if isinstance(destination, (str, pathlib.Path)):
            return await self.__download_file(destination=destination, stream=stream)
        else:
            return await self.__download_file_binary_io(
                destination=destination, seek=seek, stream=stream
            )

    async def download(
        self,
        file: Union[str, Downloadable],
        destination: Optional[Union[BinaryIO, pathlib.Path, str]] = None,
        timeout: int = 30,
        chunk_size: int = 65536,
        seek: bool = True,
    ) -> Optional[BinaryIO]:
        """
        Download file by file_id or Downloadable object to destination.

        If you want to automatically create destination (:class:`io.BytesIO`) use default
        value of destination and handle result of this method.

        :param file: file_id or Downloadable object
        :param destination: Filename, file path or instance of :class:`io.IOBase`. For e.g. :class:`io.BytesIO`, defaults to None
        :param timeout: Total timeout in seconds, defaults to 30
        :param chunk_size: File chunks size, defaults to 64 kb
        :param seek: Go to start of file when downloading is finished. Used only for destination with :class:`typing.BinaryIO` type, defaults to True
        """
        if isinstance(file, str):
            file_id = file
        else:
            file_id = getattr(file, "file_id", None)
            if file_id is None:
                raise TypeError("file can only be of the string or Downloadable type")

        _file = await self.get_file(file_id)
        # https://github.com/aiogram/aiogram/pull/282/files#r394110017
        file_path = cast(str, _file.file_path)

        return await self.download_file(
            file_path, destination=destination, timeout=timeout, chunk_size=chunk_size, seek=seek
        )

    async def __call__(self, method: TelegramMethod[T]) -> T:
        """
        Call API method

        :param method:
        :return:
        """
        return await self.session.make_request(self.__token, method)

    def __hash__(self) -> int:
        """
        Get hash for the token

        :return:
        """
        return hash(self.__token)

    def __eq__(self, other: Any) -> bool:
        """
        Compare current bot with another bot instance

        :param other:
        :return:
        """
        if not isinstance(other, Bot):
            return False
        return hash(self) == hash(other)

    # =============================================================================================
    # Group: Getting updates
    # Source: https://core.telegram.org/bots/api#getting-updates
    # =============================================================================================

    async def get_updates(
        self,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        timeout: Optional[int] = None,
        allowed_updates: Optional[List[str]] = None,
    ) -> List[Update]:
        """
        Use this method to receive incoming updates using long polling (wiki). An Array of Update
        objects is returned.
        Notes
        1. This method will not work if an outgoing webhook is set up.
        2. In order to avoid getting duplicate updates, recalculate offset after each server
        response.

        Source: https://core.telegram.org/bots/api#getupdates

        :param offset: Identifier of the first update to be returned. Must be greater by one than
        the highest among the identifiers of previously received updates. By
        default, updates starting with the earliest unconfirmed update are
        returned. An update is considered confirmed as soon as getUpdates is called
        with an offset higher than its update_id. The negative offset can be
        specified to retrieve updates starting from -offset update from the end of
        the updates queue. All previous updates will forgotten.
        :param limit: Limits the number of updates to be retrieved. Values between 1-100 are
        accepted. Defaults to 100.
        :param timeout: Timeout in seconds for long polling. Defaults to 0, i.e. usual short
        polling. Should be positive, short polling should be used for testing
        purposes only.
        :param allowed_updates: A JSON-serialized list of the update types you want your bot to
        receive. For example, specify ['message', 'edited_channel_post',
        'callback_query'] to only receive updates of these types. See
        Update for a complete list of available update types. Specify an
        empty list to receive all updates regardless of type (default). If
        not specified, the previous setting will be used.
        :return: An Array of Update objects is returned.
        """
        call = GetUpdates(
            offset=offset, limit=limit, timeout=timeout, allowed_updates=allowed_updates,
        )
        return await self(call)

    async def set_webhook(
        self,
        url: str,
        certificate: Optional[InputFile] = None,
        max_connections: Optional[int] = None,
        allowed_updates: Optional[List[str]] = None,
    ) -> bool:
        """
        Use this method to specify a url and receive incoming updates via an outgoing webhook.
        Whenever there is an update for the bot, we will send an HTTPS POST request to the
        specified url, containing a JSON-serialized Update. In case of an unsuccessful request, we
        will give up after a reasonable amount of attempts. Returns True on success.
        If you'd like to make sure that the Webhook request comes from Telegram, we recommend
        using a secret path in the URL, e.g. https://www.example.com/<token>. Since nobody else
        knows your bot‘s token, you can be pretty sure it’s us.
        Notes
        1. You will not be able to receive updates using getUpdates for as long as an outgoing
        webhook is set up.
        2. To use a self-signed certificate, you need to upload your public key certificate using
        certificate parameter. Please upload as InputFile, sending a String will not work.
        3. Ports currently supported for Webhooks: 443, 80, 88, 8443.
        NEW! If you're having any trouble setting up webhooks, please check out this amazing guide
        to Webhooks.

        Source: https://core.telegram.org/bots/api#setwebhook

        :param url: HTTPS url to send updates to. Use an empty string to remove webhook
        integration
        :param certificate: Upload your public key certificate so that the root certificate in use
        can be checked. See our self-signed guide for details.
        :param max_connections: Maximum allowed number of simultaneous HTTPS connections to the
        webhook for update delivery, 1-100. Defaults to 40. Use lower
        values to limit the load on your bot‘s server, and higher values
        to increase your bot’s throughput.
        :param allowed_updates: A JSON-serialized list of the update types you want your bot to
        receive. For example, specify ['message', 'edited_channel_post',
        'callback_query'] to only receive updates of these types. See
        Update for a complete list of available update types. Specify an
        empty list to receive all updates regardless of type (default). If
        not specified, the previous setting will be used.
        :return: Returns True on success.
        """
        call = SetWebhook(
            url=url,
            certificate=certificate,
            max_connections=max_connections,
            allowed_updates=allowed_updates,
        )
        return await self(call)

    async def delete_webhook(self,) -> bool:
        """
        Use this method to remove webhook integration if you decide to switch back to getUpdates.
        Returns True on success. Requires no parameters.

        Source: https://core.telegram.org/bots/api#deletewebhook

        :return: Returns True on success.
        """
        call = DeleteWebhook()
        return await self(call)

    async def get_webhook_info(self,) -> WebhookInfo:
        """
        Use this method to get current webhook status. Requires no parameters. On success, returns
        a WebhookInfo object. If the bot is using getUpdates, will return an object with the url
        field empty.

        Source: https://core.telegram.org/bots/api#getwebhookinfo

        :return: On success, returns a WebhookInfo object. If the bot is using getUpdates, will
        return an object with the url field empty.
        """
        call = GetWebhookInfo()
        return await self(call)

    # =============================================================================================
    # Group: Available methods
    # Source: https://core.telegram.org/bots/api#available-methods
    # =============================================================================================

    async def get_me(self,) -> User:
        """
        A simple method for testing your bot's auth token. Requires no parameters. Returns basic
        information about the bot in form of a User object.

        Source: https://core.telegram.org/bots/api#getme

        :return: Returns basic information about the bot in form of a User object.
        """
        call = GetMe()
        return await self(call)

    async def send_message(
        self,
        chat_id: Union[int, str],
        text: str,
        parse_mode: Optional[str] = None,
        disable_web_page_preview: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
    ) -> Message:
        """
        Use this method to send text messages. On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#sendmessage

        :param chat_id: Unique identifier for the target chat or username of the target channel
        (in the format @channelusername)
        :param text: Text of the message to be sent, 1-4096 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the message text. See formatting options
        for more details.
        :param disable_web_page_preview: Disables link previews for links in this message
        :param disable_notification: Sends the message silently. Users will receive a notification
        with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param reply_markup: Additional interface options. A JSON-serialized object for an inline
        keyboard, custom reply keyboard, instructions to remove reply
        keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        call = SendMessage(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup,
        )
        return await self(call)

    async def forward_message(
        self,
        chat_id: Union[int, str],
        from_chat_id: Union[int, str],
        message_id: int,
        disable_notification: Optional[bool] = None,
    ) -> Message:
        """
        Use this method to forward messages of any kind. On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#forwardmessage

        :param chat_id: Unique identifier for the target chat or username of the target channel
        (in the format @channelusername)
        :param from_chat_id: Unique identifier for the chat where the original message was sent
        (or channel username in the format @channelusername)
        :param message_id: Message identifier in the chat specified in from_chat_id
        :param disable_notification: Sends the message silently. Users will receive a notification
        with no sound.
        :return: On success, the sent Message is returned.
        """
        call = ForwardMessage(
            chat_id=chat_id,
            from_chat_id=from_chat_id,
            message_id=message_id,
            disable_notification=disable_notification,
        )
        return await self(call)

    async def send_photo(
        self,
        chat_id: Union[int, str],
        photo: Union[InputFile, str],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
    ) -> Message:
        """
        Use this method to send photos. On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#sendphoto

        :param chat_id: Unique identifier for the target chat or username of the target channel
        (in the format @channelusername)
        :param photo: Photo to send. Pass a file_id as String to send a photo that exists on the
        Telegram servers (recommended), pass an HTTP URL as a String for Telegram to
        get a photo from the Internet, or upload a new photo using
        multipart/form-data.
        :param caption: Photo caption (may also be used when resending photos by file_id), 0-1024
        characters after entities parsing
        :param parse_mode: Mode for parsing entities in the photo caption. See formatting options
        for more details.
        :param disable_notification: Sends the message silently. Users will receive a notification
        with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param reply_markup: Additional interface options. A JSON-serialized object for an inline
        keyboard, custom reply keyboard, instructions to remove reply
        keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        call = SendPhoto(
            chat_id=chat_id,
            photo=photo,
            caption=caption,
            parse_mode=parse_mode,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup,
        )
        return await self(call)

    async def send_audio(
        self,
        chat_id: Union[int, str],
        audio: Union[InputFile, str],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        duration: Optional[int] = None,
        performer: Optional[str] = None,
        title: Optional[str] = None,
        thumb: Optional[Union[InputFile, str]] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
    ) -> Message:
        """
        Use this method to send audio files, if you want Telegram clients to display them in the
        music player. Your audio must be in the .MP3 or .M4A format. On success, the sent Message
        is returned. Bots can currently send audio files of up to 50 MB in size, this limit may be
        changed in the future.
        For sending voice messages, use the sendVoice method instead.

        Source: https://core.telegram.org/bots/api#sendaudio

        :param chat_id: Unique identifier for the target chat or username of the target channel
        (in the format @channelusername)
        :param audio: Audio file to send. Pass a file_id as String to send an audio file that
        exists on the Telegram servers (recommended), pass an HTTP URL as a String
        for Telegram to get an audio file from the Internet, or upload a new one
        using multipart/form-data.
        :param caption: Audio caption, 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the audio caption. See formatting options
        for more details.
        :param duration: Duration of the audio in seconds
        :param performer: Performer
        :param title: Track name
        :param thumb: Thumbnail of the file sent; can be ignored if thumbnail generation for the
        file is supported server-side. The thumbnail should be in JPEG format and
        less than 200 kB in size. A thumbnail‘s width and height should not exceed
        320. Ignored if the file is not uploaded using multipart/form-data.
        Thumbnails can’t be reused and can be only uploaded as a new file, so you
        can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using
        multipart/form-data under <file_attach_name>.
        :param disable_notification: Sends the message silently. Users will receive a notification
        with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param reply_markup: Additional interface options. A JSON-serialized object for an inline
        keyboard, custom reply keyboard, instructions to remove reply
        keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        call = SendAudio(
            chat_id=chat_id,
            audio=audio,
            caption=caption,
            parse_mode=parse_mode,
            duration=duration,
            performer=performer,
            title=title,
            thumb=thumb,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup,
        )
        return await self(call)

    async def send_document(
        self,
        chat_id: Union[int, str],
        document: Union[InputFile, str],
        thumb: Optional[Union[InputFile, str]] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
    ) -> Message:
        """
        Use this method to send general files. On success, the sent Message is returned. Bots can
        currently send files of any type of up to 50 MB in size, this limit may be changed in the
        future.

        Source: https://core.telegram.org/bots/api#senddocument

        :param chat_id: Unique identifier for the target chat or username of the target channel
        (in the format @channelusername)
        :param document: File to send. Pass a file_id as String to send a file that exists on the
        Telegram servers (recommended), pass an HTTP URL as a String for Telegram
        to get a file from the Internet, or upload a new one using
        multipart/form-data.
        :param thumb: Thumbnail of the file sent; can be ignored if thumbnail generation for the
        file is supported server-side. The thumbnail should be in JPEG format and
        less than 200 kB in size. A thumbnail‘s width and height should not exceed
        320. Ignored if the file is not uploaded using multipart/form-data.
        Thumbnails can’t be reused and can be only uploaded as a new file, so you
        can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using
        multipart/form-data under <file_attach_name>.
        :param caption: Document caption (may also be used when resending documents by file_id),
        0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the document caption. See formatting
        options for more details.
        :param disable_notification: Sends the message silently. Users will receive a notification
        with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param reply_markup: Additional interface options. A JSON-serialized object for an inline
        keyboard, custom reply keyboard, instructions to remove reply
        keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        call = SendDocument(
            chat_id=chat_id,
            document=document,
            thumb=thumb,
            caption=caption,
            parse_mode=parse_mode,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup,
        )
        return await self(call)

    async def send_video(
        self,
        chat_id: Union[int, str],
        video: Union[InputFile, str],
        duration: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        thumb: Optional[Union[InputFile, str]] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        supports_streaming: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
    ) -> Message:
        """
        Use this method to send video files, Telegram clients support mp4 videos (other formats
        may be sent as Document). On success, the sent Message is returned. Bots can currently
        send video files of up to 50 MB in size, this limit may be changed in the future.

        Source: https://core.telegram.org/bots/api#sendvideo

        :param chat_id: Unique identifier for the target chat or username of the target channel
        (in the format @channelusername)
        :param video: Video to send. Pass a file_id as String to send a video that exists on the
        Telegram servers (recommended), pass an HTTP URL as a String for Telegram to
        get a video from the Internet, or upload a new video using
        multipart/form-data.
        :param duration: Duration of sent video in seconds
        :param width: Video width
        :param height: Video height
        :param thumb: Thumbnail of the file sent; can be ignored if thumbnail generation for the
        file is supported server-side. The thumbnail should be in JPEG format and
        less than 200 kB in size. A thumbnail‘s width and height should not exceed
        320. Ignored if the file is not uploaded using multipart/form-data.
        Thumbnails can’t be reused and can be only uploaded as a new file, so you
        can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using
        multipart/form-data under <file_attach_name>.
        :param caption: Video caption (may also be used when resending videos by file_id), 0-1024
        characters after entities parsing
        :param parse_mode: Mode for parsing entities in the video caption. See formatting options
        for more details.
        :param supports_streaming: Pass True, if the uploaded video is suitable for streaming
        :param disable_notification: Sends the message silently. Users will receive a notification
        with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param reply_markup: Additional interface options. A JSON-serialized object for an inline
        keyboard, custom reply keyboard, instructions to remove reply
        keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        call = SendVideo(
            chat_id=chat_id,
            video=video,
            duration=duration,
            width=width,
            height=height,
            thumb=thumb,
            caption=caption,
            parse_mode=parse_mode,
            supports_streaming=supports_streaming,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup,
        )
        return await self(call)

    async def send_animation(
        self,
        chat_id: Union[int, str],
        animation: Union[InputFile, str],
        duration: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        thumb: Optional[Union[InputFile, str]] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
    ) -> Message:
        """
        Use this method to send animation files (GIF or H.264/MPEG-4 AVC video without sound). On
        success, the sent Message is returned. Bots can currently send animation files of up to 50
        MB in size, this limit may be changed in the future.

        Source: https://core.telegram.org/bots/api#sendanimation

        :param chat_id: Unique identifier for the target chat or username of the target channel
        (in the format @channelusername)
        :param animation: Animation to send. Pass a file_id as String to send an animation that
        exists on the Telegram servers (recommended), pass an HTTP URL as a
        String for Telegram to get an animation from the Internet, or upload a
        new animation using multipart/form-data.
        :param duration: Duration of sent animation in seconds
        :param width: Animation width
        :param height: Animation height
        :param thumb: Thumbnail of the file sent; can be ignored if thumbnail generation for the
        file is supported server-side. The thumbnail should be in JPEG format and
        less than 200 kB in size. A thumbnail‘s width and height should not exceed
        320. Ignored if the file is not uploaded using multipart/form-data.
        Thumbnails can’t be reused and can be only uploaded as a new file, so you
        can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using
        multipart/form-data under <file_attach_name>.
        :param caption: Animation caption (may also be used when resending animation by file_id),
        0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the animation caption. See formatting
        options for more details.
        :param disable_notification: Sends the message silently. Users will receive a notification
        with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param reply_markup: Additional interface options. A JSON-serialized object for an inline
        keyboard, custom reply keyboard, instructions to remove reply
        keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        call = SendAnimation(
            chat_id=chat_id,
            animation=animation,
            duration=duration,
            width=width,
            height=height,
            thumb=thumb,
            caption=caption,
            parse_mode=parse_mode,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup,
        )
        return await self(call)

    async def send_voice(
        self,
        chat_id: Union[int, str],
        voice: Union[InputFile, str],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        duration: Optional[int] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
    ) -> Message:
        """
        Use this method to send audio files, if you want Telegram clients to display the file as a
        playable voice message. For this to work, your audio must be in an .OGG file encoded with
        OPUS (other formats may be sent as Audio or Document). On success, the sent Message is
        returned. Bots can currently send voice messages of up to 50 MB in size, this limit may be
        changed in the future.

        Source: https://core.telegram.org/bots/api#sendvoice

        :param chat_id: Unique identifier for the target chat or username of the target channel
        (in the format @channelusername)
        :param voice: Audio file to send. Pass a file_id as String to send a file that exists on
        the Telegram servers (recommended), pass an HTTP URL as a String for
        Telegram to get a file from the Internet, or upload a new one using
        multipart/form-data.
        :param caption: Voice message caption, 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the voice message caption. See formatting
        options for more details.
        :param duration: Duration of the voice message in seconds
        :param disable_notification: Sends the message silently. Users will receive a notification
        with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param reply_markup: Additional interface options. A JSON-serialized object for an inline
        keyboard, custom reply keyboard, instructions to remove reply
        keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        call = SendVoice(
            chat_id=chat_id,
            voice=voice,
            caption=caption,
            parse_mode=parse_mode,
            duration=duration,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup,
        )
        return await self(call)

    async def send_video_note(
        self,
        chat_id: Union[int, str],
        video_note: Union[InputFile, str],
        duration: Optional[int] = None,
        length: Optional[int] = None,
        thumb: Optional[Union[InputFile, str]] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
    ) -> Message:
        """
        As of v.4.0, Telegram clients support rounded square mp4 videos of up to 1 minute long.
        Use this method to send video messages. On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#sendvideonote

        :param chat_id: Unique identifier for the target chat or username of the target channel
        (in the format @channelusername)
        :param video_note: Video note to send. Pass a file_id as String to send a video note that
        exists on the Telegram servers (recommended) or upload a new video
        using multipart/form-data.. Sending video notes by a URL is currently
        unsupported
        :param duration: Duration of sent video in seconds
        :param length: Video width and height, i.e. diameter of the video message
        :param thumb: Thumbnail of the file sent; can be ignored if thumbnail generation for the
        file is supported server-side. The thumbnail should be in JPEG format and
        less than 200 kB in size. A thumbnail‘s width and height should not exceed
        320. Ignored if the file is not uploaded using multipart/form-data.
        Thumbnails can’t be reused and can be only uploaded as a new file, so you
        can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using
        multipart/form-data under <file_attach_name>.
        :param disable_notification: Sends the message silently. Users will receive a notification
        with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param reply_markup: Additional interface options. A JSON-serialized object for an inline
        keyboard, custom reply keyboard, instructions to remove reply
        keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        call = SendVideoNote(
            chat_id=chat_id,
            video_note=video_note,
            duration=duration,
            length=length,
            thumb=thumb,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup,
        )
        return await self(call)

    async def send_media_group(
        self,
        chat_id: Union[int, str],
        media: List[Union[InputMediaPhoto, InputMediaVideo]],
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
    ) -> List[Message]:
        """
        Use this method to send a group of photos or videos as an album. On success, an array of
        the sent Messages is returned.

        Source: https://core.telegram.org/bots/api#sendmediagroup

        :param chat_id: Unique identifier for the target chat or username of the target channel
        (in the format @channelusername)
        :param media: A JSON-serialized array describing photos and videos to be sent, must
        include 2-10 items
        :param disable_notification: Sends the messages silently. Users will receive a
        notification with no sound.
        :param reply_to_message_id: If the messages are a reply, ID of the original message
        :return: On success, an array of the sent Messages is returned.
        """
        call = SendMediaGroup(
            chat_id=chat_id,
            media=media,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
        )
        return await self(call)

    async def send_location(
        self,
        chat_id: Union[int, str],
        latitude: float,
        longitude: float,
        live_period: Optional[int] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
    ) -> Message:
        """
        Use this method to send point on the map. On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#sendlocation

        :param chat_id: Unique identifier for the target chat or username of the target channel
        (in the format @channelusername)
        :param latitude: Latitude of the location
        :param longitude: Longitude of the location
        :param live_period: Period in seconds for which the location will be updated (see Live
        Locations, should be between 60 and 86400.
        :param disable_notification: Sends the message silently. Users will receive a notification
        with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param reply_markup: Additional interface options. A JSON-serialized object for an inline
        keyboard, custom reply keyboard, instructions to remove reply
        keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        call = SendLocation(
            chat_id=chat_id,
            latitude=latitude,
            longitude=longitude,
            live_period=live_period,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup,
        )
        return await self(call)

    async def edit_message_live_location(
        self,
        latitude: float,
        longitude: float,
        chat_id: Optional[Union[int, str]] = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
    ) -> Union[Message, bool]:
        """
        Use this method to edit live location messages. A location can be edited until its
        live_period expires or editing is explicitly disabled by a call to
        stopMessageLiveLocation. On success, if the edited message was sent by the bot, the edited
        Message is returned, otherwise True is returned.

        Source: https://core.telegram.org/bots/api#editmessagelivelocation

        :param latitude: Latitude of new location
        :param longitude: Longitude of new location
        :param chat_id: Required if inline_message_id is not specified. Unique identifier for the
        target chat or username of the target channel (in the format
        @channelusername)
        :param message_id: Required if inline_message_id is not specified. Identifier of the
        message to edit
        :param inline_message_id: Required if chat_id and message_id are not specified. Identifier
        of the inline message
        :param reply_markup: A JSON-serialized object for a new inline keyboard.
        :return: On success, if the edited message was sent by the bot, the edited Message is
        returned, otherwise True is returned.
        """
        call = EditMessageLiveLocation(
            latitude=latitude,
            longitude=longitude,
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
            reply_markup=reply_markup,
        )
        return await self(call)

    async def stop_message_live_location(
        self,
        chat_id: Optional[Union[int, str]] = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
    ) -> Union[Message, bool]:
        """
        Use this method to stop updating a live location message before live_period expires. On
        success, if the message was sent by the bot, the sent Message is returned, otherwise True
        is returned.

        Source: https://core.telegram.org/bots/api#stopmessagelivelocation

        :param chat_id: Required if inline_message_id is not specified. Unique identifier for the
        target chat or username of the target channel (in the format
        @channelusername)
        :param message_id: Required if inline_message_id is not specified. Identifier of the
        message with live location to stop
        :param inline_message_id: Required if chat_id and message_id are not specified. Identifier
        of the inline message
        :param reply_markup: A JSON-serialized object for a new inline keyboard.
        :return: On success, if the message was sent by the bot, the sent Message is returned,
        otherwise True is returned.
        """
        call = StopMessageLiveLocation(
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
            reply_markup=reply_markup,
        )
        return await self(call)

    async def send_venue(
        self,
        chat_id: Union[int, str],
        latitude: float,
        longitude: float,
        title: str,
        address: str,
        foursquare_id: Optional[str] = None,
        foursquare_type: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
    ) -> Message:
        """
        Use this method to send information about a venue. On success, the sent Message is
        returned.

        Source: https://core.telegram.org/bots/api#sendvenue

        :param chat_id: Unique identifier for the target chat or username of the target channel
        (in the format @channelusername)
        :param latitude: Latitude of the venue
        :param longitude: Longitude of the venue
        :param title: Name of the venue
        :param address: Address of the venue
        :param foursquare_id: Foursquare identifier of the venue
        :param foursquare_type: Foursquare type of the venue, if known. (For example,
        'arts_entertainment/default', 'arts_entertainment/aquarium' or
        'food/icecream'.)
        :param disable_notification: Sends the message silently. Users will receive a notification
        with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param reply_markup: Additional interface options. A JSON-serialized object for an inline
        keyboard, custom reply keyboard, instructions to remove reply
        keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        call = SendVenue(
            chat_id=chat_id,
            latitude=latitude,
            longitude=longitude,
            title=title,
            address=address,
            foursquare_id=foursquare_id,
            foursquare_type=foursquare_type,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup,
        )
        return await self(call)

    async def send_contact(
        self,
        chat_id: Union[int, str],
        phone_number: str,
        first_name: str,
        last_name: Optional[str] = None,
        vcard: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
    ) -> Message:
        """
        Use this method to send phone contacts. On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#sendcontact

        :param chat_id: Unique identifier for the target chat or username of the target channel
        (in the format @channelusername)
        :param phone_number: Contact's phone number
        :param first_name: Contact's first name
        :param last_name: Contact's last name
        :param vcard: Additional data about the contact in the form of a vCard, 0-2048 bytes
        :param disable_notification: Sends the message silently. Users will receive a notification
        with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param reply_markup: Additional interface options. A JSON-serialized object for an inline
        keyboard, custom reply keyboard, instructions to remove keyboard or
        to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        call = SendContact(
            chat_id=chat_id,
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            vcard=vcard,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup,
        )
        return await self(call)

    async def send_poll(
        self,
        chat_id: Union[int, str],
        question: str,
        options: List[str],
        is_anonymous: Optional[bool] = None,
        type: Optional[str] = None,
        allows_multiple_answers: Optional[bool] = None,
        correct_option_id: Optional[int] = None,
        explanation: Optional[str] = None,
        explanation_parse_mode: Optional[str] = None,
        open_period: Optional[int] = None,
        close_date: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None,
        is_closed: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
    ) -> Message:
        """
        Use this method to send a native poll. On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#sendpoll

        :param chat_id: Unique identifier for the target chat or username of the target channel
        (in the format @channelusername)
        :param question: Poll question, 1-255 characters
        :param options: A JSON-serialized list of answer options, 2-10 strings 1-100 characters
        each
        :param is_anonymous: True, if the poll needs to be anonymous, defaults to True
        :param type: Poll type, 'quiz' or 'regular', defaults to 'regular'
        :param allows_multiple_answers: True, if the poll allows multiple answers, ignored for
        polls in quiz mode, defaults to False
        :param correct_option_id: 0-based identifier of the correct answer option, required for
        polls in quiz mode
        :param explanation: Text that is shown when a user chooses an incorrect answer or taps on
        the lamp icon in a quiz-style poll, 0-200 characters with at most 2
        line feeds after entities parsing
        :param explanation_parse_mode: Mode for parsing entities in the explanation. See
        formatting options for more details.
        :param open_period: Amount of time in seconds the poll will be active after creation,
        5-600. Can't be used together with close_date.
        :param close_date: Point in time (Unix timestamp) when the poll will be automatically
        closed. Must be at least 5 and no more than 600 seconds in the future.
        Can't be used together with open_period.
        :param is_closed: Pass True, if the poll needs to be immediately closed. This can be
        useful for poll preview.
        :param disable_notification: Sends the message silently. Users will receive a notification
        with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param reply_markup: Additional interface options. A JSON-serialized object for an inline
        keyboard, custom reply keyboard, instructions to remove reply
        keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        call = SendPoll(
            chat_id=chat_id,
            question=question,
            options=options,
            is_anonymous=is_anonymous,
            type=type,
            allows_multiple_answers=allows_multiple_answers,
            correct_option_id=correct_option_id,
            explanation=explanation,
            explanation_parse_mode=explanation_parse_mode,
            open_period=open_period,
            close_date=close_date,
            is_closed=is_closed,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup,
        )
        return await self(call)

    async def send_dice(
        self,
        chat_id: Union[int, str],
        emoji: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
    ) -> Message:
        """
        Use this method to send a dice, which will have a random value from 1 to 6. On success,
        the sent Message is returned. (Yes, we're aware of the 'proper' singular of die. But it's
        awkward, and we decided to help it change. One dice at a time!)

        Source: https://core.telegram.org/bots/api#senddice

        :param chat_id: Unique identifier for the target chat or username of the target channel
        (in the format @channelusername)
        :param emoji: Emoji on which the dice throw animation is based. Currently, must be one of
        '' or ''. Defauts to ''
        :param disable_notification: Sends the message silently. Users will receive a notification
        with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param reply_markup: Additional interface options. A JSON-serialized object for an inline
        keyboard, custom reply keyboard, instructions to remove reply
        keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        call = SendDice(
            chat_id=chat_id,
            emoji=emoji,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup,
        )
        return await self(call)

    async def send_chat_action(self, chat_id: Union[int, str], action: str,) -> bool:
        """
        Use this method when you need to tell the user that something is happening on the bot's
        side. The status is set for 5 seconds or less (when a message arrives from your bot,
        Telegram clients clear its typing status). Returns True on success.
        Example: The ImageBot needs some time to process a request and upload the image. Instead
        of sending a text message along the lines of 'Retrieving image, please wait…', the bot may
        use sendChatAction with action = upload_photo. The user will see a 'sending photo' status
        for the bot.
        We only recommend using this method when a response from the bot will take a noticeable
        amount of time to arrive.

        Source: https://core.telegram.org/bots/api#sendchataction

        :param chat_id: Unique identifier for the target chat or username of the target channel
        (in the format @channelusername)
        :param action: Type of action to broadcast. Choose one, depending on what the user is
        about to receive: typing for text messages, upload_photo for photos,
        record_video or upload_video for videos, record_audio or upload_audio for
        audio files, upload_document for general files, find_location for location
        data, record_video_note or upload_video_note for video notes.
        :return: Returns True on success.
        """
        call = SendChatAction(chat_id=chat_id, action=action,)
        return await self(call)

    async def get_user_profile_photos(
        self, user_id: int, offset: Optional[int] = None, limit: Optional[int] = None,
    ) -> UserProfilePhotos:
        """
        Use this method to get a list of profile pictures for a user. Returns a UserProfilePhotos
        object.

        Source: https://core.telegram.org/bots/api#getuserprofilephotos

        :param user_id: Unique identifier of the target user
        :param offset: Sequential number of the first photo to be returned. By default, all photos
        are returned.
        :param limit: Limits the number of photos to be retrieved. Values between 1-100 are
        accepted. Defaults to 100.
        :return: Returns a UserProfilePhotos object.
        """
        call = GetUserProfilePhotos(user_id=user_id, offset=offset, limit=limit,)
        return await self(call)

    async def get_file(self, file_id: str,) -> File:
        """
        Use this method to get basic info about a file and prepare it for downloading. For the
        moment, bots can download files of up to 20MB in size. On success, a File object is
        returned. The file can then be downloaded via the link
        https://api.telegram.org/file/bot<token>/<file_path>, where <file_path> is taken from the
        response. It is guaranteed that the link will be valid for at least 1 hour. When the link
        expires, a new one can be requested by calling getFile again.
        Note: This function may not preserve the original file name and MIME type. You should save
        the file's MIME type and name (if available) when the File object is received.

        Source: https://core.telegram.org/bots/api#getfile

        :param file_id: File identifier to get info about
        :return: On success, a File object is returned.
        """
        call = GetFile(file_id=file_id,)
        return await self(call)

    async def kick_chat_member(
        self,
        chat_id: Union[int, str],
        user_id: int,
        until_date: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None,
    ) -> bool:
        """
        Use this method to kick a user from a group, a supergroup or a channel. In the case of
        supergroups and channels, the user will not be able to return to the group on their own
        using invite links, etc., unless unbanned first. The bot must be an administrator in the
        chat for this to work and must have the appropriate admin rights. Returns True on success.

        Source: https://core.telegram.org/bots/api#kickchatmember

        :param chat_id: Unique identifier for the target group or username of the target
        supergroup or channel (in the format @channelusername)
        :param user_id: Unique identifier of the target user
        :param until_date: Date when the user will be unbanned, unix time. If user is banned for
        more than 366 days or less than 30 seconds from the current time they
        are considered to be banned forever
        :return: In the case of supergroups and channels, the user will not be able to return to
        the group on their own using invite links, etc. Returns True on success.
        """
        call = KickChatMember(chat_id=chat_id, user_id=user_id, until_date=until_date,)
        return await self(call)

    async def unban_chat_member(self, chat_id: Union[int, str], user_id: int,) -> bool:
        """
        Use this method to unban a previously kicked user in a supergroup or channel. The user
        will not return to the group or channel automatically, but will be able to join via link,
        etc. The bot must be an administrator for this to work. Returns True on success.

        Source: https://core.telegram.org/bots/api#unbanchatmember

        :param chat_id: Unique identifier for the target group or username of the target
        supergroup or channel (in the format @username)
        :param user_id: Unique identifier of the target user
        :return: The user will not return to the group or channel automatically, but will be able
        to join via link, etc. Returns True on success.
        """
        call = UnbanChatMember(chat_id=chat_id, user_id=user_id,)
        return await self(call)

    async def restrict_chat_member(
        self,
        chat_id: Union[int, str],
        user_id: int,
        permissions: ChatPermissions,
        until_date: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None,
    ) -> bool:
        """
        Use this method to restrict a user in a supergroup. The bot must be an administrator in
        the supergroup for this to work and must have the appropriate admin rights. Pass True for
        all permissions to lift restrictions from a user. Returns True on success.

        Source: https://core.telegram.org/bots/api#restrictchatmember

        :param chat_id: Unique identifier for the target chat or username of the target supergroup
        (in the format @supergroupusername)
        :param user_id: Unique identifier of the target user
        :param permissions: New user permissions
        :param until_date: Date when restrictions will be lifted for the user, unix time. If user
        is restricted for more than 366 days or less than 30 seconds from the
        current time, they are considered to be restricted forever
        :return: Returns True on success.
        """
        call = RestrictChatMember(
            chat_id=chat_id, user_id=user_id, permissions=permissions, until_date=until_date,
        )
        return await self(call)

    async def promote_chat_member(
        self,
        chat_id: Union[int, str],
        user_id: int,
        can_change_info: Optional[bool] = None,
        can_post_messages: Optional[bool] = None,
        can_edit_messages: Optional[bool] = None,
        can_delete_messages: Optional[bool] = None,
        can_invite_users: Optional[bool] = None,
        can_restrict_members: Optional[bool] = None,
        can_pin_messages: Optional[bool] = None,
        can_promote_members: Optional[bool] = None,
    ) -> bool:
        """
        Use this method to promote or demote a user in a supergroup or a channel. The bot must be
        an administrator in the chat for this to work and must have the appropriate admin rights.
        Pass False for all boolean parameters to demote a user. Returns True on success.

        Source: https://core.telegram.org/bots/api#promotechatmember

        :param chat_id: Unique identifier for the target chat or username of the target channel
        (in the format @channelusername)
        :param user_id: Unique identifier of the target user
        :param can_change_info: Pass True, if the administrator can change chat title, photo and
        other settings
        :param can_post_messages: Pass True, if the administrator can create channel posts,
        channels only
        :param can_edit_messages: Pass True, if the administrator can edit messages of other users
        and can pin messages, channels only
        :param can_delete_messages: Pass True, if the administrator can delete messages of other
        users
        :param can_invite_users: Pass True, if the administrator can invite new users to the chat
        :param can_restrict_members: Pass True, if the administrator can restrict, ban or unban
        chat members
        :param can_pin_messages: Pass True, if the administrator can pin messages, supergroups
        only
        :param can_promote_members: Pass True, if the administrator can add new administrators
        with a subset of their own privileges or demote administrators
        that he has promoted, directly or indirectly (promoted by
        administrators that were appointed by him)
        :return: Returns True on success.
        """
        call = PromoteChatMember(
            chat_id=chat_id,
            user_id=user_id,
            can_change_info=can_change_info,
            can_post_messages=can_post_messages,
            can_edit_messages=can_edit_messages,
            can_delete_messages=can_delete_messages,
            can_invite_users=can_invite_users,
            can_restrict_members=can_restrict_members,
            can_pin_messages=can_pin_messages,
            can_promote_members=can_promote_members,
        )
        return await self(call)

    async def set_chat_administrator_custom_title(
        self, chat_id: Union[int, str], user_id: int, custom_title: str,
    ) -> bool:
        """
        Use this method to set a custom title for an administrator in a supergroup promoted by the
        bot. Returns True on success.

        Source: https://core.telegram.org/bots/api#setchatadministratorcustomtitle

        :param chat_id: Unique identifier for the target chat or username of the target supergroup
        (in the format @supergroupusername)
        :param user_id: Unique identifier of the target user
        :param custom_title: New custom title for the administrator; 0-16 characters, emoji are
        not allowed
        :return: Returns True on success.
        """
        call = SetChatAdministratorCustomTitle(
            chat_id=chat_id, user_id=user_id, custom_title=custom_title,
        )
        return await self(call)

    async def set_chat_permissions(
        self, chat_id: Union[int, str], permissions: ChatPermissions,
    ) -> bool:
        """
        Use this method to set default chat permissions for all members. The bot must be an
        administrator in the group or a supergroup for this to work and must have the
        can_restrict_members admin rights. Returns True on success.

        Source: https://core.telegram.org/bots/api#setchatpermissions

        :param chat_id: Unique identifier for the target chat or username of the target supergroup
        (in the format @supergroupusername)
        :param permissions: New default chat permissions
        :return: Returns True on success.
        """
        call = SetChatPermissions(chat_id=chat_id, permissions=permissions,)
        return await self(call)

    async def export_chat_invite_link(self, chat_id: Union[int, str],) -> str:
        """
        Use this method to generate a new invite link for a chat; any previously generated link is
        revoked. The bot must be an administrator in the chat for this to work and must have the
        appropriate admin rights. Returns the new invite link as String on success.
        Note: Each administrator in a chat generates their own invite links. Bots can't use invite
        links generated by other administrators. If you want your bot to work with invite links,
        it will need to generate its own link using exportChatInviteLink — after this the link
        will become available to the bot via the getChat method. If your bot needs to generate a
        new invite link replacing its previous one, use exportChatInviteLink again.

        Source: https://core.telegram.org/bots/api#exportchatinvitelink

        :param chat_id: Unique identifier for the target chat or username of the target channel
        (in the format @channelusername)
        :return: Returns the new invite link as String on success.
        """
        call = ExportChatInviteLink(chat_id=chat_id,)
        return await self(call)

    async def set_chat_photo(self, chat_id: Union[int, str], photo: InputFile,) -> bool:
        """
        Use this method to set a new profile photo for the chat. Photos can't be changed for
        private chats. The bot must be an administrator in the chat for this to work and must have
        the appropriate admin rights. Returns True on success.

        Source: https://core.telegram.org/bots/api#setchatphoto

        :param chat_id: Unique identifier for the target chat or username of the target channel
        (in the format @channelusername)
        :param photo: New chat photo, uploaded using multipart/form-data
        :return: Returns True on success.
        """
        call = SetChatPhoto(chat_id=chat_id, photo=photo,)
        return await self(call)

    async def delete_chat_photo(self, chat_id: Union[int, str],) -> bool:
        """
        Use this method to delete a chat photo. Photos can't be changed for private chats. The bot
        must be an administrator in the chat for this to work and must have the appropriate admin
        rights. Returns True on success.

        Source: https://core.telegram.org/bots/api#deletechatphoto

        :param chat_id: Unique identifier for the target chat or username of the target channel
        (in the format @channelusername)
        :return: Returns True on success.
        """
        call = DeleteChatPhoto(chat_id=chat_id,)
        return await self(call)

    async def set_chat_title(self, chat_id: Union[int, str], title: str,) -> bool:
        """
        Use this method to change the title of a chat. Titles can't be changed for private chats.
        The bot must be an administrator in the chat for this to work and must have the
        appropriate admin rights. Returns True on success.

        Source: https://core.telegram.org/bots/api#setchattitle

        :param chat_id: Unique identifier for the target chat or username of the target channel
        (in the format @channelusername)
        :param title: New chat title, 1-255 characters
        :return: Returns True on success.
        """
        call = SetChatTitle(chat_id=chat_id, title=title,)
        return await self(call)

    async def set_chat_description(
        self, chat_id: Union[int, str], description: Optional[str] = None,
    ) -> bool:
        """
        Use this method to change the description of a group, a supergroup or a channel. The bot
        must be an administrator in the chat for this to work and must have the appropriate admin
        rights. Returns True on success.

        Source: https://core.telegram.org/bots/api#setchatdescription

        :param chat_id: Unique identifier for the target chat or username of the target channel
        (in the format @channelusername)
        :param description: New chat description, 0-255 characters
        :return: Returns True on success.
        """
        call = SetChatDescription(chat_id=chat_id, description=description,)
        return await self(call)

    async def pin_chat_message(
        self,
        chat_id: Union[int, str],
        message_id: int,
        disable_notification: Optional[bool] = None,
    ) -> bool:
        """
        Use this method to pin a message in a group, a supergroup, or a channel. The bot must be
        an administrator in the chat for this to work and must have the ‘can_pin_messages’ admin
        right in the supergroup or ‘can_edit_messages’ admin right in the channel. Returns True on
        success.

        Source: https://core.telegram.org/bots/api#pinchatmessage

        :param chat_id: Unique identifier for the target chat or username of the target channel
        (in the format @channelusername)
        :param message_id: Identifier of a message to pin
        :param disable_notification: Pass True, if it is not necessary to send a notification to
        all chat members about the new pinned message. Notifications
        are always disabled in channels.
        :return: Returns True on success.
        """
        call = PinChatMessage(
            chat_id=chat_id, message_id=message_id, disable_notification=disable_notification,
        )
        return await self(call)

    async def unpin_chat_message(self, chat_id: Union[int, str],) -> bool:
        """
        Use this method to unpin a message in a group, a supergroup, or a channel. The bot must be
        an administrator in the chat for this to work and must have the ‘can_pin_messages’ admin
        right in the supergroup or ‘can_edit_messages’ admin right in the channel. Returns True on
        success.

        Source: https://core.telegram.org/bots/api#unpinchatmessage

        :param chat_id: Unique identifier for the target chat or username of the target channel
        (in the format @channelusername)
        :return: Returns True on success.
        """
        call = UnpinChatMessage(chat_id=chat_id,)
        return await self(call)

    async def leave_chat(self, chat_id: Union[int, str],) -> bool:
        """
        Use this method for your bot to leave a group, supergroup or channel. Returns True on
        success.

        Source: https://core.telegram.org/bots/api#leavechat

        :param chat_id: Unique identifier for the target chat or username of the target supergroup
        or channel (in the format @channelusername)
        :return: Returns True on success.
        """
        call = LeaveChat(chat_id=chat_id,)
        return await self(call)

    async def get_chat(self, chat_id: Union[int, str],) -> Chat:
        """
        Use this method to get up to date information about the chat (current name of the user for
        one-on-one conversations, current username of a user, group or channel, etc.). Returns a
        Chat object on success.

        Source: https://core.telegram.org/bots/api#getchat

        :param chat_id: Unique identifier for the target chat or username of the target supergroup
        or channel (in the format @channelusername)
        :return: Returns a Chat object on success.
        """
        call = GetChat(chat_id=chat_id,)
        return await self(call)

    async def get_chat_administrators(self, chat_id: Union[int, str],) -> List[ChatMember]:
        """
        Use this method to get a list of administrators in a chat. On success, returns an Array of
        ChatMember objects that contains information about all chat administrators except other
        bots. If the chat is a group or a supergroup and no administrators were appointed, only
        the creator will be returned.

        Source: https://core.telegram.org/bots/api#getchatadministrators

        :param chat_id: Unique identifier for the target chat or username of the target supergroup
        or channel (in the format @channelusername)
        :return: On success, returns an Array of ChatMember objects that contains information
        about all chat administrators except other bots. If the chat is a group or a
        supergroup and no administrators were appointed, only the creator will be
        returned.
        """
        call = GetChatAdministrators(chat_id=chat_id,)
        return await self(call)

    async def get_chat_members_count(self, chat_id: Union[int, str],) -> int:
        """
        Use this method to get the number of members in a chat. Returns Int on success.

        Source: https://core.telegram.org/bots/api#getchatmemberscount

        :param chat_id: Unique identifier for the target chat or username of the target supergroup
        or channel (in the format @channelusername)
        :return: Returns Int on success.
        """
        call = GetChatMembersCount(chat_id=chat_id,)
        return await self(call)

    async def get_chat_member(self, chat_id: Union[int, str], user_id: int,) -> ChatMember:
        """
        Use this method to get information about a member of a chat. Returns a ChatMember object
        on success.

        Source: https://core.telegram.org/bots/api#getchatmember

        :param chat_id: Unique identifier for the target chat or username of the target supergroup
        or channel (in the format @channelusername)
        :param user_id: Unique identifier of the target user
        :return: Returns a ChatMember object on success.
        """
        call = GetChatMember(chat_id=chat_id, user_id=user_id,)
        return await self(call)

    async def set_chat_sticker_set(self, chat_id: Union[int, str], sticker_set_name: str,) -> bool:
        """
        Use this method to set a new group sticker set for a supergroup. The bot must be an
        administrator in the chat for this to work and must have the appropriate admin rights. Use
        the field can_set_sticker_set optionally returned in getChat requests to check if the bot
        can use this method. Returns True on success.

        Source: https://core.telegram.org/bots/api#setchatstickerset

        :param chat_id: Unique identifier for the target chat or username of the target supergroup
        (in the format @supergroupusername)
        :param sticker_set_name: Name of the sticker set to be set as the group sticker set
        :return: Use the field can_set_sticker_set optionally returned in getChat requests to
        check if the bot can use this method. Returns True on success.
        """
        call = SetChatStickerSet(chat_id=chat_id, sticker_set_name=sticker_set_name,)
        return await self(call)

    async def delete_chat_sticker_set(self, chat_id: Union[int, str],) -> bool:
        """
        Use this method to delete a group sticker set from a supergroup. The bot must be an
        administrator in the chat for this to work and must have the appropriate admin rights. Use
        the field can_set_sticker_set optionally returned in getChat requests to check if the bot
        can use this method. Returns True on success.

        Source: https://core.telegram.org/bots/api#deletechatstickerset

        :param chat_id: Unique identifier for the target chat or username of the target supergroup
        (in the format @supergroupusername)
        :return: Use the field can_set_sticker_set optionally returned in getChat requests to
        check if the bot can use this method. Returns True on success.
        """
        call = DeleteChatStickerSet(chat_id=chat_id,)
        return await self(call)

    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: Optional[str] = None,
        show_alert: Optional[bool] = None,
        url: Optional[str] = None,
        cache_time: Optional[int] = None,
    ) -> bool:
        """
        Use this method to send answers to callback queries sent from inline keyboards. The answer
        will be displayed to the user as a notification at the top of the chat screen or as an
        alert. On success, True is returned.
        Alternatively, the user can be redirected to the specified Game URL. For this option to
        work, you must first create a game for your bot via @Botfather and accept the terms.
        Otherwise, you may use links like t.me/your_bot?start=XXXX that open your bot with a
        parameter.

        Source: https://core.telegram.org/bots/api#answercallbackquery

        :param callback_query_id: Unique identifier for the query to be answered
        :param text: Text of the notification. If not specified, nothing will be shown to the
        user, 0-200 characters
        :param show_alert: If true, an alert will be shown by the client instead of a notification
        at the top of the chat screen. Defaults to false.
        :param url: URL that will be opened by the user's client. If you have created a Game and
        accepted the conditions via @Botfather, specify the URL that opens your game —
        note that this will only work if the query comes from a callback_game button.
        :param cache_time: The maximum amount of time in seconds that the result of the callback
        query may be cached client-side. Telegram apps will support caching
        starting in version 3.14. Defaults to 0.
        :return: On success, True is returned.
        """
        call = AnswerCallbackQuery(
            callback_query_id=callback_query_id,
            text=text,
            show_alert=show_alert,
            url=url,
            cache_time=cache_time,
        )
        return await self(call)

    async def set_my_commands(self, commands: List[BotCommand],) -> bool:
        """
        Use this method to change the list of the bot's commands. Returns True on success.

        Source: https://core.telegram.org/bots/api#setmycommands

        :param commands: A JSON-serialized list of bot commands to be set as the list of the bot's
        commands. At most 100 commands can be specified.
        :return: Returns True on success.
        """
        call = SetMyCommands(commands=commands,)
        return await self(call)

    async def get_my_commands(self,) -> List[BotCommand]:
        """
        Use this method to get the current list of the bot's commands. Requires no parameters.
        Returns Array of BotCommand on success.

        Source: https://core.telegram.org/bots/api#getmycommands

        :return: Returns Array of BotCommand on success.
        """
        call = GetMyCommands()
        return await self(call)

    # =============================================================================================
    # Group: Updating messages
    # Source: https://core.telegram.org/bots/api#updating-messages
    # =============================================================================================

    async def edit_message_text(
        self,
        text: str,
        chat_id: Optional[Union[int, str]] = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
        parse_mode: Optional[str] = None,
        disable_web_page_preview: Optional[bool] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
    ) -> Union[Message, bool]:
        """
        Use this method to edit text and game messages. On success, if edited message is sent by
        the bot, the edited Message is returned, otherwise True is returned.

        Source: https://core.telegram.org/bots/api#editmessagetext

        :param text: New text of the message, 1-4096 characters after entities parsing
        :param chat_id: Required if inline_message_id is not specified. Unique identifier for the
        target chat or username of the target channel (in the format
        @channelusername)
        :param message_id: Required if inline_message_id is not specified. Identifier of the
        message to edit
        :param inline_message_id: Required if chat_id and message_id are not specified. Identifier
        of the inline message
        :param parse_mode: Mode for parsing entities in the message text. See formatting options
        for more details.
        :param disable_web_page_preview: Disables link previews for links in this message
        :param reply_markup: A JSON-serialized object for an inline keyboard.
        :return: On success, if edited message is sent by the bot, the edited Message is returned,
        otherwise True is returned.
        """
        call = EditMessageText(
            text=text,
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview,
            reply_markup=reply_markup,
        )
        return await self(call)

    async def edit_message_caption(
        self,
        chat_id: Optional[Union[int, str]] = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
    ) -> Union[Message, bool]:
        """
        Use this method to edit captions of messages. On success, if edited message is sent by the
        bot, the edited Message is returned, otherwise True is returned.

        Source: https://core.telegram.org/bots/api#editmessagecaption

        :param chat_id: Required if inline_message_id is not specified. Unique identifier for the
        target chat or username of the target channel (in the format
        @channelusername)
        :param message_id: Required if inline_message_id is not specified. Identifier of the
        message to edit
        :param inline_message_id: Required if chat_id and message_id are not specified. Identifier
        of the inline message
        :param caption: New caption of the message, 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the message caption. See formatting
        options for more details.
        :param reply_markup: A JSON-serialized object for an inline keyboard.
        :return: On success, if edited message is sent by the bot, the edited Message is returned,
        otherwise True is returned.
        """
        call = EditMessageCaption(
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
            caption=caption,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
        )
        return await self(call)

    async def edit_message_media(
        self,
        media: InputMedia,
        chat_id: Optional[Union[int, str]] = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
    ) -> Union[Message, bool]:
        """
        Use this method to edit animation, audio, document, photo, or video messages. If a message
        is a part of a message album, then it can be edited only to a photo or a video. Otherwise,
        message type can be changed arbitrarily. When inline message is edited, new file can't be
        uploaded. Use previously uploaded file via its file_id or specify a URL. On success, if
        the edited message was sent by the bot, the edited Message is returned, otherwise True is
        returned.

        Source: https://core.telegram.org/bots/api#editmessagemedia

        :param media: A JSON-serialized object for a new media content of the message
        :param chat_id: Required if inline_message_id is not specified. Unique identifier for the
        target chat or username of the target channel (in the format
        @channelusername)
        :param message_id: Required if inline_message_id is not specified. Identifier of the
        message to edit
        :param inline_message_id: Required if chat_id and message_id are not specified. Identifier
        of the inline message
        :param reply_markup: A JSON-serialized object for a new inline keyboard.
        :return: On success, if the edited message was sent by the bot, the edited Message is
        returned, otherwise True is returned.
        """
        call = EditMessageMedia(
            media=media,
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
            reply_markup=reply_markup,
        )
        return await self(call)

    async def edit_message_reply_markup(
        self,
        chat_id: Optional[Union[int, str]] = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
    ) -> Union[Message, bool]:
        """
        Use this method to edit only the reply markup of messages. On success, if edited message
        is sent by the bot, the edited Message is returned, otherwise True is returned.

        Source: https://core.telegram.org/bots/api#editmessagereplymarkup

        :param chat_id: Required if inline_message_id is not specified. Unique identifier for the
        target chat or username of the target channel (in the format
        @channelusername)
        :param message_id: Required if inline_message_id is not specified. Identifier of the
        message to edit
        :param inline_message_id: Required if chat_id and message_id are not specified. Identifier
        of the inline message
        :param reply_markup: A JSON-serialized object for an inline keyboard.
        :return: On success, if edited message is sent by the bot, the edited Message is returned,
        otherwise True is returned.
        """
        call = EditMessageReplyMarkup(
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
            reply_markup=reply_markup,
        )
        return await self(call)

    async def stop_poll(
        self,
        chat_id: Union[int, str],
        message_id: int,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
    ) -> Poll:
        """
        Use this method to stop a poll which was sent by the bot. On success, the stopped Poll
        with the final results is returned.

        Source: https://core.telegram.org/bots/api#stoppoll

        :param chat_id: Unique identifier for the target chat or username of the target channel
        (in the format @channelusername)
        :param message_id: Identifier of the original message with the poll
        :param reply_markup: A JSON-serialized object for a new message inline keyboard.
        :return: On success, the stopped Poll with the final results is returned.
        """
        call = StopPoll(chat_id=chat_id, message_id=message_id, reply_markup=reply_markup,)
        return await self(call)

    async def delete_message(self, chat_id: Union[int, str], message_id: int,) -> bool:
        """
        Use this method to delete a message, including service messages, with the following
        limitations:
        - A message can only be deleted if it was sent less than 48 hours ago.
        - A dice message in a private chat can only be deleted if it was sent more than 24 hours
        ago.
        - Bots can delete outgoing messages in private chats, groups, and supergroups.
        - Bots can delete incoming messages in private chats.
        - Bots granted can_post_messages permissions can delete outgoing messages in channels.
        - If the bot is an administrator of a group, it can delete any message there.
        - If the bot has can_delete_messages permission in a supergroup or a channel, it can
        delete any message there.
        Returns True on success.

        Source: https://core.telegram.org/bots/api#deletemessage

        :param chat_id: Unique identifier for the target chat or username of the target channel
        (in the format @channelusername)
        :param message_id: Identifier of the message to delete
        :return: Returns True on success.
        """
        call = DeleteMessage(chat_id=chat_id, message_id=message_id,)
        return await self(call)

    # =============================================================================================
    # Group: Stickers
    # Source: https://core.telegram.org/bots/api#stickers
    # =============================================================================================

    async def send_sticker(
        self,
        chat_id: Union[int, str],
        sticker: Union[InputFile, str],
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
    ) -> Message:
        """
        Use this method to send static .WEBP or animated .TGS stickers. On success, the sent
        Message is returned.

        Source: https://core.telegram.org/bots/api#sendsticker

        :param chat_id: Unique identifier for the target chat or username of the target channel
        (in the format @channelusername)
        :param sticker: Sticker to send. Pass a file_id as String to send a file that exists on
        the Telegram servers (recommended), pass an HTTP URL as a String for
        Telegram to get a .WEBP file from the Internet, or upload a new one using
        multipart/form-data.
        :param disable_notification: Sends the message silently. Users will receive a notification
        with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param reply_markup: Additional interface options. A JSON-serialized object for an inline
        keyboard, custom reply keyboard, instructions to remove reply
        keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        call = SendSticker(
            chat_id=chat_id,
            sticker=sticker,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup,
        )
        return await self(call)

    async def get_sticker_set(self, name: str,) -> StickerSet:
        """
        Use this method to get a sticker set. On success, a StickerSet object is returned.

        Source: https://core.telegram.org/bots/api#getstickerset

        :param name: Name of the sticker set
        :return: On success, a StickerSet object is returned.
        """
        call = GetStickerSet(name=name,)
        return await self(call)

    async def upload_sticker_file(self, user_id: int, png_sticker: InputFile,) -> File:
        """
        Use this method to upload a .PNG file with a sticker for later use in createNewStickerSet
        and addStickerToSet methods (can be used multiple times). Returns the uploaded File on
        success.

        Source: https://core.telegram.org/bots/api#uploadstickerfile

        :param user_id: User identifier of sticker file owner
        :param png_sticker: PNG image with the sticker, must be up to 512 kilobytes in size,
        dimensions must not exceed 512px, and either width or height must be
        exactly 512px.
        :return: Returns the uploaded File on success.
        """
        call = UploadStickerFile(user_id=user_id, png_sticker=png_sticker,)
        return await self(call)

    async def create_new_sticker_set(
        self,
        user_id: int,
        name: str,
        title: str,
        emojis: str,
        png_sticker: Optional[Union[InputFile, str]] = None,
        tgs_sticker: Optional[InputFile] = None,
        contains_masks: Optional[bool] = None,
        mask_position: Optional[MaskPosition] = None,
    ) -> bool:
        """
        Use this method to create a new sticker set owned by a user. The bot will be able to edit
        the sticker set thus created. You must use exactly one of the fields png_sticker or
        tgs_sticker. Returns True on success.

        Source: https://core.telegram.org/bots/api#createnewstickerset

        :param user_id: User identifier of created sticker set owner
        :param name: Short name of sticker set, to be used in t.me/addstickers/ URLs (e.g.,
        animals). Can contain only english letters, digits and underscores. Must
        begin with a letter, can't contain consecutive underscores and must end in
        '_by_<bot username>'. <bot_username> is case insensitive. 1-64 characters.
        :param title: Sticker set title, 1-64 characters
        :param emojis: One or more emoji corresponding to the sticker
        :param png_sticker: PNG image with the sticker, must be up to 512 kilobytes in size,
        dimensions must not exceed 512px, and either width or height must be
        exactly 512px. Pass a file_id as a String to send a file that already
        exists on the Telegram servers, pass an HTTP URL as a String for
        Telegram to get a file from the Internet, or upload a new one using
        multipart/form-data.
        :param tgs_sticker: TGS animation with the sticker, uploaded using multipart/form-data.
        See https://core.telegram.org/animated_stickers#technical-requirements
        for technical requirements
        :param contains_masks: Pass True, if a set of mask stickers should be created
        :param mask_position: A JSON-serialized object for position where the mask should be
        placed on faces
        :return: Returns True on success.
        """
        call = CreateNewStickerSet(
            user_id=user_id,
            name=name,
            title=title,
            emojis=emojis,
            png_sticker=png_sticker,
            tgs_sticker=tgs_sticker,
            contains_masks=contains_masks,
            mask_position=mask_position,
        )
        return await self(call)

    async def add_sticker_to_set(
        self,
        user_id: int,
        name: str,
        emojis: str,
        png_sticker: Optional[Union[InputFile, str]] = None,
        tgs_sticker: Optional[InputFile] = None,
        mask_position: Optional[MaskPosition] = None,
    ) -> bool:
        """
        Use this method to add a new sticker to a set created by the bot. You must use exactly one
        of the fields png_sticker or tgs_sticker. Animated stickers can be added to animated
        sticker sets and only to them. Animated sticker sets can have up to 50 stickers. Static
        sticker sets can have up to 120 stickers. Returns True on success.

        Source: https://core.telegram.org/bots/api#addstickertoset

        :param user_id: User identifier of sticker set owner
        :param name: Sticker set name
        :param emojis: One or more emoji corresponding to the sticker
        :param png_sticker: PNG image with the sticker, must be up to 512 kilobytes in size,
        dimensions must not exceed 512px, and either width or height must be
        exactly 512px. Pass a file_id as a String to send a file that already
        exists on the Telegram servers, pass an HTTP URL as a String for
        Telegram to get a file from the Internet, or upload a new one using
        multipart/form-data.
        :param tgs_sticker: TGS animation with the sticker, uploaded using multipart/form-data.
        See https://core.telegram.org/animated_stickers#technical-requirements
        for technical requirements
        :param mask_position: A JSON-serialized object for position where the mask should be
        placed on faces
        :return: Returns True on success.
        """
        call = AddStickerToSet(
            user_id=user_id,
            name=name,
            emojis=emojis,
            png_sticker=png_sticker,
            tgs_sticker=tgs_sticker,
            mask_position=mask_position,
        )
        return await self(call)

    async def set_sticker_position_in_set(self, sticker: str, position: int,) -> bool:
        """
        Use this method to move a sticker in a set created by the bot to a specific position.
        Returns True on success.

        Source: https://core.telegram.org/bots/api#setstickerpositioninset

        :param sticker: File identifier of the sticker
        :param position: New sticker position in the set, zero-based
        :return: Returns True on success.
        """
        call = SetStickerPositionInSet(sticker=sticker, position=position,)
        return await self(call)

    async def delete_sticker_from_set(self, sticker: str,) -> bool:
        """
        Use this method to delete a sticker from a set created by the bot. Returns True on
        success.

        Source: https://core.telegram.org/bots/api#deletestickerfromset

        :param sticker: File identifier of the sticker
        :return: Returns True on success.
        """
        call = DeleteStickerFromSet(sticker=sticker,)
        return await self(call)

    async def set_sticker_set_thumb(
        self, name: str, user_id: int, thumb: Optional[Union[InputFile, str]] = None,
    ) -> bool:
        """
        Use this method to set the thumbnail of a sticker set. Animated thumbnails can be set for
        animated sticker sets only. Returns True on success.

        Source: https://core.telegram.org/bots/api#setstickersetthumb

        :param name: Sticker set name
        :param user_id: User identifier of the sticker set owner
        :param thumb: A PNG image with the thumbnail, must be up to 128 kilobytes in size and have
        width and height exactly 100px, or a TGS animation with the thumbnail up to
        32 kilobytes in size; see
        https://core.telegram.org/animated_stickers#technical-requirements for
        animated sticker technical requirements. Pass a file_id as a String to send
        a file that already exists on the Telegram servers, pass an HTTP URL as a
        String for Telegram to get a file from the Internet, or upload a new one
        using multipart/form-data.. Animated sticker set thumbnail can't be uploaded
        via HTTP URL.
        :return: Returns True on success.
        """
        call = SetStickerSetThumb(name=name, user_id=user_id, thumb=thumb,)
        return await self(call)

    # =============================================================================================
    # Group: Inline mode
    # Source: https://core.telegram.org/bots/api#inline-mode
    # =============================================================================================

    async def answer_inline_query(
        self,
        inline_query_id: str,
        results: List[InlineQueryResult],
        cache_time: Optional[int] = None,
        is_personal: Optional[bool] = None,
        next_offset: Optional[str] = None,
        switch_pm_text: Optional[str] = None,
        switch_pm_parameter: Optional[str] = None,
    ) -> bool:
        """
        Use this method to send answers to an inline query. On success, True is returned.
        No more than 50 results per query are allowed.

        Source: https://core.telegram.org/bots/api#answerinlinequery

        :param inline_query_id: Unique identifier for the answered query
        :param results: A JSON-serialized array of results for the inline query
        :param cache_time: The maximum amount of time in seconds that the result of the inline
        query may be cached on the server. Defaults to 300.
        :param is_personal: Pass True, if results may be cached on the server side only for the
        user that sent the query. By default, results may be returned to any
        user who sends the same query
        :param next_offset: Pass the offset that a client should send in the next query with the
        same text to receive more results. Pass an empty string if there are
        no more results or if you don‘t support pagination. Offset length
        can’t exceed 64 bytes.
        :param switch_pm_text: If passed, clients will display a button with specified text that
        switches the user to a private chat with the bot and sends the bot
        a start message with the parameter switch_pm_parameter
        :param switch_pm_parameter: Deep-linking parameter for the /start message sent to the bot
        when user presses the switch button. 1-64 characters, only
        A-Z, a-z, 0-9, _ and - are allowed.
        :return: On success, True is returned.
        """
        call = AnswerInlineQuery(
            inline_query_id=inline_query_id,
            results=results,
            cache_time=cache_time,
            is_personal=is_personal,
            next_offset=next_offset,
            switch_pm_text=switch_pm_text,
            switch_pm_parameter=switch_pm_parameter,
        )
        return await self(call)

    # =============================================================================================
    # Group: Payments
    # Source: https://core.telegram.org/bots/api#payments
    # =============================================================================================

    async def send_invoice(
        self,
        chat_id: int,
        title: str,
        description: str,
        payload: str,
        provider_token: str,
        start_parameter: str,
        currency: str,
        prices: List[LabeledPrice],
        provider_data: Optional[str] = None,
        photo_url: Optional[str] = None,
        photo_size: Optional[int] = None,
        photo_width: Optional[int] = None,
        photo_height: Optional[int] = None,
        need_name: Optional[bool] = None,
        need_phone_number: Optional[bool] = None,
        need_email: Optional[bool] = None,
        need_shipping_address: Optional[bool] = None,
        send_phone_number_to_provider: Optional[bool] = None,
        send_email_to_provider: Optional[bool] = None,
        is_flexible: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
    ) -> Message:
        """
        Use this method to send invoices. On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#sendinvoice

        :param chat_id: Unique identifier for the target private chat
        :param title: Product name, 1-32 characters
        :param description: Product description, 1-255 characters
        :param payload: Bot-defined invoice payload, 1-128 bytes. This will not be displayed to
        the user, use for your internal processes.
        :param provider_token: Payments provider token, obtained via Botfather
        :param start_parameter: Unique deep-linking parameter that can be used to generate this
        invoice when used as a start parameter
        :param currency: Three-letter ISO 4217 currency code, see more on currencies
        :param prices: Price breakdown, a JSON-serialized list of components (e.g. product price,
        tax, discount, delivery cost, delivery tax, bonus, etc.)
        :param provider_data: JSON-encoded data about the invoice, which will be shared with the
        payment provider. A detailed description of required fields should
        be provided by the payment provider.
        :param photo_url: URL of the product photo for the invoice. Can be a photo of the goods or
        a marketing image for a service. People like it better when they see
        what they are paying for.
        :param photo_size: Photo size
        :param photo_width: Photo width
        :param photo_height: Photo height
        :param need_name: Pass True, if you require the user's full name to complete the order
        :param need_phone_number: Pass True, if you require the user's phone number to complete
        the order
        :param need_email: Pass True, if you require the user's email address to complete the
        order
        :param need_shipping_address: Pass True, if you require the user's shipping address to
        complete the order
        :param send_phone_number_to_provider: Pass True, if user's phone number should be sent to
        provider
        :param send_email_to_provider: Pass True, if user's email address should be sent to
        provider
        :param is_flexible: Pass True, if the final price depends on the shipping method
        :param disable_notification: Sends the message silently. Users will receive a notification
        with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param reply_markup: A JSON-serialized object for an inline keyboard. If empty, one 'Pay
        total price' button will be shown. If not empty, the first button
        must be a Pay button.
        :return: On success, the sent Message is returned.
        """
        call = SendInvoice(
            chat_id=chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token=provider_token,
            start_parameter=start_parameter,
            currency=currency,
            prices=prices,
            provider_data=provider_data,
            photo_url=photo_url,
            photo_size=photo_size,
            photo_width=photo_width,
            photo_height=photo_height,
            need_name=need_name,
            need_phone_number=need_phone_number,
            need_email=need_email,
            need_shipping_address=need_shipping_address,
            send_phone_number_to_provider=send_phone_number_to_provider,
            send_email_to_provider=send_email_to_provider,
            is_flexible=is_flexible,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup,
        )
        return await self(call)

    async def answer_shipping_query(
        self,
        shipping_query_id: str,
        ok: bool,
        shipping_options: Optional[List[ShippingOption]] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        If you sent an invoice requesting a shipping address and the parameter is_flexible was
        specified, the Bot API will send an Update with a shipping_query field to the bot. Use
        this method to reply to shipping queries. On success, True is returned.

        Source: https://core.telegram.org/bots/api#answershippingquery

        :param shipping_query_id: Unique identifier for the query to be answered
        :param ok: Specify True if delivery to the specified address is possible and False if
        there are any problems (for example, if delivery to the specified address is
        not possible)
        :param shipping_options: Required if ok is True. A JSON-serialized array of available
        shipping options.
        :param error_message: Required if ok is False. Error message in human readable form that
        explains why it is impossible to complete the order (e.g. "Sorry,
        delivery to your desired address is unavailable'). Telegram will
        display this message to the user.
        :return: On success, True is returned.
        """
        call = AnswerShippingQuery(
            shipping_query_id=shipping_query_id,
            ok=ok,
            shipping_options=shipping_options,
            error_message=error_message,
        )
        return await self(call)

    async def answer_pre_checkout_query(
        self, pre_checkout_query_id: str, ok: bool, error_message: Optional[str] = None,
    ) -> bool:
        """
        Once the user has confirmed their payment and shipping details, the Bot API sends the
        final confirmation in the form of an Update with the field pre_checkout_query. Use this
        method to respond to such pre-checkout queries. On success, True is returned. Note: The
        Bot API must receive an answer within 10 seconds after the pre-checkout query was sent.

        Source: https://core.telegram.org/bots/api#answerprecheckoutquery

        :param pre_checkout_query_id: Unique identifier for the query to be answered
        :param ok: Specify True if everything is alright (goods are available, etc.) and the bot
        is ready to proceed with the order. Use False if there are any problems.
        :param error_message: Required if ok is False. Error message in human readable form that
        explains the reason for failure to proceed with the checkout (e.g.
        "Sorry, somebody just bought the last of our amazing black T-shirts
        while you were busy filling out your payment details. Please choose
        a different color or garment!"). Telegram will display this message
        to the user.
        :return: On success, True is returned.
        """
        call = AnswerPreCheckoutQuery(
            pre_checkout_query_id=pre_checkout_query_id, ok=ok, error_message=error_message,
        )
        return await self(call)

    # =============================================================================================
    # Group: Telegram Passport
    # Source: https://core.telegram.org/bots/api#telegram-passport
    # =============================================================================================

    async def set_passport_data_errors(
        self, user_id: int, errors: List[PassportElementError],
    ) -> bool:
        """
        Informs a user that some of the Telegram Passport elements they provided contains errors.
        The user will not be able to re-submit their Passport to you until the errors are fixed
        (the contents of the field for which you returned the error must change). Returns True on
        success.
        Use this if the data submitted by the user doesn't satisfy the standards your service
        requires for any reason. For example, if a birthday date seems invalid, a submitted
        document is blurry, a scan shows evidence of tampering, etc. Supply some details in the
        error message to make sure the user knows how to correct the issues.

        Source: https://core.telegram.org/bots/api#setpassportdataerrors

        :param user_id: User identifier
        :param errors: A JSON-serialized array describing the errors
        :return: The user will not be able to re-submit their Passport to you until the errors are
        fixed (the contents of the field for which you returned the error must change).
        Returns True on success.
        """
        call = SetPassportDataErrors(user_id=user_id, errors=errors,)
        return await self(call)

    # =============================================================================================
    # Group: Games
    # Source: https://core.telegram.org/bots/api#games
    # =============================================================================================

    async def send_game(
        self,
        chat_id: int,
        game_short_name: str,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
    ) -> Message:
        """
        Use this method to send a game. On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#sendgame

        :param chat_id: Unique identifier for the target chat
        :param game_short_name: Short name of the game, serves as the unique identifier for the
        game. Set up your games via Botfather.
        :param disable_notification: Sends the message silently. Users will receive a notification
        with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param reply_markup: A JSON-serialized object for an inline keyboard. If empty, one ‘Play
        game_title’ button will be shown. If not empty, the first button must
        launch the game.
        :return: On success, the sent Message is returned.
        """
        call = SendGame(
            chat_id=chat_id,
            game_short_name=game_short_name,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup,
        )
        return await self(call)

    async def set_game_score(
        self,
        user_id: int,
        score: int,
        force: Optional[bool] = None,
        disable_edit_message: Optional[bool] = None,
        chat_id: Optional[int] = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
    ) -> Union[Message, bool]:
        """
        Use this method to set the score of the specified user in a game. On success, if the
        message was sent by the bot, returns the edited Message, otherwise returns True. Returns
        an error, if the new score is not greater than the user's current score in the chat and
        force is False.

        Source: https://core.telegram.org/bots/api#setgamescore

        :param user_id: User identifier
        :param score: New score, must be non-negative
        :param force: Pass True, if the high score is allowed to decrease. This can be useful when
        fixing mistakes or banning cheaters
        :param disable_edit_message: Pass True, if the game message should not be automatically
        edited to include the current scoreboard
        :param chat_id: Required if inline_message_id is not specified. Unique identifier for the
        target chat
        :param message_id: Required if inline_message_id is not specified. Identifier of the sent
        message
        :param inline_message_id: Required if chat_id and message_id are not specified. Identifier
        of the inline message
        :return: On success, if the message was sent by the bot, returns the edited Message,
        otherwise returns True. Returns an error, if the new score is not greater than
        the user's current score in the chat and force is False.
        """
        call = SetGameScore(
            user_id=user_id,
            score=score,
            force=force,
            disable_edit_message=disable_edit_message,
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
        )
        return await self(call)

    async def get_game_high_scores(
        self,
        user_id: int,
        chat_id: Optional[int] = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
    ) -> List[GameHighScore]:
        """
        Use this method to get data for high score tables. Will return the score of the specified
        user and several of their neighbors in a game. On success, returns an Array of
        GameHighScore objects.
        This method will currently return scores for the target user, plus two of their closest
        neighbors on each side. Will also return the top three users if the user and his neighbors
        are not among them. Please note that this behavior is subject to change.

        Source: https://core.telegram.org/bots/api#getgamehighscores

        :param user_id: Target user id
        :param chat_id: Required if inline_message_id is not specified. Unique identifier for the
        target chat
        :param message_id: Required if inline_message_id is not specified. Identifier of the sent
        message
        :param inline_message_id: Required if chat_id and message_id are not specified. Identifier
        of the inline message
        :return: Will return the score of the specified user and several of their neighbors in a
        game. On success, returns an Array of GameHighScore objects. This method will
        currently return scores for the target user, plus two of their closest neighbors
        on each side. Will also return the top three users if the user and his neighbors
        are not among them.
        """
        call = GetGameHighScores(
            user_id=user_id,
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
        )
        return await self(call)
