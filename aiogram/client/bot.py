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

from aiogram.utils.mixins import ContextInstanceMixin
from aiogram.utils.token import extract_bot_id, validate_token

from ..methods import (
    AddStickerToSet,
    AnswerCallbackQuery,
    AnswerInlineQuery,
    AnswerPreCheckoutQuery,
    AnswerShippingQuery,
    BanChatMember,
    Close,
    CopyMessage,
    CreateChatInviteLink,
    CreateNewStickerSet,
    DeleteChatPhoto,
    DeleteChatStickerSet,
    DeleteMessage,
    DeleteMyCommands,
    DeleteStickerFromSet,
    DeleteWebhook,
    EditChatInviteLink,
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
    GetChatMemberCount,
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
    LogOut,
    PinChatMessage,
    PromoteChatMember,
    RestrictChatMember,
    RevokeChatInviteLink,
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
    UnpinAllChatMessages,
    UnpinChatMessage,
    UploadStickerFile,
)
from ..types import (
    UNSET,
    BotCommand,
    BotCommandScope,
    Chat,
    ChatInviteLink,
    ChatMemberAdministrator,
    ChatMemberBanned,
    ChatMemberLeft,
    ChatMemberMember,
    ChatMemberOwner,
    ChatMemberRestricted,
    ChatPermissions,
    Downloadable,
    File,
    ForceReply,
    GameHighScore,
    InlineKeyboardMarkup,
    InlineQueryResult,
    InputFile,
    InputMedia,
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    LabeledPrice,
    MaskPosition,
    Message,
    MessageEntity,
    MessageId,
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
    def __init__(
        self,
        token: str,
        session: Optional[BaseSession] = None,
        parse_mode: Optional[str] = None,
    ) -> None:
        """
        Bot class

        :param token: Telegram Bot token `Obtained from @BotFather <https://t.me/BotFather>`_
        :param session: HTTP Client session (For example AiohttpSession).
            If not specified it will be automatically created.
        :param parse_mode: Default parse mode.
            If specified it will be propagated into the API methods at runtime.
        :raise TokenValidationError: When token has invalid format this exception will be raised
        """

        validate_token(token)

        if session is None:
            session = AiohttpSession()

        self.session = session
        self.parse_mode = parse_mode
        self.__token = token

    @property
    def token(self) -> str:
        return self.__token

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
                await self.session.close()
            self.reset_current(token)

    @alru_cache()  # type: ignore
    async def me(self) -> User:
        return await self.get_me()

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

    @classmethod
    async def __aiofiles_reader(
        cls, file: str, chunk_size: int = 65536
    ) -> AsyncGenerator[bytes, None]:
        async with aiofiles.open(file, "rb") as f:
            while chunk := await f.read(chunk_size):
                yield chunk

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

        close_stream = False
        if self.session.api.is_local:
            stream = self.__aiofiles_reader(
                self.session.api.wrap_local_file(file_path), chunk_size=chunk_size
            )
            close_stream = True
        else:
            url = self.session.api.file_url(self.__token, file_path)
            stream = self.session.stream_content(url=url, timeout=timeout, chunk_size=chunk_size)

        try:
            if isinstance(destination, (str, pathlib.Path)):
                return await self.__download_file(destination=destination, stream=stream)
            else:
                return await self.__download_file_binary_io(
                    destination=destination, seek=seek, stream=stream
                )
        finally:
            if close_stream:
                await stream.aclose()

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

        file_ = await self.get_file(file_id)

        # `file_path` can be None for large files but this files can't be downloaded
        # So we need to do type-cast
        # https://github.com/aiogram/aiogram/pull/282/files#r394110017
        file_path = cast(str, file_.file_path)

        return await self.download_file(
            file_path, destination=destination, timeout=timeout, chunk_size=chunk_size, seek=seek
        )

    async def __call__(
        self, method: TelegramMethod[T], request_timeout: Optional[int] = None
    ) -> T:
        """
        Call API method

        :param method:
        :return:
        """
        return await self.session(self, method, timeout=request_timeout)

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
        request_timeout: Optional[int] = None,
    ) -> List[Update]:
        """
        Use this method to receive incoming updates using long polling (`wiki <https://en.wikipedia.org/wiki/Push_technology#Long_polling>`_). An Array of :class:`aiogram.types.update.Update` objects is returned.

         **Notes**

         **1.** This method will not work if an outgoing webhook is set up.

         **2.** In order to avoid getting duplicate updates, recalculate *offset* after each server response.

        Source: https://core.telegram.org/bots/api#getupdates

        :param offset: Identifier of the first update to be returned. Must be greater by one than the highest among the identifiers of previously received updates. By default, updates starting with the earliest unconfirmed update are returned. An update is considered confirmed as soon as :class:`aiogram.methods.get_updates.GetUpdates` is called with an *offset* higher than its *update_id*. The negative offset can be specified to retrieve updates starting from *-offset* update from the end of the updates queue. All previous updates will forgotten.
        :param limit: Limits the number of updates to be retrieved. Values between 1-100 are accepted. Defaults to 100.
        :param timeout: Timeout in seconds for long polling. Defaults to 0, i.e. usual short polling. Should be positive, short polling should be used for testing purposes only.
        :param allowed_updates: A JSON-serialized list of the update types you want your bot to receive. For example, specify ['message', 'edited_channel_post', 'callback_query'] to only receive updates of these types. See :class:`aiogram.types.update.Update` for a complete list of available update types. Specify an empty list to receive all update types except *chat_member* (default). If not specified, the previous setting will be used.
        :param request_timeout: Request timeout
        :return: An Array of Update objects is returned.
        """
        call = GetUpdates(
            offset=offset,
            limit=limit,
            timeout=timeout,
            allowed_updates=allowed_updates,
        )
        return await self(call, request_timeout=request_timeout)

    async def set_webhook(
        self,
        url: str,
        certificate: Optional[InputFile] = None,
        ip_address: Optional[str] = None,
        max_connections: Optional[int] = None,
        allowed_updates: Optional[List[str]] = None,
        drop_pending_updates: Optional[bool] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to specify a url and receive incoming updates via an outgoing webhook. Whenever there is an update for the bot, we will send an HTTPS POST request to the specified url, containing a JSON-serialized :class:`aiogram.types.update.Update`. In case of an unsuccessful request, we will give up after a reasonable amount of attempts. Returns :code:`True` on success.
        If you'd like to make sure that the Webhook request comes from Telegram, we recommend using a secret path in the URL, e.g. :code:`https://www.example.com/<token>`. Since nobody else knows your bot's token, you can be pretty sure it's us.

         **Notes**

         **1.** You will not be able to receive updates using :class:`aiogram.methods.get_updates.GetUpdates` for as long as an outgoing webhook is set up.

         **2.** To use a self-signed certificate, you need to upload your `public key certificate <https://core.telegram.org/bots/self-signed>`_ using *certificate* parameter. Please upload as InputFile, sending a String will not work.

         **3.** Ports currently supported *for Webhooks*: **443, 80, 88, 8443**.
         **NEW!** If you're having any trouble setting up webhooks, please check out this `amazing guide to Webhooks <https://core.telegram.org/bots/webhooks>`_.

        Source: https://core.telegram.org/bots/api#setwebhook

        :param url: HTTPS url to send updates to. Use an empty string to remove webhook integration
        :param certificate: Upload your public key certificate so that the root certificate in use can be checked. See our `self-signed guide <https://core.telegram.org/bots/self-signed>`_ for details.
        :param ip_address: The fixed IP address which will be used to send webhook requests instead of the IP address resolved through DNS
        :param max_connections: Maximum allowed number of simultaneous HTTPS connections to the webhook for update delivery, 1-100. Defaults to *40*. Use lower values to limit the load on your bot's server, and higher values to increase your bot's throughput.
        :param allowed_updates: A JSON-serialized list of the update types you want your bot to receive. For example, specify ['message', 'edited_channel_post', 'callback_query'] to only receive updates of these types. See :class:`aiogram.types.update.Update` for a complete list of available update types. Specify an empty list to receive all update types except *chat_member* (default). If not specified, the previous setting will be used.
        :param drop_pending_updates: Pass :code:`True` to drop all pending updates
        :param request_timeout: Request timeout
        :return: Returns True on success.
        """
        call = SetWebhook(
            url=url,
            certificate=certificate,
            ip_address=ip_address,
            max_connections=max_connections,
            allowed_updates=allowed_updates,
            drop_pending_updates=drop_pending_updates,
        )
        return await self(call, request_timeout=request_timeout)

    async def delete_webhook(
        self,
        drop_pending_updates: Optional[bool] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to remove webhook integration if you decide to switch back to :class:`aiogram.methods.get_updates.GetUpdates`. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#deletewebhook

        :param drop_pending_updates: Pass :code:`True` to drop all pending updates
        :param request_timeout: Request timeout
        :return: Returns True on success.
        """
        call = DeleteWebhook(
            drop_pending_updates=drop_pending_updates,
        )
        return await self(call, request_timeout=request_timeout)

    async def get_webhook_info(
        self,
        request_timeout: Optional[int] = None,
    ) -> WebhookInfo:
        """
        Use this method to get current webhook status. Requires no parameters. On success, returns a :class:`aiogram.types.webhook_info.WebhookInfo` object. If the bot is using :class:`aiogram.methods.get_updates.GetUpdates`, will return an object with the *url* field empty.

        Source: https://core.telegram.org/bots/api#getwebhookinfo

        :param request_timeout: Request timeout
        :return: On success, returns a WebhookInfo object. If the bot is using getUpdates, will
            return an object with the url field empty.
        """
        call = GetWebhookInfo()
        return await self(call, request_timeout=request_timeout)

    # =============================================================================================
    # Group: Available methods
    # Source: https://core.telegram.org/bots/api#available-methods
    # =============================================================================================

    async def get_me(
        self,
        request_timeout: Optional[int] = None,
    ) -> User:
        """
        A simple method for testing your bot's auth token. Requires no parameters. Returns basic information about the bot in form of a :class:`aiogram.types.user.User` object.

        Source: https://core.telegram.org/bots/api#getme

        :param request_timeout: Request timeout
        :return: Returns basic information about the bot in form of a User object.
        """
        call = GetMe()
        return await self(call, request_timeout=request_timeout)

    async def log_out(
        self,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to log out from the cloud Bot API server before launching the bot locally. You **must** log out the bot before running it locally, otherwise there is no guarantee that the bot will receive updates. After a successful call, you can immediately log in on a local server, but will not be able to log in back to the cloud Bot API server for 10 minutes. Returns :code:`True` on success. Requires no parameters.

        Source: https://core.telegram.org/bots/api#logout

        :param request_timeout: Request timeout
        :return: Returns True on success.
        """
        call = LogOut()
        return await self(call, request_timeout=request_timeout)

    async def close(
        self,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to close the bot instance before moving it from one local server to another. You need to delete the webhook before calling this method to ensure that the bot isn't launched again after server restart. The method will return error 429 in the first 10 minutes after the bot is launched. Returns :code:`True` on success. Requires no parameters.

        Source: https://core.telegram.org/bots/api#close

        :param request_timeout: Request timeout
        :return: The method will return error 429 in the first 10 minutes after the bot is
            launched. Returns True on success.
        """
        call = Close()
        return await self(call, request_timeout=request_timeout)

    async def send_message(
        self,
        chat_id: Union[int, str],
        text: str,
        parse_mode: Optional[str] = UNSET,
        entities: Optional[List[MessageEntity]] = None,
        disable_web_page_preview: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        Use this method to send text messages. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendmessage

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param text: Text of the message to be sent, 1-4096 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the message text. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param entities: List of special entities that appear in message text, which can be specified instead of *parse_mode*
        :param disable_web_page_preview: Disables link previews for links in this message
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True`, if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_, `custom reply keyboard <https://core.telegram.org/bots#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.
        :param request_timeout: Request timeout
        :return: On success, the sent Message is returned.
        """
        call = SendMessage(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            entities=entities,
            disable_web_page_preview=disable_web_page_preview,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def forward_message(
        self,
        chat_id: Union[int, str],
        from_chat_id: Union[int, str],
        message_id: int,
        disable_notification: Optional[bool] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        Use this method to forward messages of any kind. Service messages can't be forwarded. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#forwardmessage

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param from_chat_id: Unique identifier for the chat where the original message was sent (or channel username in the format :code:`@channelusername`)
        :param message_id: Message identifier in the chat specified in *from_chat_id*
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param request_timeout: Request timeout
        :return: On success, the sent Message is returned.
        """
        call = ForwardMessage(
            chat_id=chat_id,
            from_chat_id=from_chat_id,
            message_id=message_id,
            disable_notification=disable_notification,
        )
        return await self(call, request_timeout=request_timeout)

    async def copy_message(
        self,
        chat_id: Union[int, str],
        from_chat_id: Union[int, str],
        message_id: int,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET,
        caption_entities: Optional[List[MessageEntity]] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        request_timeout: Optional[int] = None,
    ) -> MessageId:
        """
        Use this method to copy messages of any kind. Service messages and invoice messages can't be copied. The method is analogous to the method :class:`aiogram.methods.forward_message.ForwardMessage`, but the copied message doesn't have a link to the original message. Returns the :class:`aiogram.types.message_id.MessageId` of the sent message on success.

        Source: https://core.telegram.org/bots/api#copymessage

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param from_chat_id: Unique identifier for the chat where the original message was sent (or channel username in the format :code:`@channelusername`)
        :param message_id: Message identifier in the chat specified in *from_chat_id*
        :param caption: New caption for media, 0-1024 characters after entities parsing. If not specified, the original caption is kept
        :param parse_mode: Mode for parsing entities in the new caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: List of special entities that appear in the new caption, which can be specified instead of *parse_mode*
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True`, if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_, `custom reply keyboard <https://core.telegram.org/bots#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.
        :param request_timeout: Request timeout
        :return: Returns the MessageId of the sent message on success.
        """
        call = CopyMessage(
            chat_id=chat_id,
            from_chat_id=from_chat_id,
            message_id=message_id,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def send_photo(
        self,
        chat_id: Union[int, str],
        photo: Union[InputFile, str],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET,
        caption_entities: Optional[List[MessageEntity]] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        Use this method to send photos. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendphoto

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param photo: Photo to send. Pass a file_id as String to send a photo that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a photo from the Internet, or upload a new photo using multipart/form-data. The photo must be at most 10 MB in size. The photo's width and height must not exceed 10000 in total. Width and height ratio must be at most 20. :ref:`More info on Sending Files » <sending-files>`
        :param caption: Photo caption (may also be used when resending photos by *file_id*), 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the photo caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: List of special entities that appear in the caption, which can be specified instead of *parse_mode*
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True`, if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_, `custom reply keyboard <https://core.telegram.org/bots#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.
        :param request_timeout: Request timeout
        :return: On success, the sent Message is returned.
        """
        call = SendPhoto(
            chat_id=chat_id,
            photo=photo,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def send_audio(
        self,
        chat_id: Union[int, str],
        audio: Union[InputFile, str],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET,
        caption_entities: Optional[List[MessageEntity]] = None,
        duration: Optional[int] = None,
        performer: Optional[str] = None,
        title: Optional[str] = None,
        thumb: Optional[Union[InputFile, str]] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        Use this method to send audio files, if you want Telegram clients to display them in the music player. Your audio must be in the .MP3 or .M4A format. On success, the sent :class:`aiogram.types.message.Message` is returned. Bots can currently send audio files of up to 50 MB in size, this limit may be changed in the future.
        For sending voice messages, use the :class:`aiogram.methods.send_voice.SendVoice` method instead.

        Source: https://core.telegram.org/bots/api#sendaudio

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param audio: Audio file to send. Pass a file_id as String to send an audio file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get an audio file from the Internet, or upload a new one using multipart/form-data. :ref:`More info on Sending Files » <sending-files>`
        :param caption: Audio caption, 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the audio caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: List of special entities that appear in the caption, which can be specified instead of *parse_mode*
        :param duration: Duration of the audio in seconds
        :param performer: Performer
        :param title: Track name
        :param thumb: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. :ref:`More info on Sending Files » <sending-files>`
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True`, if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_, `custom reply keyboard <https://core.telegram.org/bots#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.
        :param request_timeout: Request timeout
        :return: On success, the sent Message is returned.
        """
        call = SendAudio(
            chat_id=chat_id,
            audio=audio,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            duration=duration,
            performer=performer,
            title=title,
            thumb=thumb,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def send_document(
        self,
        chat_id: Union[int, str],
        document: Union[InputFile, str],
        thumb: Optional[Union[InputFile, str]] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET,
        caption_entities: Optional[List[MessageEntity]] = None,
        disable_content_type_detection: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        Use this method to send general files. On success, the sent :class:`aiogram.types.message.Message` is returned. Bots can currently send files of any type of up to 50 MB in size, this limit may be changed in the future.

        Source: https://core.telegram.org/bots/api#senddocument

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param document: File to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. :ref:`More info on Sending Files » <sending-files>`
        :param thumb: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. :ref:`More info on Sending Files » <sending-files>`
        :param caption: Document caption (may also be used when resending documents by *file_id*), 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the document caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: List of special entities that appear in the caption, which can be specified instead of *parse_mode*
        :param disable_content_type_detection: Disables automatic server-side content type detection for files uploaded using multipart/form-data
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True`, if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_, `custom reply keyboard <https://core.telegram.org/bots#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.
        :param request_timeout: Request timeout
        :return: On success, the sent Message is returned.
        """
        call = SendDocument(
            chat_id=chat_id,
            document=document,
            thumb=thumb,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            disable_content_type_detection=disable_content_type_detection,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def send_video(
        self,
        chat_id: Union[int, str],
        video: Union[InputFile, str],
        duration: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        thumb: Optional[Union[InputFile, str]] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET,
        caption_entities: Optional[List[MessageEntity]] = None,
        supports_streaming: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        Use this method to send video files, Telegram clients support mp4 videos (other formats may be sent as :class:`aiogram.types.document.Document`). On success, the sent :class:`aiogram.types.message.Message` is returned. Bots can currently send video files of up to 50 MB in size, this limit may be changed in the future.

        Source: https://core.telegram.org/bots/api#sendvideo

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param video: Video to send. Pass a file_id as String to send a video that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a video from the Internet, or upload a new video using multipart/form-data. :ref:`More info on Sending Files » <sending-files>`
        :param duration: Duration of sent video in seconds
        :param width: Video width
        :param height: Video height
        :param thumb: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. :ref:`More info on Sending Files » <sending-files>`
        :param caption: Video caption (may also be used when resending videos by *file_id*), 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the video caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: List of special entities that appear in the caption, which can be specified instead of *parse_mode*
        :param supports_streaming: Pass :code:`True`, if the uploaded video is suitable for streaming
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True`, if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_, `custom reply keyboard <https://core.telegram.org/bots#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.
        :param request_timeout: Request timeout
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
            caption_entities=caption_entities,
            supports_streaming=supports_streaming,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def send_animation(
        self,
        chat_id: Union[int, str],
        animation: Union[InputFile, str],
        duration: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        thumb: Optional[Union[InputFile, str]] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET,
        caption_entities: Optional[List[MessageEntity]] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        Use this method to send animation files (GIF or H.264/MPEG-4 AVC video without sound). On success, the sent :class:`aiogram.types.message.Message` is returned. Bots can currently send animation files of up to 50 MB in size, this limit may be changed in the future.

        Source: https://core.telegram.org/bots/api#sendanimation

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param animation: Animation to send. Pass a file_id as String to send an animation that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get an animation from the Internet, or upload a new animation using multipart/form-data. :ref:`More info on Sending Files » <sending-files>`
        :param duration: Duration of sent animation in seconds
        :param width: Animation width
        :param height: Animation height
        :param thumb: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. :ref:`More info on Sending Files » <sending-files>`
        :param caption: Animation caption (may also be used when resending animation by *file_id*), 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the animation caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: List of special entities that appear in the caption, which can be specified instead of *parse_mode*
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True`, if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_, `custom reply keyboard <https://core.telegram.org/bots#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.
        :param request_timeout: Request timeout
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
            caption_entities=caption_entities,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def send_voice(
        self,
        chat_id: Union[int, str],
        voice: Union[InputFile, str],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET,
        caption_entities: Optional[List[MessageEntity]] = None,
        duration: Optional[int] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        Use this method to send audio files, if you want Telegram clients to display the file as a playable voice message. For this to work, your audio must be in an .OGG file encoded with OPUS (other formats may be sent as :class:`aiogram.types.audio.Audio` or :class:`aiogram.types.document.Document`). On success, the sent :class:`aiogram.types.message.Message` is returned. Bots can currently send voice messages of up to 50 MB in size, this limit may be changed in the future.

        Source: https://core.telegram.org/bots/api#sendvoice

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param voice: Audio file to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. :ref:`More info on Sending Files » <sending-files>`
        :param caption: Voice message caption, 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the voice message caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: List of special entities that appear in the caption, which can be specified instead of *parse_mode*
        :param duration: Duration of the voice message in seconds
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True`, if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_, `custom reply keyboard <https://core.telegram.org/bots#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.
        :param request_timeout: Request timeout
        :return: On success, the sent Message is returned.
        """
        call = SendVoice(
            chat_id=chat_id,
            voice=voice,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            duration=duration,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def send_video_note(
        self,
        chat_id: Union[int, str],
        video_note: Union[InputFile, str],
        duration: Optional[int] = None,
        length: Optional[int] = None,
        thumb: Optional[Union[InputFile, str]] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        As of `v.4.0 <https://telegram.org/blog/video-messages-and-telescope>`_, Telegram clients support rounded square mp4 videos of up to 1 minute long. Use this method to send video messages. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendvideonote

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param video_note: Video note to send. Pass a file_id as String to send a video note that exists on the Telegram servers (recommended) or upload a new video using multipart/form-data. :ref:`More info on Sending Files » <sending-files>`. Sending video notes by a URL is currently unsupported
        :param duration: Duration of sent video in seconds
        :param length: Video width and height, i.e. diameter of the video message
        :param thumb: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. :ref:`More info on Sending Files » <sending-files>`
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True`, if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_, `custom reply keyboard <https://core.telegram.org/bots#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.
        :param request_timeout: Request timeout
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
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def send_media_group(
        self,
        chat_id: Union[int, str],
        media: List[Union[InputMediaAudio, InputMediaDocument, InputMediaPhoto, InputMediaVideo]],
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        request_timeout: Optional[int] = None,
    ) -> List[Message]:
        """
        Use this method to send a group of photos, videos, documents or audios as an album. Documents and audio files can be only grouped in an album with messages of the same type. On success, an array of `Messages <https://core.telegram.org/bots/api#message>`_ that were sent is returned.

        Source: https://core.telegram.org/bots/api#sendmediagroup

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param media: A JSON-serialized array describing messages to be sent, must include 2-10 items
        :param disable_notification: Sends messages `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param reply_to_message_id: If the messages are a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True`, if the message should be sent even if the specified replied-to message is not found
        :param request_timeout: Request timeout
        :return: On success, an array of Messages that were sent is returned.
        """
        call = SendMediaGroup(
            chat_id=chat_id,
            media=media,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
        )
        return await self(call, request_timeout=request_timeout)

    async def send_location(
        self,
        chat_id: Union[int, str],
        latitude: float,
        longitude: float,
        horizontal_accuracy: Optional[float] = None,
        live_period: Optional[int] = None,
        heading: Optional[int] = None,
        proximity_alert_radius: Optional[int] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        Use this method to send point on the map. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendlocation

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param latitude: Latitude of the location
        :param longitude: Longitude of the location
        :param horizontal_accuracy: The radius of uncertainty for the location, measured in meters; 0-1500
        :param live_period: Period in seconds for which the location will be updated (see `Live Locations <https://telegram.org/blog/live-locations>`_, should be between 60 and 86400.
        :param heading: For live locations, a direction in which the user is moving, in degrees. Must be between 1 and 360 if specified.
        :param proximity_alert_radius: For live locations, a maximum distance for proximity alerts about approaching another chat member, in meters. Must be between 1 and 100000 if specified.
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True`, if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_, `custom reply keyboard <https://core.telegram.org/bots#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.
        :param request_timeout: Request timeout
        :return: On success, the sent Message is returned.
        """
        call = SendLocation(
            chat_id=chat_id,
            latitude=latitude,
            longitude=longitude,
            horizontal_accuracy=horizontal_accuracy,
            live_period=live_period,
            heading=heading,
            proximity_alert_radius=proximity_alert_radius,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def edit_message_live_location(
        self,
        latitude: float,
        longitude: float,
        chat_id: Optional[Union[int, str]] = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
        horizontal_accuracy: Optional[float] = None,
        heading: Optional[int] = None,
        proximity_alert_radius: Optional[int] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        request_timeout: Optional[int] = None,
    ) -> Union[Message, bool]:
        """
        Use this method to edit live location messages. A location can be edited until its *live_period* expires or editing is explicitly disabled by a call to :class:`aiogram.methods.stop_message_live_location.StopMessageLiveLocation`. On success, if the edited message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned.

        Source: https://core.telegram.org/bots/api#editmessagelivelocation

        :param latitude: Latitude of new location
        :param longitude: Longitude of new location
        :param chat_id: Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param message_id: Required if *inline_message_id* is not specified. Identifier of the message to edit
        :param inline_message_id: Required if *chat_id* and *message_id* are not specified. Identifier of the inline message
        :param horizontal_accuracy: The radius of uncertainty for the location, measured in meters; 0-1500
        :param heading: Direction in which the user is moving, in degrees. Must be between 1 and 360 if specified.
        :param proximity_alert_radius: Maximum distance for proximity alerts about approaching another chat member, in meters. Must be between 1 and 100000 if specified.
        :param reply_markup: A JSON-serialized object for a new `inline keyboard <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_.
        :param request_timeout: Request timeout
        :return: On success, if the edited message is not an inline message, the edited Message is
            returned, otherwise True is returned.
        """
        call = EditMessageLiveLocation(
            latitude=latitude,
            longitude=longitude,
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
            horizontal_accuracy=horizontal_accuracy,
            heading=heading,
            proximity_alert_radius=proximity_alert_radius,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def stop_message_live_location(
        self,
        chat_id: Optional[Union[int, str]] = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        request_timeout: Optional[int] = None,
    ) -> Union[Message, bool]:
        """
        Use this method to stop updating a live location message before *live_period* expires. On success, if the message was sent by the bot, the sent :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned.

        Source: https://core.telegram.org/bots/api#stopmessagelivelocation

        :param chat_id: Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param message_id: Required if *inline_message_id* is not specified. Identifier of the message with live location to stop
        :param inline_message_id: Required if *chat_id* and *message_id* are not specified. Identifier of the inline message
        :param reply_markup: A JSON-serialized object for a new `inline keyboard <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_.
        :param request_timeout: Request timeout
        :return: On success, if the message was sent by the bot, the sent Message is returned,
            otherwise True is returned.
        """
        call = StopMessageLiveLocation(
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def send_venue(
        self,
        chat_id: Union[int, str],
        latitude: float,
        longitude: float,
        title: str,
        address: str,
        foursquare_id: Optional[str] = None,
        foursquare_type: Optional[str] = None,
        google_place_id: Optional[str] = None,
        google_place_type: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        Use this method to send information about a venue. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendvenue

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param latitude: Latitude of the venue
        :param longitude: Longitude of the venue
        :param title: Name of the venue
        :param address: Address of the venue
        :param foursquare_id: Foursquare identifier of the venue
        :param foursquare_type: Foursquare type of the venue, if known. (For example, 'arts_entertainment/default', 'arts_entertainment/aquarium' or 'food/icecream'.)
        :param google_place_id: Google Places identifier of the venue
        :param google_place_type: Google Places type of the venue. (See `supported types <https://developers.google.com/places/web-service/supported_types>`_.)
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True`, if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_, `custom reply keyboard <https://core.telegram.org/bots#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.
        :param request_timeout: Request timeout
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
            google_place_id=google_place_id,
            google_place_type=google_place_type,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def send_contact(
        self,
        chat_id: Union[int, str],
        phone_number: str,
        first_name: str,
        last_name: Optional[str] = None,
        vcard: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        Use this method to send phone contacts. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendcontact

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param phone_number: Contact's phone number
        :param first_name: Contact's first name
        :param last_name: Contact's last name
        :param vcard: Additional data about the contact in the form of a `vCard <https://en.wikipedia.org/wiki/VCard>`_, 0-2048 bytes
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True`, if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_, `custom reply keyboard <https://core.telegram.org/bots#keyboards>`_, instructions to remove keyboard or to force a reply from the user.
        :param request_timeout: Request timeout
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
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

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
        explanation_parse_mode: Optional[str] = UNSET,
        explanation_entities: Optional[List[MessageEntity]] = None,
        open_period: Optional[int] = None,
        close_date: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None,
        is_closed: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        Use this method to send a native poll. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendpoll

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param question: Poll question, 1-300 characters
        :param options: A JSON-serialized list of answer options, 2-10 strings 1-100 characters each
        :param is_anonymous: True, if the poll needs to be anonymous, defaults to :code:`True`
        :param type: Poll type, 'quiz' or 'regular', defaults to 'regular'
        :param allows_multiple_answers: True, if the poll allows multiple answers, ignored for polls in quiz mode, defaults to :code:`False`
        :param correct_option_id: 0-based identifier of the correct answer option, required for polls in quiz mode
        :param explanation: Text that is shown when a user chooses an incorrect answer or taps on the lamp icon in a quiz-style poll, 0-200 characters with at most 2 line feeds after entities parsing
        :param explanation_parse_mode: Mode for parsing entities in the explanation. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param explanation_entities: List of special entities that appear in the poll explanation, which can be specified instead of *parse_mode*
        :param open_period: Amount of time in seconds the poll will be active after creation, 5-600. Can't be used together with *close_date*.
        :param close_date: Point in time (Unix timestamp) when the poll will be automatically closed. Must be at least 5 and no more than 600 seconds in the future. Can't be used together with *open_period*.
        :param is_closed: Pass :code:`True`, if the poll needs to be immediately closed. This can be useful for poll preview.
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True`, if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_, `custom reply keyboard <https://core.telegram.org/bots#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.
        :param request_timeout: Request timeout
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
            explanation_entities=explanation_entities,
            open_period=open_period,
            close_date=close_date,
            is_closed=is_closed,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def send_dice(
        self,
        chat_id: Union[int, str],
        emoji: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        Use this method to send an animated emoji that will display a random value. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#senddice

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param emoji: Emoji on which the dice throw animation is based. Currently, must be one of '🎲', '🎯', '🏀', '⚽', '🎳', or '🎰'. Dice can have values 1-6 for '🎲', '🎯' and '🎳', values 1-5 for '🏀' and '⚽', and values 1-64 for '🎰'. Defaults to '🎲'
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True`, if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_, `custom reply keyboard <https://core.telegram.org/bots#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.
        :param request_timeout: Request timeout
        :return: On success, the sent Message is returned.
        """
        call = SendDice(
            chat_id=chat_id,
            emoji=emoji,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def send_chat_action(
        self,
        chat_id: Union[int, str],
        action: str,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method when you need to tell the user that something is happening on the bot's side. The status is set for 5 seconds or less (when a message arrives from your bot, Telegram clients clear its typing status). Returns :code:`True` on success.

         Example: The `ImageBot <https://t.me/imagebot>`_ needs some time to process a request and upload the image. Instead of sending a text message along the lines of 'Retrieving image, please wait…', the bot may use :class:`aiogram.methods.send_chat_action.SendChatAction` with *action* = *upload_photo*. The user will see a 'sending photo' status for the bot.

        We only recommend using this method when a response from the bot will take a **noticeable** amount of time to arrive.

        Source: https://core.telegram.org/bots/api#sendchataction

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param action: Type of action to broadcast. Choose one, depending on what the user is about to receive: *typing* for `text messages <https://core.telegram.org/bots/api#sendmessage>`_, *upload_photo* for `photos <https://core.telegram.org/bots/api#sendphoto>`_, *record_video* or *upload_video* for `videos <https://core.telegram.org/bots/api#sendvideo>`_, *record_voice* or *upload_voice* for `voice notes <https://core.telegram.org/bots/api#sendvoice>`_, *upload_document* for `general files <https://core.telegram.org/bots/api#senddocument>`_, *find_location* for `location data <https://core.telegram.org/bots/api#sendlocation>`_, *record_video_note* or *upload_video_note* for `video notes <https://core.telegram.org/bots/api#sendvideonote>`_.
        :param request_timeout: Request timeout
        :return: Returns True on success.
        """
        call = SendChatAction(
            chat_id=chat_id,
            action=action,
        )
        return await self(call, request_timeout=request_timeout)

    async def get_user_profile_photos(
        self,
        user_id: int,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        request_timeout: Optional[int] = None,
    ) -> UserProfilePhotos:
        """
        Use this method to get a list of profile pictures for a user. Returns a :class:`aiogram.types.user_profile_photos.UserProfilePhotos` object.

        Source: https://core.telegram.org/bots/api#getuserprofilephotos

        :param user_id: Unique identifier of the target user
        :param offset: Sequential number of the first photo to be returned. By default, all photos are returned.
        :param limit: Limits the number of photos to be retrieved. Values between 1-100 are accepted. Defaults to 100.
        :param request_timeout: Request timeout
        :return: Returns a UserProfilePhotos object.
        """
        call = GetUserProfilePhotos(
            user_id=user_id,
            offset=offset,
            limit=limit,
        )
        return await self(call, request_timeout=request_timeout)

    async def get_file(
        self,
        file_id: str,
        request_timeout: Optional[int] = None,
    ) -> File:
        """
        Use this method to get basic info about a file and prepare it for downloading. For the moment, bots can download files of up to 20MB in size. On success, a :class:`aiogram.types.file.File` object is returned. The file can then be downloaded via the link :code:`https://api.telegram.org/file/bot<token>/<file_path>`, where :code:`<file_path>` is taken from the response. It is guaranteed that the link will be valid for at least 1 hour. When the link expires, a new one can be requested by calling :class:`aiogram.methods.get_file.GetFile` again.
        **Note:** This function may not preserve the original file name and MIME type. You should save the file's MIME type and name (if available) when the File object is received.

        Source: https://core.telegram.org/bots/api#getfile

        :param file_id: File identifier to get info about
        :param request_timeout: Request timeout
        :return: On success, a File object is returned.
        """
        call = GetFile(
            file_id=file_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def ban_chat_member(
        self,
        chat_id: Union[int, str],
        user_id: int,
        until_date: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None,
        revoke_messages: Optional[bool] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to ban a user in a group, a supergroup or a channel. In the case of supergroups and channels, the user will not be able to return to the chat on their own using invite links, etc., unless `unbanned <https://core.telegram.org/bots/api#unbanchatmember>`_ first. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#banchatmember

        :param chat_id: Unique identifier for the target group or username of the target supergroup or channel (in the format :code:`@channelusername`)
        :param user_id: Unique identifier of the target user
        :param until_date: Date when the user will be unbanned, unix time. If user is banned for more than 366 days or less than 30 seconds from the current time they are considered to be banned forever. Applied for supergroups and channels only.
        :param revoke_messages: Pass :code:`True` to delete all messages from the chat for the user that is being removed. If :code:`False`, the user will be able to see messages in the group that were sent before the user was removed. Always :code:`True` for supergroups and channels.
        :param request_timeout: Request timeout
        :return: In the case of supergroups and channels, the user will not be able to return to
            the chat on their own using invite links, etc. Returns True on success.
        """
        call = BanChatMember(
            chat_id=chat_id,
            user_id=user_id,
            until_date=until_date,
            revoke_messages=revoke_messages,
        )
        return await self(call, request_timeout=request_timeout)

    async def kick_chat_member(
        self,
        chat_id: Union[int, str],
        user_id: int,
        until_date: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None,
        revoke_messages: Optional[bool] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        .. warning:

            Renamed from :code:`kickChatMember` in 5.3 bot API version and can be removed in near future

        Use this method to ban a user in a group, a supergroup or a channel. In the case of supergroups and channels, the user will not be able to return to the chat on their own using invite links, etc., unless `unbanned <https://core.telegram.org/bots/api#unbanchatmember>`_ first. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#banchatmember

        :param chat_id: Unique identifier for the target group or username of the target supergroup or channel (in the format :code:`@channelusername`)
        :param user_id: Unique identifier of the target user
        :param until_date: Date when the user will be unbanned, unix time. If user is banned for more than 366 days or less than 30 seconds from the current time they are considered to be banned forever. Applied for supergroups and channels only.
        :param revoke_messages: Pass :code:`True` to delete all messages from the chat for the user that is being removed. If :code:`False`, the user will be able to see messages in the group that were sent before the user was removed. Always :code:`True` for supergroups and channels.
        :param request_timeout: Request timeout
        :return: In the case of supergroups and channels, the user will not be able to return to
            the chat on their own using invite links, etc. Returns True on success.
        """
        call = KickChatMember(
            chat_id=chat_id,
            user_id=user_id,
            until_date=until_date,
            revoke_messages=revoke_messages,
        )
        return await self(call, request_timeout=request_timeout)

    async def unban_chat_member(
        self,
        chat_id: Union[int, str],
        user_id: int,
        only_if_banned: Optional[bool] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to unban a previously banned user in a supergroup or channel. The user will **not** return to the group or channel automatically, but will be able to join via link, etc. The bot must be an administrator for this to work. By default, this method guarantees that after the call the user is not a member of the chat, but will be able to join it. So if the user is a member of the chat they will also be **removed** from the chat. If you don't want this, use the parameter *only_if_banned*. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#unbanchatmember

        :param chat_id: Unique identifier for the target group or username of the target supergroup or channel (in the format :code:`@username`)
        :param user_id: Unique identifier of the target user
        :param only_if_banned: Do nothing if the user is not banned
        :param request_timeout: Request timeout
        :return: The user will not return to the group or channel automatically, but will be able
            to join via link, etc. Returns True on success.
        """
        call = UnbanChatMember(
            chat_id=chat_id,
            user_id=user_id,
            only_if_banned=only_if_banned,
        )
        return await self(call, request_timeout=request_timeout)

    async def restrict_chat_member(
        self,
        chat_id: Union[int, str],
        user_id: int,
        permissions: ChatPermissions,
        until_date: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to restrict a user in a supergroup. The bot must be an administrator in the supergroup for this to work and must have the appropriate admin rights. Pass :code:`True` for all permissions to lift restrictions from a user. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#restrictchatmember

        :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)
        :param user_id: Unique identifier of the target user
        :param permissions: A JSON-serialized object for new user permissions
        :param until_date: Date when restrictions will be lifted for the user, unix time. If user is restricted for more than 366 days or less than 30 seconds from the current time, they are considered to be restricted forever
        :param request_timeout: Request timeout
        :return: Returns True on success.
        """
        call = RestrictChatMember(
            chat_id=chat_id,
            user_id=user_id,
            permissions=permissions,
            until_date=until_date,
        )
        return await self(call, request_timeout=request_timeout)

    async def promote_chat_member(
        self,
        chat_id: Union[int, str],
        user_id: int,
        is_anonymous: Optional[bool] = None,
        can_manage_chat: Optional[bool] = None,
        can_post_messages: Optional[bool] = None,
        can_edit_messages: Optional[bool] = None,
        can_delete_messages: Optional[bool] = None,
        can_manage_voice_chats: Optional[bool] = None,
        can_restrict_members: Optional[bool] = None,
        can_promote_members: Optional[bool] = None,
        can_change_info: Optional[bool] = None,
        can_invite_users: Optional[bool] = None,
        can_pin_messages: Optional[bool] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to promote or demote a user in a supergroup or a channel. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Pass :code:`False` for all boolean parameters to demote a user. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#promotechatmember

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param user_id: Unique identifier of the target user
        :param is_anonymous: Pass :code:`True`, if the administrator's presence in the chat is hidden
        :param can_manage_chat: Pass True, if the administrator can access the chat event log, chat statistics, message statistics in channels, see channel members, see anonymous administrators in supergroups and ignore slow mode. Implied by any other administrator privilege
        :param can_post_messages: Pass True, if the administrator can create channel posts, channels only
        :param can_edit_messages: Pass True, if the administrator can edit messages of other users and can pin messages, channels only
        :param can_delete_messages: Pass True, if the administrator can delete messages of other users
        :param can_manage_voice_chats: Pass True, if the administrator can manage voice chats
        :param can_restrict_members: Pass True, if the administrator can restrict, ban or unban chat members
        :param can_promote_members: Pass True, if the administrator can add new administrators with a subset of their own privileges or demote administrators that he has promoted, directly or indirectly (promoted by administrators that were appointed by him)
        :param can_change_info: Pass True, if the administrator can change chat title, photo and other settings
        :param can_invite_users: Pass True, if the administrator can invite new users to the chat
        :param can_pin_messages: Pass True, if the administrator can pin messages, supergroups only
        :param request_timeout: Request timeout
        :return: Returns True on success.
        """
        call = PromoteChatMember(
            chat_id=chat_id,
            user_id=user_id,
            is_anonymous=is_anonymous,
            can_manage_chat=can_manage_chat,
            can_post_messages=can_post_messages,
            can_edit_messages=can_edit_messages,
            can_delete_messages=can_delete_messages,
            can_manage_voice_chats=can_manage_voice_chats,
            can_restrict_members=can_restrict_members,
            can_promote_members=can_promote_members,
            can_change_info=can_change_info,
            can_invite_users=can_invite_users,
            can_pin_messages=can_pin_messages,
        )
        return await self(call, request_timeout=request_timeout)

    async def set_chat_administrator_custom_title(
        self,
        chat_id: Union[int, str],
        user_id: int,
        custom_title: str,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to set a custom title for an administrator in a supergroup promoted by the bot. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#setchatadministratorcustomtitle

        :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)
        :param user_id: Unique identifier of the target user
        :param custom_title: New custom title for the administrator; 0-16 characters, emoji are not allowed
        :param request_timeout: Request timeout
        :return: Returns True on success.
        """
        call = SetChatAdministratorCustomTitle(
            chat_id=chat_id,
            user_id=user_id,
            custom_title=custom_title,
        )
        return await self(call, request_timeout=request_timeout)

    async def set_chat_permissions(
        self,
        chat_id: Union[int, str],
        permissions: ChatPermissions,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to set default chat permissions for all members. The bot must be an administrator in the group or a supergroup for this to work and must have the *can_restrict_members* admin rights. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#setchatpermissions

        :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)
        :param permissions: New default chat permissions
        :param request_timeout: Request timeout
        :return: Returns True on success.
        """
        call = SetChatPermissions(
            chat_id=chat_id,
            permissions=permissions,
        )
        return await self(call, request_timeout=request_timeout)

    async def export_chat_invite_link(
        self,
        chat_id: Union[int, str],
        request_timeout: Optional[int] = None,
    ) -> str:
        """
        Use this method to generate a new primary invite link for a chat; any previously generated primary link is revoked. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns the new invite link as *String* on success.

         Note: Each administrator in a chat generates their own invite links. Bots can't use invite links generated by other administrators. If you want your bot to work with invite links, it will need to generate its own link using :class:`aiogram.methods.export_chat_invite_link.ExportChatInviteLink` or by calling the :class:`aiogram.methods.get_chat.GetChat` method. If your bot needs to generate a new primary invite link replacing its previous one, use :class:`aiogram.methods.export_chat_invite_link.ExportChatInviteLink` again.

        Source: https://core.telegram.org/bots/api#exportchatinvitelink

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param request_timeout: Request timeout
        :return: Returns the new invite link as String on success.
        """
        call = ExportChatInviteLink(
            chat_id=chat_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def create_chat_invite_link(
        self,
        chat_id: Union[int, str],
        expire_date: Optional[int] = None,
        member_limit: Optional[int] = None,
        request_timeout: Optional[int] = None,
    ) -> ChatInviteLink:
        """
        Use this method to create an additional invite link for a chat. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. The link can be revoked using the method :class:`aiogram.methods.revoke_chat_invite_link.RevokeChatInviteLink`. Returns the new invite link as :class:`aiogram.types.chat_invite_link.ChatInviteLink` object.

        Source: https://core.telegram.org/bots/api#createchatinvitelink

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param expire_date: Point in time (Unix timestamp) when the link will expire
        :param member_limit: Maximum number of users that can be members of the chat simultaneously after joining the chat via this invite link; 1-99999
        :param request_timeout: Request timeout
        :return: Returns the new invite link as ChatInviteLink object.
        """
        call = CreateChatInviteLink(
            chat_id=chat_id,
            expire_date=expire_date,
            member_limit=member_limit,
        )
        return await self(call, request_timeout=request_timeout)

    async def edit_chat_invite_link(
        self,
        chat_id: Union[int, str],
        invite_link: str,
        expire_date: Optional[int] = None,
        member_limit: Optional[int] = None,
        request_timeout: Optional[int] = None,
    ) -> ChatInviteLink:
        """
        Use this method to edit a non-primary invite link created by the bot. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns the edited invite link as a :class:`aiogram.types.chat_invite_link.ChatInviteLink` object.

        Source: https://core.telegram.org/bots/api#editchatinvitelink

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param invite_link: The invite link to edit
        :param expire_date: Point in time (Unix timestamp) when the link will expire
        :param member_limit: Maximum number of users that can be members of the chat simultaneously after joining the chat via this invite link; 1-99999
        :param request_timeout: Request timeout
        :return: Returns the edited invite link as a ChatInviteLink object.
        """
        call = EditChatInviteLink(
            chat_id=chat_id,
            invite_link=invite_link,
            expire_date=expire_date,
            member_limit=member_limit,
        )
        return await self(call, request_timeout=request_timeout)

    async def revoke_chat_invite_link(
        self,
        chat_id: Union[int, str],
        invite_link: str,
        request_timeout: Optional[int] = None,
    ) -> ChatInviteLink:
        """
        Use this method to revoke an invite link created by the bot. If the primary link is revoked, a new link is automatically generated. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns the revoked invite link as :class:`aiogram.types.chat_invite_link.ChatInviteLink` object.

        Source: https://core.telegram.org/bots/api#revokechatinvitelink

        :param chat_id: Unique identifier of the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param invite_link: The invite link to revoke
        :param request_timeout: Request timeout
        :return: Returns the revoked invite link as ChatInviteLink object.
        """
        call = RevokeChatInviteLink(
            chat_id=chat_id,
            invite_link=invite_link,
        )
        return await self(call, request_timeout=request_timeout)

    async def set_chat_photo(
        self,
        chat_id: Union[int, str],
        photo: InputFile,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to set a new profile photo for the chat. Photos can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#setchatphoto

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param photo: New chat photo, uploaded using multipart/form-data
        :param request_timeout: Request timeout
        :return: Returns True on success.
        """
        call = SetChatPhoto(
            chat_id=chat_id,
            photo=photo,
        )
        return await self(call, request_timeout=request_timeout)

    async def delete_chat_photo(
        self,
        chat_id: Union[int, str],
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to delete a chat photo. Photos can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#deletechatphoto

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param request_timeout: Request timeout
        :return: Returns True on success.
        """
        call = DeleteChatPhoto(
            chat_id=chat_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def set_chat_title(
        self,
        chat_id: Union[int, str],
        title: str,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to change the title of a chat. Titles can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#setchattitle

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param title: New chat title, 1-255 characters
        :param request_timeout: Request timeout
        :return: Returns True on success.
        """
        call = SetChatTitle(
            chat_id=chat_id,
            title=title,
        )
        return await self(call, request_timeout=request_timeout)

    async def set_chat_description(
        self,
        chat_id: Union[int, str],
        description: Optional[str] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to change the description of a group, a supergroup or a channel. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#setchatdescription

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param description: New chat description, 0-255 characters
        :param request_timeout: Request timeout
        :return: Returns True on success.
        """
        call = SetChatDescription(
            chat_id=chat_id,
            description=description,
        )
        return await self(call, request_timeout=request_timeout)

    async def pin_chat_message(
        self,
        chat_id: Union[int, str],
        message_id: int,
        disable_notification: Optional[bool] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to add a message to the list of pinned messages in a chat. If the chat is not a private chat, the bot must be an administrator in the chat for this to work and must have the 'can_pin_messages' admin right in a supergroup or 'can_edit_messages' admin right in a channel. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#pinchatmessage

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param message_id: Identifier of a message to pin
        :param disable_notification: Pass :code:`True`, if it is not necessary to send a notification to all chat members about the new pinned message. Notifications are always disabled in channels and private chats.
        :param request_timeout: Request timeout
        :return: Returns True on success.
        """
        call = PinChatMessage(
            chat_id=chat_id,
            message_id=message_id,
            disable_notification=disable_notification,
        )
        return await self(call, request_timeout=request_timeout)

    async def unpin_chat_message(
        self,
        chat_id: Union[int, str],
        message_id: Optional[int] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to remove a message from the list of pinned messages in a chat. If the chat is not a private chat, the bot must be an administrator in the chat for this to work and must have the 'can_pin_messages' admin right in a supergroup or 'can_edit_messages' admin right in a channel. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#unpinchatmessage

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param message_id: Identifier of a message to unpin. If not specified, the most recent pinned message (by sending date) will be unpinned.
        :param request_timeout: Request timeout
        :return: Returns True on success.
        """
        call = UnpinChatMessage(
            chat_id=chat_id,
            message_id=message_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def unpin_all_chat_messages(
        self,
        chat_id: Union[int, str],
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to clear the list of pinned messages in a chat. If the chat is not a private chat, the bot must be an administrator in the chat for this to work and must have the 'can_pin_messages' admin right in a supergroup or 'can_edit_messages' admin right in a channel. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#unpinallchatmessages

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param request_timeout: Request timeout
        :return: Returns True on success.
        """
        call = UnpinAllChatMessages(
            chat_id=chat_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def leave_chat(
        self,
        chat_id: Union[int, str],
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method for your bot to leave a group, supergroup or channel. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#leavechat

        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel (in the format :code:`@channelusername`)
        :param request_timeout: Request timeout
        :return: Returns True on success.
        """
        call = LeaveChat(
            chat_id=chat_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def get_chat(
        self,
        chat_id: Union[int, str],
        request_timeout: Optional[int] = None,
    ) -> Chat:
        """
        Use this method to get up to date information about the chat (current name of the user for one-on-one conversations, current username of a user, group or channel, etc.). Returns a :class:`aiogram.types.chat.Chat` object on success.

        Source: https://core.telegram.org/bots/api#getchat

        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel (in the format :code:`@channelusername`)
        :param request_timeout: Request timeout
        :return: Returns a Chat object on success.
        """
        call = GetChat(
            chat_id=chat_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def get_chat_administrators(
        self,
        chat_id: Union[int, str],
        request_timeout: Optional[int] = None,
    ) -> List[
        Union[
            ChatMemberOwner,
            ChatMemberAdministrator,
            ChatMemberMember,
            ChatMemberRestricted,
            ChatMemberLeft,
            ChatMemberBanned,
        ]
    ]:
        """
        Use this method to get a list of administrators in a chat. On success, returns an Array of :class:`aiogram.types.chat_member.ChatMember` objects that contains information about all chat administrators except other bots. If the chat is a group or a supergroup and no administrators were appointed, only the creator will be returned.

        Source: https://core.telegram.org/bots/api#getchatadministrators

        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel (in the format :code:`@channelusername`)
        :param request_timeout: Request timeout
        :return: On success, returns an Array of ChatMember objects that contains information
            about all chat administrators except other bots. If the chat is a group or a
            supergroup and no administrators were appointed, only the creator will be
            returned.
        """
        call = GetChatAdministrators(
            chat_id=chat_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def get_chat_member_count(
        self,
        chat_id: Union[int, str],
        request_timeout: Optional[int] = None,
    ) -> int:
        """
        Use this method to get the number of members in a chat. Returns *Int* on success.

        Source: https://core.telegram.org/bots/api#getchatmembercount

        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel (in the format :code:`@channelusername`)
        :param request_timeout: Request timeout
        :return: Returns Int on success.
        """
        call = GetChatMemberCount(
            chat_id=chat_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def get_chat_members_count(
        self,
        chat_id: Union[int, str],
        request_timeout: Optional[int] = None,
    ) -> int:
        """
        .. warning:

            Renamed from :code:`getChatMembersCount` in 5.3 bot API version and can be removed in near future

        Use this method to get the number of members in a chat. Returns *Int* on success.

        Source: https://core.telegram.org/bots/api#getchatmembercount

        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel (in the format :code:`@channelusername`)
        :param request_timeout: Request timeout
        :return: Returns Int on success.
        """
        call = GetChatMembersCount(
            chat_id=chat_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def get_chat_member(
        self,
        chat_id: Union[int, str],
        user_id: int,
        request_timeout: Optional[int] = None,
    ) -> Union[
        ChatMemberOwner,
        ChatMemberAdministrator,
        ChatMemberMember,
        ChatMemberRestricted,
        ChatMemberLeft,
        ChatMemberBanned,
    ]:
        """
        Use this method to get information about a member of a chat. Returns a :class:`aiogram.types.chat_member.ChatMember` object on success.

        Source: https://core.telegram.org/bots/api#getchatmember

        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel (in the format :code:`@channelusername`)
        :param user_id: Unique identifier of the target user
        :param request_timeout: Request timeout
        :return: Returns a ChatMember object on success.
        """
        call = GetChatMember(
            chat_id=chat_id,
            user_id=user_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def set_chat_sticker_set(
        self,
        chat_id: Union[int, str],
        sticker_set_name: str,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to set a new group sticker set for a supergroup. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Use the field *can_set_sticker_set* optionally returned in :class:`aiogram.methods.get_chat.GetChat` requests to check if the bot can use this method. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#setchatstickerset

        :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)
        :param sticker_set_name: Name of the sticker set to be set as the group sticker set
        :param request_timeout: Request timeout
        :return: Use the field can_set_sticker_set optionally returned in getChat requests to
            check if the bot can use this method. Returns True on success.
        """
        call = SetChatStickerSet(
            chat_id=chat_id,
            sticker_set_name=sticker_set_name,
        )
        return await self(call, request_timeout=request_timeout)

    async def delete_chat_sticker_set(
        self,
        chat_id: Union[int, str],
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to delete a group sticker set from a supergroup. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Use the field *can_set_sticker_set* optionally returned in :class:`aiogram.methods.get_chat.GetChat` requests to check if the bot can use this method. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#deletechatstickerset

        :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)
        :param request_timeout: Request timeout
        :return: Use the field can_set_sticker_set optionally returned in getChat requests to
            check if the bot can use this method. Returns True on success.
        """
        call = DeleteChatStickerSet(
            chat_id=chat_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: Optional[str] = None,
        show_alert: Optional[bool] = None,
        url: Optional[str] = None,
        cache_time: Optional[int] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to send answers to callback queries sent from `inline keyboards <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_. The answer will be displayed to the user as a notification at the top of the chat screen or as an alert. On success, :code:`True` is returned.

         Alternatively, the user can be redirected to the specified Game URL. For this option to work, you must first create a game for your bot via `@Botfather <https://t.me/botfather>`_ and accept the terms. Otherwise, you may use links like :code:`t.me/your_bot?start=XXXX` that open your bot with a parameter.

        Source: https://core.telegram.org/bots/api#answercallbackquery

        :param callback_query_id: Unique identifier for the query to be answered
        :param text: Text of the notification. If not specified, nothing will be shown to the user, 0-200 characters
        :param show_alert: If *true*, an alert will be shown by the client instead of a notification at the top of the chat screen. Defaults to *false*.
        :param url: URL that will be opened by the user's client. If you have created a :class:`aiogram.types.game.Game` and accepted the conditions via `@Botfather <https://t.me/botfather>`_, specify the URL that opens your game — note that this will only work if the query comes from a `https://core.telegram.org/bots/api#inlinekeyboardbutton <https://core.telegram.org/bots/api#inlinekeyboardbutton>`_ *callback_game* button.
        :param cache_time: The maximum amount of time in seconds that the result of the callback query may be cached client-side. Telegram apps will support caching starting in version 3.14. Defaults to 0.
        :param request_timeout: Request timeout
        :return: On success, True is returned.
        """
        call = AnswerCallbackQuery(
            callback_query_id=callback_query_id,
            text=text,
            show_alert=show_alert,
            url=url,
            cache_time=cache_time,
        )
        return await self(call, request_timeout=request_timeout)

    async def set_my_commands(
        self,
        commands: List[BotCommand],
        scope: Optional[BotCommandScope] = None,
        language_code: Optional[str] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to change the list of the bot's commands. See `https://core.telegram.org/bots#commands <https://core.telegram.org/bots#commands>`_`https://core.telegram.org/bots#commands <https://core.telegram.org/bots#commands>`_ for more details about bot commands. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#setmycommands

        :param commands: A JSON-serialized list of bot commands to be set as the list of the bot's commands. At most 100 commands can be specified.
        :param scope: A JSON-serialized object, describing scope of users for which the commands are relevant. Defaults to :class:`aiogram.types.bot_command_scope_default.BotCommandScopeDefault`.
        :param language_code: A two-letter ISO 639-1 language code. If empty, commands will be applied to all users from the given scope, for whose language there are no dedicated commands
        :param request_timeout: Request timeout
        :return: Returns True on success.
        """
        call = SetMyCommands(
            commands=commands,
            scope=scope,
            language_code=language_code,
        )
        return await self(call, request_timeout=request_timeout)

    async def delete_my_commands(
        self,
        scope: Optional[BotCommandScope] = None,
        language_code: Optional[str] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to delete the list of the bot's commands for the given scope and user language. After deletion, `higher level commands <https://core.telegram.org/bots/api#determining-list-of-commands>`_ will be shown to affected users. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#deletemycommands

        :param scope: A JSON-serialized object, describing scope of users for which the commands are relevant. Defaults to :class:`aiogram.types.bot_command_scope_default.BotCommandScopeDefault`.
        :param language_code: A two-letter ISO 639-1 language code. If empty, commands will be applied to all users from the given scope, for whose language there are no dedicated commands
        :param request_timeout: Request timeout
        :return: Returns True on success.
        """
        call = DeleteMyCommands(
            scope=scope,
            language_code=language_code,
        )
        return await self(call, request_timeout=request_timeout)

    async def get_my_commands(
        self,
        scope: Optional[BotCommandScope] = None,
        language_code: Optional[str] = None,
        request_timeout: Optional[int] = None,
    ) -> List[BotCommand]:
        """
        Use this method to get the current list of the bot's commands for the given scope and user language. Returns Array of :class:`aiogram.types.bot_command.BotCommand` on success. If commands aren't set, an empty list is returned.

        Source: https://core.telegram.org/bots/api#getmycommands

        :param scope: A JSON-serialized object, describing scope of users. Defaults to :class:`aiogram.types.bot_command_scope_default.BotCommandScopeDefault`.
        :param language_code: A two-letter ISO 639-1 language code or an empty string
        :param request_timeout: Request timeout
        :return: Returns Array of BotCommand on success. If commands aren't set, an empty list is
            returned.
        """
        call = GetMyCommands(
            scope=scope,
            language_code=language_code,
        )
        return await self(call, request_timeout=request_timeout)

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
        parse_mode: Optional[str] = UNSET,
        entities: Optional[List[MessageEntity]] = None,
        disable_web_page_preview: Optional[bool] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        request_timeout: Optional[int] = None,
    ) -> Union[Message, bool]:
        """
        Use this method to edit text and `game <https://core.telegram.org/bots/api#games>`_ messages. On success, if the edited message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned.

        Source: https://core.telegram.org/bots/api#editmessagetext

        :param text: New text of the message, 1-4096 characters after entities parsing
        :param chat_id: Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param message_id: Required if *inline_message_id* is not specified. Identifier of the message to edit
        :param inline_message_id: Required if *chat_id* and *message_id* are not specified. Identifier of the inline message
        :param parse_mode: Mode for parsing entities in the message text. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param entities: List of special entities that appear in message text, which can be specified instead of *parse_mode*
        :param disable_web_page_preview: Disables link previews for links in this message
        :param reply_markup: A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_.
        :param request_timeout: Request timeout
        :return: On success, if the edited message is not an inline message, the edited Message is
            returned, otherwise True is returned.
        """
        call = EditMessageText(
            text=text,
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
            parse_mode=parse_mode,
            entities=entities,
            disable_web_page_preview=disable_web_page_preview,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def edit_message_caption(
        self,
        chat_id: Optional[Union[int, str]] = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET,
        caption_entities: Optional[List[MessageEntity]] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        request_timeout: Optional[int] = None,
    ) -> Union[Message, bool]:
        """
        Use this method to edit captions of messages. On success, if the edited message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned.

        Source: https://core.telegram.org/bots/api#editmessagecaption

        :param chat_id: Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param message_id: Required if *inline_message_id* is not specified. Identifier of the message to edit
        :param inline_message_id: Required if *chat_id* and *message_id* are not specified. Identifier of the inline message
        :param caption: New caption of the message, 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the message caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: List of special entities that appear in the caption, which can be specified instead of *parse_mode*
        :param reply_markup: A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_.
        :param request_timeout: Request timeout
        :return: On success, if the edited message is not an inline message, the edited Message is
            returned, otherwise True is returned.
        """
        call = EditMessageCaption(
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def edit_message_media(
        self,
        media: InputMedia,
        chat_id: Optional[Union[int, str]] = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        request_timeout: Optional[int] = None,
    ) -> Union[Message, bool]:
        """
        Use this method to edit animation, audio, document, photo, or video messages. If a message is part of a message album, then it can be edited only to an audio for audio albums, only to a document for document albums and to a photo or a video otherwise. When an inline message is edited, a new file can't be uploaded. Use a previously uploaded file via its file_id or specify a URL. On success, if the edited message was sent by the bot, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned.

        Source: https://core.telegram.org/bots/api#editmessagemedia

        :param media: A JSON-serialized object for a new media content of the message
        :param chat_id: Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param message_id: Required if *inline_message_id* is not specified. Identifier of the message to edit
        :param inline_message_id: Required if *chat_id* and *message_id* are not specified. Identifier of the inline message
        :param reply_markup: A JSON-serialized object for a new `inline keyboard <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_.
        :param request_timeout: Request timeout
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
        return await self(call, request_timeout=request_timeout)

    async def edit_message_reply_markup(
        self,
        chat_id: Optional[Union[int, str]] = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        request_timeout: Optional[int] = None,
    ) -> Union[Message, bool]:
        """
        Use this method to edit only the reply markup of messages. On success, if the edited message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned.

        Source: https://core.telegram.org/bots/api#editmessagereplymarkup

        :param chat_id: Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param message_id: Required if *inline_message_id* is not specified. Identifier of the message to edit
        :param inline_message_id: Required if *chat_id* and *message_id* are not specified. Identifier of the inline message
        :param reply_markup: A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_.
        :param request_timeout: Request timeout
        :return: On success, if the edited message is not an inline message, the edited Message is
            returned, otherwise True is returned.
        """
        call = EditMessageReplyMarkup(
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def stop_poll(
        self,
        chat_id: Union[int, str],
        message_id: int,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        request_timeout: Optional[int] = None,
    ) -> Poll:
        """
        Use this method to stop a poll which was sent by the bot. On success, the stopped :class:`aiogram.types.poll.Poll` with the final results is returned.

        Source: https://core.telegram.org/bots/api#stoppoll

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param message_id: Identifier of the original message with the poll
        :param reply_markup: A JSON-serialized object for a new message `inline keyboard <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_.
        :param request_timeout: Request timeout
        :return: On success, the stopped Poll with the final results is returned.
        """
        call = StopPoll(
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def delete_message(
        self,
        chat_id: Union[int, str],
        message_id: int,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to delete a message, including service messages, with the following limitations:

        - A message can only be deleted if it was sent less than 48 hours ago.

        - A dice message in a private chat can only be deleted if it was sent more than 24 hours ago.

        - Bots can delete outgoing messages in private chats, groups, and supergroups.

        - Bots can delete incoming messages in private chats.

        - Bots granted *can_post_messages* permissions can delete outgoing messages in channels.

        - If the bot is an administrator of a group, it can delete any message there.

        - If the bot has *can_delete_messages* permission in a supergroup or a channel, it can delete any message there.

        Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#deletemessage

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param message_id: Identifier of the message to delete
        :param request_timeout: Request timeout
        :return: Returns True on success.
        """
        call = DeleteMessage(
            chat_id=chat_id,
            message_id=message_id,
        )
        return await self(call, request_timeout=request_timeout)

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
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        Use this method to send static .WEBP or `animated <https://telegram.org/blog/animated-stickers>`_ .TGS stickers. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendsticker

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param sticker: Sticker to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a .WEBP file from the Internet, or upload a new one using multipart/form-data. :ref:`More info on Sending Files » <sending-files>`
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True`, if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_, `custom reply keyboard <https://core.telegram.org/bots#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.
        :param request_timeout: Request timeout
        :return: On success, the sent Message is returned.
        """
        call = SendSticker(
            chat_id=chat_id,
            sticker=sticker,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def get_sticker_set(
        self,
        name: str,
        request_timeout: Optional[int] = None,
    ) -> StickerSet:
        """
        Use this method to get a sticker set. On success, a :class:`aiogram.types.sticker_set.StickerSet` object is returned.

        Source: https://core.telegram.org/bots/api#getstickerset

        :param name: Name of the sticker set
        :param request_timeout: Request timeout
        :return: On success, a StickerSet object is returned.
        """
        call = GetStickerSet(
            name=name,
        )
        return await self(call, request_timeout=request_timeout)

    async def upload_sticker_file(
        self,
        user_id: int,
        png_sticker: InputFile,
        request_timeout: Optional[int] = None,
    ) -> File:
        """
        Use this method to upload a .PNG file with a sticker for later use in *createNewStickerSet* and *addStickerToSet* methods (can be used multiple times). Returns the uploaded :class:`aiogram.types.file.File` on success.

        Source: https://core.telegram.org/bots/api#uploadstickerfile

        :param user_id: User identifier of sticker file owner
        :param png_sticker: **PNG** image with the sticker, must be up to 512 kilobytes in size, dimensions must not exceed 512px, and either width or height must be exactly 512px. :ref:`More info on Sending Files » <sending-files>`
        :param request_timeout: Request timeout
        :return: Returns the uploaded File on success.
        """
        call = UploadStickerFile(
            user_id=user_id,
            png_sticker=png_sticker,
        )
        return await self(call, request_timeout=request_timeout)

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
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to create a new sticker set owned by a user. The bot will be able to edit the sticker set thus created. You **must** use exactly one of the fields *png_sticker* or *tgs_sticker*. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#createnewstickerset

        :param user_id: User identifier of created sticker set owner
        :param name: Short name of sticker set, to be used in :code:`t.me/addstickers/` URLs (e.g., *animals*). Can contain only english letters, digits and underscores. Must begin with a letter, can't contain consecutive underscores and must end in *'_by_<bot username>'*. *<bot_username>* is case insensitive. 1-64 characters.
        :param title: Sticker set title, 1-64 characters
        :param emojis: One or more emoji corresponding to the sticker
        :param png_sticker: **PNG** image with the sticker, must be up to 512 kilobytes in size, dimensions must not exceed 512px, and either width or height must be exactly 512px. Pass a *file_id* as a String to send a file that already exists on the Telegram servers, pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. :ref:`More info on Sending Files » <sending-files>`
        :param tgs_sticker: **TGS** animation with the sticker, uploaded using multipart/form-data. See `https://core.telegram.org/animated_stickers#technical-requirements <https://core.telegram.org/animated_stickers#technical-requirements>`_`https://core.telegram.org/animated_stickers#technical-requirements <https://core.telegram.org/animated_stickers#technical-requirements>`_ for technical requirements
        :param contains_masks: Pass :code:`True`, if a set of mask stickers should be created
        :param mask_position: A JSON-serialized object for position where the mask should be placed on faces
        :param request_timeout: Request timeout
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
        return await self(call, request_timeout=request_timeout)

    async def add_sticker_to_set(
        self,
        user_id: int,
        name: str,
        emojis: str,
        png_sticker: Optional[Union[InputFile, str]] = None,
        tgs_sticker: Optional[InputFile] = None,
        mask_position: Optional[MaskPosition] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to add a new sticker to a set created by the bot. You **must** use exactly one of the fields *png_sticker* or *tgs_sticker*. Animated stickers can be added to animated sticker sets and only to them. Animated sticker sets can have up to 50 stickers. Static sticker sets can have up to 120 stickers. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#addstickertoset

        :param user_id: User identifier of sticker set owner
        :param name: Sticker set name
        :param emojis: One or more emoji corresponding to the sticker
        :param png_sticker: **PNG** image with the sticker, must be up to 512 kilobytes in size, dimensions must not exceed 512px, and either width or height must be exactly 512px. Pass a *file_id* as a String to send a file that already exists on the Telegram servers, pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. :ref:`More info on Sending Files » <sending-files>`
        :param tgs_sticker: **TGS** animation with the sticker, uploaded using multipart/form-data. See `https://core.telegram.org/animated_stickers#technical-requirements <https://core.telegram.org/animated_stickers#technical-requirements>`_`https://core.telegram.org/animated_stickers#technical-requirements <https://core.telegram.org/animated_stickers#technical-requirements>`_ for technical requirements
        :param mask_position: A JSON-serialized object for position where the mask should be placed on faces
        :param request_timeout: Request timeout
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
        return await self(call, request_timeout=request_timeout)

    async def set_sticker_position_in_set(
        self,
        sticker: str,
        position: int,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to move a sticker in a set created by the bot to a specific position. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#setstickerpositioninset

        :param sticker: File identifier of the sticker
        :param position: New sticker position in the set, zero-based
        :param request_timeout: Request timeout
        :return: Returns True on success.
        """
        call = SetStickerPositionInSet(
            sticker=sticker,
            position=position,
        )
        return await self(call, request_timeout=request_timeout)

    async def delete_sticker_from_set(
        self,
        sticker: str,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to delete a sticker from a set created by the bot. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#deletestickerfromset

        :param sticker: File identifier of the sticker
        :param request_timeout: Request timeout
        :return: Returns True on success.
        """
        call = DeleteStickerFromSet(
            sticker=sticker,
        )
        return await self(call, request_timeout=request_timeout)

    async def set_sticker_set_thumb(
        self,
        name: str,
        user_id: int,
        thumb: Optional[Union[InputFile, str]] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to set the thumbnail of a sticker set. Animated thumbnails can be set for animated sticker sets only. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#setstickersetthumb

        :param name: Sticker set name
        :param user_id: User identifier of the sticker set owner
        :param thumb: A **PNG** image with the thumbnail, must be up to 128 kilobytes in size and have width and height exactly 100px, or a **TGS** animation with the thumbnail up to 32 kilobytes in size; see `https://core.telegram.org/animated_stickers#technical-requirements <https://core.telegram.org/animated_stickers#technical-requirements>`_`https://core.telegram.org/animated_stickers#technical-requirements <https://core.telegram.org/animated_stickers#technical-requirements>`_ for animated sticker technical requirements. Pass a *file_id* as a String to send a file that already exists on the Telegram servers, pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. :ref:`More info on Sending Files » <sending-files>`. Animated sticker set thumbnail can't be uploaded via HTTP URL.
        :param request_timeout: Request timeout
        :return: Returns True on success.
        """
        call = SetStickerSetThumb(
            name=name,
            user_id=user_id,
            thumb=thumb,
        )
        return await self(call, request_timeout=request_timeout)

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
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to send answers to an inline query. On success, :code:`True` is returned.

        No more than **50** results per query are allowed.

        Source: https://core.telegram.org/bots/api#answerinlinequery

        :param inline_query_id: Unique identifier for the answered query
        :param results: A JSON-serialized array of results for the inline query
        :param cache_time: The maximum amount of time in seconds that the result of the inline query may be cached on the server. Defaults to 300.
        :param is_personal: Pass :code:`True`, if results may be cached on the server side only for the user that sent the query. By default, results may be returned to any user who sends the same query
        :param next_offset: Pass the offset that a client should send in the next query with the same text to receive more results. Pass an empty string if there are no more results or if you don't support pagination. Offset length can't exceed 64 bytes.
        :param switch_pm_text: If passed, clients will display a button with specified text that switches the user to a private chat with the bot and sends the bot a start message with the parameter *switch_pm_parameter*
        :param switch_pm_parameter: `Deep-linking <https://core.telegram.org/bots#deep-linking>`_ parameter for the /start message sent to the bot when user presses the switch button. 1-64 characters, only :code:`A-Z`, :code:`a-z`, :code:`0-9`, :code:`_` and :code:`-` are allowed.
        :param request_timeout: Request timeout
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
        return await self(call, request_timeout=request_timeout)

    # =============================================================================================
    # Group: Payments
    # Source: https://core.telegram.org/bots/api#payments
    # =============================================================================================

    async def send_invoice(
        self,
        chat_id: Union[int, str],
        title: str,
        description: str,
        payload: str,
        provider_token: str,
        currency: str,
        prices: List[LabeledPrice],
        max_tip_amount: Optional[int] = None,
        suggested_tip_amounts: Optional[List[int]] = None,
        start_parameter: Optional[str] = None,
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
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        Use this method to send invoices. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendinvoice

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param title: Product name, 1-32 characters
        :param description: Product description, 1-255 characters
        :param payload: Bot-defined invoice payload, 1-128 bytes. This will not be displayed to the user, use for your internal processes.
        :param provider_token: Payments provider token, obtained via `Botfather <https://t.me/botfather>`_
        :param currency: Three-letter ISO 4217 currency code, see `more on currencies <https://core.telegram.org/bots/payments#supported-currencies>`_
        :param prices: Price breakdown, a JSON-serialized list of components (e.g. product price, tax, discount, delivery cost, delivery tax, bonus, etc.)
        :param max_tip_amount: The maximum accepted amount for tips in the *smallest units* of the currency (integer, **not** float/double). For example, for a maximum tip of :code:`US$ 1.45` pass :code:`max_tip_amount = 145`. See the *exp* parameter in `currencies.json <https://core.telegram.org/bots/payments/currencies.json>`_, it shows the number of digits past the decimal point for each currency (2 for the majority of currencies). Defaults to 0
        :param suggested_tip_amounts: A JSON-serialized array of suggested amounts of tips in the *smallest units* of the currency (integer, **not** float/double). At most 4 suggested tip amounts can be specified. The suggested tip amounts must be positive, passed in a strictly increased order and must not exceed *max_tip_amount*.
        :param start_parameter: Unique deep-linking parameter. If left empty, **forwarded copies** of the sent message will have a *Pay* button, allowing multiple users to pay directly from the forwarded message, using the same invoice. If non-empty, forwarded copies of the sent message will have a *URL* button with a deep link to the bot (instead of a *Pay* button), with the value used as the start parameter
        :param provider_data: A JSON-serialized data about the invoice, which will be shared with the payment provider. A detailed description of required fields should be provided by the payment provider.
        :param photo_url: URL of the product photo for the invoice. Can be a photo of the goods or a marketing image for a service. People like it better when they see what they are paying for.
        :param photo_size: Photo size
        :param photo_width: Photo width
        :param photo_height: Photo height
        :param need_name: Pass :code:`True`, if you require the user's full name to complete the order
        :param need_phone_number: Pass :code:`True`, if you require the user's phone number to complete the order
        :param need_email: Pass :code:`True`, if you require the user's email address to complete the order
        :param need_shipping_address: Pass :code:`True`, if you require the user's shipping address to complete the order
        :param send_phone_number_to_provider: Pass :code:`True`, if user's phone number should be sent to provider
        :param send_email_to_provider: Pass :code:`True`, if user's email address should be sent to provider
        :param is_flexible: Pass :code:`True`, if the final price depends on the shipping method
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True`, if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_. If empty, one 'Pay :code:`total price`' button will be shown. If not empty, the first button must be a Pay button.
        :param request_timeout: Request timeout
        :return: On success, the sent Message is returned.
        """
        call = SendInvoice(
            chat_id=chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token=provider_token,
            currency=currency,
            prices=prices,
            max_tip_amount=max_tip_amount,
            suggested_tip_amounts=suggested_tip_amounts,
            start_parameter=start_parameter,
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
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def answer_shipping_query(
        self,
        shipping_query_id: str,
        ok: bool,
        shipping_options: Optional[List[ShippingOption]] = None,
        error_message: Optional[str] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        If you sent an invoice requesting a shipping address and the parameter *is_flexible* was specified, the Bot API will send an :class:`aiogram.types.update.Update` with a *shipping_query* field to the bot. Use this method to reply to shipping queries. On success, True is returned.

        Source: https://core.telegram.org/bots/api#answershippingquery

        :param shipping_query_id: Unique identifier for the query to be answered
        :param ok: Specify True if delivery to the specified address is possible and False if there are any problems (for example, if delivery to the specified address is not possible)
        :param shipping_options: Required if *ok* is True. A JSON-serialized array of available shipping options.
        :param error_message: Required if *ok* is False. Error message in human readable form that explains why it is impossible to complete the order (e.g. "Sorry, delivery to your desired address is unavailable'). Telegram will display this message to the user.
        :param request_timeout: Request timeout
        :return: On success, True is returned.
        """
        call = AnswerShippingQuery(
            shipping_query_id=shipping_query_id,
            ok=ok,
            shipping_options=shipping_options,
            error_message=error_message,
        )
        return await self(call, request_timeout=request_timeout)

    async def answer_pre_checkout_query(
        self,
        pre_checkout_query_id: str,
        ok: bool,
        error_message: Optional[str] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Once the user has confirmed their payment and shipping details, the Bot API sends the final confirmation in the form of an :class:`aiogram.types.update.Update` with the field *pre_checkout_query*. Use this method to respond to such pre-checkout queries. On success, True is returned. **Note:** The Bot API must receive an answer within 10 seconds after the pre-checkout query was sent.

        Source: https://core.telegram.org/bots/api#answerprecheckoutquery

        :param pre_checkout_query_id: Unique identifier for the query to be answered
        :param ok: Specify :code:`True` if everything is alright (goods are available, etc.) and the bot is ready to proceed with the order. Use :code:`False` if there are any problems.
        :param error_message: Required if *ok* is :code:`False`. Error message in human readable form that explains the reason for failure to proceed with the checkout (e.g. "Sorry, somebody just bought the last of our amazing black T-shirts while you were busy filling out your payment details. Please choose a different color or garment!"). Telegram will display this message to the user.
        :param request_timeout: Request timeout
        :return: On success, True is returned.
        """
        call = AnswerPreCheckoutQuery(
            pre_checkout_query_id=pre_checkout_query_id,
            ok=ok,
            error_message=error_message,
        )
        return await self(call, request_timeout=request_timeout)

    # =============================================================================================
    # Group: Telegram Passport
    # Source: https://core.telegram.org/bots/api#telegram-passport
    # =============================================================================================

    async def set_passport_data_errors(
        self,
        user_id: int,
        errors: List[PassportElementError],
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Informs a user that some of the Telegram Passport elements they provided contains errors. The user will not be able to re-submit their Passport to you until the errors are fixed (the contents of the field for which you returned the error must change). Returns :code:`True` on success.
        Use this if the data submitted by the user doesn't satisfy the standards your service requires for any reason. For example, if a birthday date seems invalid, a submitted document is blurry, a scan shows evidence of tampering, etc. Supply some details in the error message to make sure the user knows how to correct the issues.

        Source: https://core.telegram.org/bots/api#setpassportdataerrors

        :param user_id: User identifier
        :param errors: A JSON-serialized array describing the errors
        :param request_timeout: Request timeout
        :return: The user will not be able to re-submit their Passport to you until the errors are
            fixed (the contents of the field for which you returned the error must change).
            Returns True on success.
        """
        call = SetPassportDataErrors(
            user_id=user_id,
            errors=errors,
        )
        return await self(call, request_timeout=request_timeout)

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
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        Use this method to send a game. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendgame

        :param chat_id: Unique identifier for the target chat
        :param game_short_name: Short name of the game, serves as the unique identifier for the game. Set up your games via `Botfather <https://t.me/botfather>`_.
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True`, if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_. If empty, one 'Play game_title' button will be shown. If not empty, the first button must launch the game.
        :param request_timeout: Request timeout
        :return: On success, the sent Message is returned.
        """
        call = SendGame(
            chat_id=chat_id,
            game_short_name=game_short_name,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def set_game_score(
        self,
        user_id: int,
        score: int,
        force: Optional[bool] = None,
        disable_edit_message: Optional[bool] = None,
        chat_id: Optional[int] = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
        request_timeout: Optional[int] = None,
    ) -> Union[Message, bool]:
        """
        Use this method to set the score of the specified user in a game. On success, if the message was sent by the bot, returns the edited :class:`aiogram.types.message.Message`, otherwise returns :code:`True`. Returns an error, if the new score is not greater than the user's current score in the chat and *force* is :code:`False`.

        Source: https://core.telegram.org/bots/api#setgamescore

        :param user_id: User identifier
        :param score: New score, must be non-negative
        :param force: Pass True, if the high score is allowed to decrease. This can be useful when fixing mistakes or banning cheaters
        :param disable_edit_message: Pass True, if the game message should not be automatically edited to include the current scoreboard
        :param chat_id: Required if *inline_message_id* is not specified. Unique identifier for the target chat
        :param message_id: Required if *inline_message_id* is not specified. Identifier of the sent message
        :param inline_message_id: Required if *chat_id* and *message_id* are not specified. Identifier of the inline message
        :param request_timeout: Request timeout
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
        return await self(call, request_timeout=request_timeout)

    async def get_game_high_scores(
        self,
        user_id: int,
        chat_id: Optional[int] = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
        request_timeout: Optional[int] = None,
    ) -> List[GameHighScore]:
        """
        Use this method to get data for high score tables. Will return the score of the specified user and several of their neighbors in a game. On success, returns an *Array* of :class:`aiogram.types.game_high_score.GameHighScore` objects.

         This method will currently return scores for the target user, plus two of their closest neighbors on each side. Will also return the top three users if the user and his neighbors are not among them. Please note that this behavior is subject to change.

        Source: https://core.telegram.org/bots/api#getgamehighscores

        :param user_id: Target user id
        :param chat_id: Required if *inline_message_id* is not specified. Unique identifier for the target chat
        :param message_id: Required if *inline_message_id* is not specified. Identifier of the sent message
        :param inline_message_id: Required if *chat_id* and *message_id* are not specified. Identifier of the inline message
        :param request_timeout: Request timeout
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
        return await self(call, request_timeout=request_timeout)
