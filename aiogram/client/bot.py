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

from aiogram.utils.mixins import ContextInstanceMixin
from aiogram.utils.token import extract_bot_id, validate_token

from ..methods import (
    AddStickerToSet,
    AnswerCallbackQuery,
    AnswerInlineQuery,
    AnswerPreCheckoutQuery,
    AnswerShippingQuery,
    AnswerWebAppQuery,
    ApproveChatJoinRequest,
    BanChatMember,
    BanChatSenderChat,
    Close,
    CloseForumTopic,
    CloseGeneralForumTopic,
    CopyMessage,
    CreateChatInviteLink,
    CreateForumTopic,
    CreateInvoiceLink,
    CreateNewStickerSet,
    DeclineChatJoinRequest,
    DeleteChatPhoto,
    DeleteChatStickerSet,
    DeleteForumTopic,
    DeleteMessage,
    DeleteMyCommands,
    DeleteStickerFromSet,
    DeleteWebhook,
    EditChatInviteLink,
    EditForumTopic,
    EditGeneralForumTopic,
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
    GetChatMenuButton,
    GetCustomEmojiStickers,
    GetFile,
    GetForumTopicIconStickers,
    GetGameHighScores,
    GetMe,
    GetMyCommands,
    GetMyDefaultAdministratorRights,
    GetStickerSet,
    GetUpdates,
    GetUserProfilePhotos,
    GetWebhookInfo,
    HideGeneralForumTopic,
    LeaveChat,
    LogOut,
    PinChatMessage,
    PromoteChatMember,
    ReopenForumTopic,
    ReopenGeneralForumTopic,
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
    SetChatMenuButton,
    SetChatPermissions,
    SetChatPhoto,
    SetChatStickerSet,
    SetChatTitle,
    SetGameScore,
    SetMyCommands,
    SetMyDefaultAdministratorRights,
    SetPassportDataErrors,
    SetStickerPositionInSet,
    SetStickerSetThumb,
    SetWebhook,
    StopMessageLiveLocation,
    StopPoll,
    TelegramMethod,
    UnbanChatMember,
    UnbanChatSenderChat,
    UnhideGeneralForumTopic,
    UnpinAllChatMessages,
    UnpinAllForumTopicMessages,
    UnpinChatMessage,
    UploadStickerFile,
)
from ..types import (
    UNSET,
    BotCommand,
    BotCommandScope,
    Chat,
    ChatAdministratorRights,
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
    ForumTopic,
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
    MenuButtonCommands,
    MenuButtonDefault,
    MenuButtonWebApp,
    Message,
    MessageEntity,
    MessageId,
    PassportElementError,
    Poll,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    SentWebAppMessage,
    ShippingOption,
    Sticker,
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
        self._me: Optional[User] = None

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

    async def me(self) -> User:
        """
        Cached alias for getMe method

        :return:
        """
        if self._me is None:  # pragma: no cover
            self._me = await self.get_me()
        return self._me

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
                str(self.session.api.wrap_local_file.to_local(file_path)), chunk_size=chunk_size
            )
            close_stream = True
        else:
            url = self.session.api.file_url(self.__token, file_path)
            stream = self.session.stream_content(url=url, timeout=timeout, chunk_size=chunk_size)

        try:
            if isinstance(destination, (str, pathlib.Path)):
                await self.__download_file(destination=destination, stream=stream)
                return None
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
            # type is ignored in due to:
            # Incompatible types in assignment (expression has type "Optional[Any]", variable has type "str")
            file_id = getattr(file, "file_id", None)  # type: ignore
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

    async def add_sticker_to_set(
        self,
        user_id: int,
        name: str,
        emojis: str,
        png_sticker: Optional[Union[InputFile, str]] = None,
        tgs_sticker: Optional[InputFile] = None,
        webm_sticker: Optional[InputFile] = None,
        mask_position: Optional[MaskPosition] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to add a new sticker to a set created by the bot. You **must** use exactly one of the fields *png_sticker*, *tgs_sticker*, or *webm_sticker*. Animated stickers can be added to animated sticker sets and only to them. Animated sticker sets can have up to 50 stickers. Static sticker sets can have up to 120 stickers. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'addstickertoset', 'name': 'addStickerToSet', 'description': 'Use this method to add a new sticker to a set created by the bot. You must use exactly one of the fields png_sticker, tgs_sticker, or webm_sticker. Animated stickers can be added to animated sticker sets and only to them. Animated sticker sets can have up to 50 stickers. Static sticker sets can have up to 120 stickers. Returns True on success.', 'html_description': '<p>Use this method to add a new sticker to a set created by the bot. You <strong>must</strong> use exactly one of the fields <em>png_sticker</em>, <em>tgs_sticker</em>, or <em>webm_sticker</em>. Animated stickers can be added to animated sticker sets and only to them. Animated sticker sets can have up to 50 stickers. Static sticker sets can have up to 120 stickers. Returns <em>True</em> on success.</p>', 'rst_description': 'Use this method to add a new sticker to a set created by the bot. You **must** use exactly one of the fields *png_sticker*, *tgs_sticker*, or *webm_sticker*. Animated stickers can be added to animated sticker sets and only to them. Animated sticker sets can have up to 50 stickers. Static sticker sets can have up to 120 stickers. Returns :code:`True` on success.', 'annotations': [{'type': 'Integer', 'required': True, 'description': 'User identifier of sticker set owner', 'html_description': '<td>User identifier of sticker set owner</td>', 'rst_description': 'User identifier of sticker set owner\n', 'name': 'user_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'String', 'required': True, 'description': 'Sticker set name', 'html_description': '<td>Sticker set name</td>', 'rst_description': 'Sticker set name\n', 'name': 'name', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': True, 'description': 'One or more emoji corresponding to the sticker', 'html_description': '<td>One or more emoji corresponding to the sticker</td>', 'rst_description': 'One or more emoji corresponding to the sticker\n', 'name': 'emojis', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'InputFile or String', 'required': False, 'description': 'PNG image with the sticker, must be up to 512 kilobytes in size, dimensions must not exceed 512px, and either width or height must be exactly 512px. Pass a file_id as a String to send a file that already exists on the Telegram servers, pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. More information on Sending Files', 'html_description': '<td><strong>PNG</strong> image with the sticker, must be up to 512 kilobytes in size, dimensions must not exceed 512px, and either width or height must be exactly 512px. Pass a <em>file_id</em> as a String to send a file that already exists on the Telegram servers, pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. <a href="#sending-files">More information on Sending Files &#187;</a></td>', 'rst_description': '**PNG** image with the sticker, must be up to 512 kilobytes in size, dimensions must not exceed 512px, and either width or height must be exactly 512px. Pass a *file_id* as a String to send a file that already exists on the Telegram servers, pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`\n', 'name': 'png_sticker', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InputFile'}}, {'type': 'std', 'name': 'str'}]}}, {'type': 'InputFile', 'required': False, 'description': 'TGS animation with the sticker, uploaded using multipart/form-data. See https://core.telegram.org/stickers#animated-sticker-requirements for technical requirements', 'html_description': '<td><strong>TGS</strong> animation with the sticker, uploaded using multipart/form-data. See <a href="/stickers#animated-sticker-requirements"/><a href="https://core.telegram.org/stickers#animated-sticker-requirements">https://core.telegram.org/stickers#animated-sticker-requirements</a> for technical requirements</td>', 'rst_description': '**TGS** animation with the sticker, uploaded using multipart/form-data. See `https://core.telegram.org/stickers#animated-sticker-requirements <https://core.telegram.org/stickers#animated-sticker-requirements>`_`https://core.telegram.org/stickers#animated-sticker-requirements <https://core.telegram.org/stickers#animated-sticker-requirements>`_ for technical requirements\n', 'name': 'tgs_sticker', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'InputFile'}}}, {'type': 'InputFile', 'required': False, 'description': 'WEBM video with the sticker, uploaded using multipart/form-data. See https://core.telegram.org/stickers#video-sticker-requirements for technical requirements', 'html_description': '<td><strong>WEBM</strong> video with the sticker, uploaded using multipart/form-data. See <a href="/stickers#video-sticker-requirements"/><a href="https://core.telegram.org/stickers#video-sticker-requirements">https://core.telegram.org/stickers#video-sticker-requirements</a> for technical requirements</td>', 'rst_description': '**WEBM** video with the sticker, uploaded using multipart/form-data. See `https://core.telegram.org/stickers#video-sticker-requirements <https://core.telegram.org/stickers#video-sticker-requirements>`_`https://core.telegram.org/stickers#video-sticker-requirements <https://core.telegram.org/stickers#video-sticker-requirements>`_ for technical requirements\n', 'name': 'webm_sticker', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'InputFile'}}}, {'type': 'MaskPosition', 'required': False, 'description': 'A JSON-serialized object for position where the mask should be placed on faces', 'html_description': '<td>A JSON-serialized object for position where the mask should be placed on faces</td>', 'rst_description': 'A JSON-serialized object for position where the mask should be placed on faces\n', 'name': 'mask_position', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'MaskPosition'}}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param user_id: User identifier of sticker set owner
        :param name: Sticker set name
        :param emojis: One or more emoji corresponding to the sticker
        :param png_sticker: **PNG** image with the sticker, must be up to 512 kilobytes in size, dimensions must not exceed 512px, and either width or height must be exactly 512px. Pass a *file_id* as a String to send a file that already exists on the Telegram servers, pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`
        :param tgs_sticker: **TGS** animation with the sticker, uploaded using multipart/form-data. See `https://core.telegram.org/stickers#animated-sticker-requirements <https://core.telegram.org/stickers#animated-sticker-requirements>`_`https://core.telegram.org/stickers#animated-sticker-requirements <https://core.telegram.org/stickers#animated-sticker-requirements>`_ for technical requirements
        :param webm_sticker: **WEBM** video with the sticker, uploaded using multipart/form-data. See `https://core.telegram.org/stickers#video-sticker-requirements <https://core.telegram.org/stickers#video-sticker-requirements>`_`https://core.telegram.org/stickers#video-sticker-requirements <https://core.telegram.org/stickers#video-sticker-requirements>`_ for technical requirements
        :param mask_position: A JSON-serialized object for position where the mask should be placed on faces
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = AddStickerToSet(
            user_id=user_id,
            name=name,
            emojis=emojis,
            png_sticker=png_sticker,
            tgs_sticker=tgs_sticker,
            webm_sticker=webm_sticker,
            mask_position=mask_position,
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
        Use this method to send answers to callback queries sent from `inline keyboards <https://core.telegram.org/bots/features#inline-keyboards>`_. The answer will be displayed to the user as a notification at the top of the chat screen or as an alert. On success, :code:`True` is returned.

         Alternatively, the user can be redirected to the specified Game URL. For this option to work, you must first create a game for your bot via `@BotFather <https://t.me/botfather>`_ and accept the terms. Otherwise, you may use links like :code:`t.me/your_bot?start=XXXX` that open your bot with a parameter.

        Source: https://core.telegram.org/bots/api#{'anchor': 'answercallbackquery', 'name': 'answerCallbackQuery', 'description': 'Use this method to send answers to callback queries sent from inline keyboards. The answer will be displayed to the user as a notification at the top of the chat screen or as an alert. On success, True is returned.\nAlternatively, the user can be redirected to the specified Game URL. For this option to work, you must first create a game for your bot via @BotFather and accept the terms. Otherwise, you may use links like t.me/your_bot?start=XXXX that open your bot with a parameter.', 'html_description': '<p>Use this method to send answers to callback queries sent from <a href="/bots/features#inline-keyboards">inline keyboards</a>. The answer will be displayed to the user as a notification at the top of the chat screen or as an alert. On success, <em>True</em> is returned.</p><blockquote>\n<p>Alternatively, the user can be redirected to the specified Game URL. For this option to work, you must first create a game for your bot via <a href="https://t.me/botfather">@BotFather</a> and accept the terms. Otherwise, you may use links like <code>t.me/your_bot?start=XXXX</code> that open your bot with a parameter.</p>\n</blockquote>', 'rst_description': 'Use this method to send answers to callback queries sent from `inline keyboards <https://core.telegram.org/bots/features#inline-keyboards>`_. The answer will be displayed to the user as a notification at the top of the chat screen or as an alert. On success, :code:`True` is returned.\n\n Alternatively, the user can be redirected to the specified Game URL. For this option to work, you must first create a game for your bot via `@BotFather <https://t.me/botfather>`_ and accept the terms. Otherwise, you may use links like :code:`t.me/your_bot?start=XXXX` that open your bot with a parameter.', 'annotations': [{'type': 'String', 'required': True, 'description': 'Unique identifier for the query to be answered', 'html_description': '<td>Unique identifier for the query to be answered</td>', 'rst_description': 'Unique identifier for the query to be answered\n', 'name': 'callback_query_id', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': False, 'description': 'Text of the notification. If not specified, nothing will be shown to the user, 0-200 characters', 'html_description': '<td>Text of the notification. If not specified, nothing will be shown to the user, 0-200 characters</td>', 'rst_description': 'Text of the notification. If not specified, nothing will be shown to the user, 0-200 characters\n', 'name': 'text', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'Boolean', 'required': False, 'description': 'If True, an alert will be shown by the client instead of a notification at the top of the chat screen. Defaults to false.', 'html_description': '<td>If <em>True</em>, an alert will be shown by the client instead of a notification at the top of the chat screen. Defaults to <em>false</em>.</td>', 'rst_description': 'If :code:`True`, an alert will be shown by the client instead of a notification at the top of the chat screen. Defaults to *false*.\n', 'name': 'show_alert', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'String', 'required': False, 'description': "URL that will be opened by the user's client. If you have created a Game and accepted the conditions via @BotFather, specify the URL that opens your game - note that this will only work if the query comes from a callback_game button.\n\nOtherwise, you may use links like t.me/your_bot?start=XXXX that open your bot with a parameter.", 'html_description': '<td>URL that will be opened by the user\'s client. If you have created a <a href="#game">Game</a> and accepted the conditions via <a href="https://t.me/botfather">@BotFather</a>, specify the URL that opens your game - note that this will only work if the query comes from a <a href="#inlinekeyboardbutton"><em>callback_game</em></a> button.<br/>\n<br/>\nOtherwise, you may use links like <code>t.me/your_bot?start=XXXX</code> that open your bot with a parameter.</td>', 'rst_description': "URL that will be opened by the user's client. If you have created a :class:`aiogram.types.game.Game` and accepted the conditions via `@BotFather <https://t.me/botfather>`_, specify the URL that opens your game - note that this will only work if the query comes from a `https://core.telegram.org/bots/api#inlinekeyboardbutton <https://core.telegram.org/bots/api#inlinekeyboardbutton>`_ *callback_game* button.\n\n\n\nOtherwise, you may use links like :code:`t.me/your_bot?start=XXXX` that open your bot with a parameter.\n", 'name': 'url', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'Integer', 'required': False, 'description': 'The maximum amount of time in seconds that the result of the callback query may be cached client-side. Telegram apps will support caching starting in version 3.14. Defaults to 0.', 'html_description': '<td>The maximum amount of time in seconds that the result of the callback query may be cached client-side. Telegram apps will support caching starting in version 3.14. Defaults to 0.</td>', 'rst_description': 'The maximum amount of time in seconds that the result of the callback query may be cached client-side. Telegram apps will support caching starting in version 3.14. Defaults to 0.\n', 'name': 'cache_time', 'parsed_type': {'type': 'std', 'name': 'int'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'On success, True is returned.'}, 'bases': ['TelegramMethod']}

        :param callback_query_id: Unique identifier for the query to be answered
        :param text: Text of the notification. If not specified, nothing will be shown to the user, 0-200 characters
        :param show_alert: If :code:`True`, an alert will be shown by the client instead of a notification at the top of the chat screen. Defaults to *false*.
        :param url: URL that will be opened by the user's client. If you have created a :class:`aiogram.types.game.Game` and accepted the conditions via `@BotFather <https://t.me/botfather>`_, specify the URL that opens your game - note that this will only work if the query comes from a `https://core.telegram.org/bots/api#inlinekeyboardbutton <https://core.telegram.org/bots/api#inlinekeyboardbutton>`_ *callback_game* button.
        :param cache_time: The maximum amount of time in seconds that the result of the callback query may be cached client-side. Telegram apps will support caching starting in version 3.14. Defaults to 0.
        :param request_timeout: Request timeout
        :return: Otherwise, you may use links like :code:`t.me/your_bot?start=XXXX` that open your bot with a parameter.
        """

        call = AnswerCallbackQuery(
            callback_query_id=callback_query_id,
            text=text,
            show_alert=show_alert,
            url=url,
            cache_time=cache_time,
        )
        return await self(call, request_timeout=request_timeout)

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

        Source: https://core.telegram.org/bots/api#{'anchor': 'answerinlinequery', 'name': 'answerInlineQuery', 'description': 'Use this method to send answers to an inline query. On success, True is returned.\nNo more than 50 results per query are allowed.', 'html_description': '<p>Use this method to send answers to an inline query. On success, <em>True</em> is returned.<br/>\nNo more than <strong>50</strong> results per query are allowed.</p>', 'rst_description': 'Use this method to send answers to an inline query. On success, :code:`True` is returned.\n\nNo more than **50** results per query are allowed.', 'annotations': [{'type': 'String', 'required': True, 'description': 'Unique identifier for the answered query', 'html_description': '<td>Unique identifier for the answered query</td>', 'rst_description': 'Unique identifier for the answered query\n', 'name': 'inline_query_id', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'Array of InlineQueryResult', 'required': True, 'description': 'A JSON-serialized array of results for the inline query', 'html_description': '<td>A JSON-serialized array of results for the inline query</td>', 'rst_description': 'A JSON-serialized array of results for the inline query\n', 'name': 'results', 'parsed_type': {'type': 'array', 'items': {'type': 'entity', 'references': {'category': 'types', 'name': 'InlineQueryResult'}}}}, {'type': 'Integer', 'required': False, 'description': 'The maximum amount of time in seconds that the result of the inline query may be cached on the server. Defaults to 300.', 'html_description': '<td>The maximum amount of time in seconds that the result of the inline query may be cached on the server. Defaults to 300.</td>', 'rst_description': 'The maximum amount of time in seconds that the result of the inline query may be cached on the server. Defaults to 300.\n', 'name': 'cache_time', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if results may be cached on the server side only for the user that sent the query. By default, results may be returned to any user who sends the same query', 'html_description': '<td>Pass <em>True</em> if results may be cached on the server side only for the user that sent the query. By default, results may be returned to any user who sends the same query</td>', 'rst_description': 'Pass :code:`True` if results may be cached on the server side only for the user that sent the query. By default, results may be returned to any user who sends the same query\n', 'name': 'is_personal', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'String', 'required': False, 'description': "Pass the offset that a client should send in the next query with the same text to receive more results. Pass an empty string if there are no more results or if you don't support pagination. Offset length can't exceed 64 bytes.", 'html_description': "<td>Pass the offset that a client should send in the next query with the same text to receive more results. Pass an empty string if there are no more results or if you don't support pagination. Offset length can't exceed 64 bytes.</td>", 'rst_description': "Pass the offset that a client should send in the next query with the same text to receive more results. Pass an empty string if there are no more results or if you don't support pagination. Offset length can't exceed 64 bytes.\n", 'name': 'next_offset', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': False, 'description': 'If passed, clients will display a button with specified text that switches the user to a private chat with the bot and sends the bot a start message with the parameter switch_pm_parameter', 'html_description': '<td>If passed, clients will display a button with specified text that switches the user to a private chat with the bot and sends the bot a start message with the parameter <em>switch_pm_parameter</em></td>', 'rst_description': 'If passed, clients will display a button with specified text that switches the user to a private chat with the bot and sends the bot a start message with the parameter *switch_pm_parameter*\n', 'name': 'switch_pm_text', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': False, 'description': "Deep-linking parameter for the /start message sent to the bot when user presses the switch button. 1-64 characters, only A-Z, a-z, 0-9, _ and - are allowed.\n\nExample: An inline bot that sends YouTube videos can ask the user to connect the bot to their YouTube account to adapt search results accordingly. To do this, it displays a 'Connect your YouTube account' button above the results, or even before showing any. The user presses the button, switches to a private chat with the bot and, in doing so, passes a start parameter that instructs the bot to return an OAuth link. Once done, the bot can offer a switch_inline button so that the user can easily return to the chat where they wanted to use the bot's inline capabilities.", 'html_description': '<td><a href="/bots/features#deep-linking">Deep-linking</a> parameter for the /start message sent to the bot when user presses the switch button. 1-64 characters, only <code>A-Z</code>, <code>a-z</code>, <code>0-9</code>, <code>_</code> and <code>-</code> are allowed.<br/>\n<br/>\n<em>Example:</em> An inline bot that sends YouTube videos can ask the user to connect the bot to their YouTube account to adapt search results accordingly. To do this, it displays a \'Connect your YouTube account\' button above the results, or even before showing any. The user presses the button, switches to a private chat with the bot and, in doing so, passes a start parameter that instructs the bot to return an OAuth link. Once done, the bot can offer a <a href="#inlinekeyboardmarkup"><em>switch_inline</em></a> button so that the user can easily return to the chat where they wanted to use the bot\'s inline capabilities.</td>', 'rst_description': "`Deep-linking <https://core.telegram.org/bots/features#deep-linking>`_ parameter for the /start message sent to the bot when user presses the switch button. 1-64 characters, only :code:`A-Z`, :code:`a-z`, :code:`0-9`, :code:`_` and :code:`-` are allowed.\n\n\n\n*Example:* An inline bot that sends YouTube videos can ask the user to connect the bot to their YouTube account to adapt search results accordingly. To do this, it displays a 'Connect your YouTube account' button above the results, or even before showing any. The user presses the button, switches to a private chat with the bot and, in doing so, passes a start parameter that instructs the bot to return an OAuth link. Once done, the bot can offer a `https://core.telegram.org/bots/api#inlinekeyboardmarkup <https://core.telegram.org/bots/api#inlinekeyboardmarkup>`_ *switch_inline* button so that the user can easily return to the chat where they wanted to use the bot's inline capabilities.\n", 'name': 'switch_pm_parameter', 'parsed_type': {'type': 'std', 'name': 'str'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'On success, True is returned.'}, 'bases': ['TelegramMethod']}

        :param inline_query_id: Unique identifier for the answered query
        :param results: A JSON-serialized array of results for the inline query
        :param cache_time: The maximum amount of time in seconds that the result of the inline query may be cached on the server. Defaults to 300.
        :param is_personal: Pass :code:`True` if results may be cached on the server side only for the user that sent the query. By default, results may be returned to any user who sends the same query
        :param next_offset: Pass the offset that a client should send in the next query with the same text to receive more results. Pass an empty string if there are no more results or if you don't support pagination. Offset length can't exceed 64 bytes.
        :param switch_pm_text: If passed, clients will display a button with specified text that switches the user to a private chat with the bot and sends the bot a start message with the parameter *switch_pm_parameter*
        :param switch_pm_parameter: `Deep-linking <https://core.telegram.org/bots/features#deep-linking>`_ parameter for the /start message sent to the bot when user presses the switch button. 1-64 characters, only :code:`A-Z`, :code:`a-z`, :code:`0-9`, :code:`_` and :code:`-` are allowed.
        :param request_timeout: Request timeout
        :return: On success, :code:`True` is returned.
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

    async def answer_pre_checkout_query(
        self,
        pre_checkout_query_id: str,
        ok: bool,
        error_message: Optional[str] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Once the user has confirmed their payment and shipping details, the Bot API sends the final confirmation in the form of an :class:`aiogram.types.update.Update` with the field *pre_checkout_query*. Use this method to respond to such pre-checkout queries. On success, :code:`True` is returned. **Note:** The Bot API must receive an answer within 10 seconds after the pre-checkout query was sent.

        Source: https://core.telegram.org/bots/api#{'anchor': 'answerprecheckoutquery', 'name': 'answerPreCheckoutQuery', 'description': 'Once the user has confirmed their payment and shipping details, the Bot API sends the final confirmation in the form of an Update with the field pre_checkout_query. Use this method to respond to such pre-checkout queries. On success, True is returned. Note: The Bot API must receive an answer within 10 seconds after the pre-checkout query was sent.', 'html_description': '<p>Once the user has confirmed their payment and shipping details, the Bot API sends the final confirmation in the form of an <a href="#update">Update</a> with the field <em>pre_checkout_query</em>. Use this method to respond to such pre-checkout queries. On success, <em>True</em> is returned. <strong>Note:</strong> The Bot API must receive an answer within 10 seconds after the pre-checkout query was sent.</p>', 'rst_description': 'Once the user has confirmed their payment and shipping details, the Bot API sends the final confirmation in the form of an :class:`aiogram.types.update.Update` with the field *pre_checkout_query*. Use this method to respond to such pre-checkout queries. On success, :code:`True` is returned. **Note:** The Bot API must receive an answer within 10 seconds after the pre-checkout query was sent.', 'annotations': [{'type': 'String', 'required': True, 'description': 'Unique identifier for the query to be answered', 'html_description': '<td>Unique identifier for the query to be answered</td>', 'rst_description': 'Unique identifier for the query to be answered\n', 'name': 'pre_checkout_query_id', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'Boolean', 'required': True, 'description': 'Specify True if everything is alright (goods are available, etc.) and the bot is ready to proceed with the order. Use False if there are any problems.', 'html_description': '<td>Specify <em>True</em> if everything is alright (goods are available, etc.) and the bot is ready to proceed with the order. Use <em>False</em> if there are any problems.</td>', 'rst_description': 'Specify :code:`True` if everything is alright (goods are available, etc.) and the bot is ready to proceed with the order. Use :code:`False` if there are any problems.\n', 'name': 'ok', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'String', 'required': False, 'description': 'Required if ok is False. Error message in human readable form that explains the reason for failure to proceed with the checkout (e.g. "Sorry, somebody just bought the last of our amazing black T-shirts while you were busy filling out your payment details. Please choose a different color or garment!"). Telegram will display this message to the user.', 'html_description': '<td>Required if <em>ok</em> is <em>False</em>. Error message in human readable form that explains the reason for failure to proceed with the checkout (e.g. "Sorry, somebody just bought the last of our amazing black T-shirts while you were busy filling out your payment details. Please choose a different color or garment!"). Telegram will display this message to the user.</td>', 'rst_description': 'Required if *ok* is :code:`False`. Error message in human readable form that explains the reason for failure to proceed with the checkout (e.g. "Sorry, somebody just bought the last of our amazing black T-shirts while you were busy filling out your payment details. Please choose a different color or garment!"). Telegram will display this message to the user.\n', 'name': 'error_message', 'parsed_type': {'type': 'std', 'name': 'str'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'On success, True is returned.'}, 'bases': ['TelegramMethod']}

        :param pre_checkout_query_id: Unique identifier for the query to be answered
        :param ok: Specify :code:`True` if everything is alright (goods are available, etc.) and the bot is ready to proceed with the order. Use :code:`False` if there are any problems.
        :param error_message: Required if *ok* is :code:`False`. Error message in human readable form that explains the reason for failure to proceed with the checkout (e.g. "Sorry, somebody just bought the last of our amazing black T-shirts while you were busy filling out your payment details. Please choose a different color or garment!"). Telegram will display this message to the user.
        :param request_timeout: Request timeout
        :return: **Note:** The Bot API must receive an answer within 10 seconds after the pre-checkout query was sent.
        """

        call = AnswerPreCheckoutQuery(
            pre_checkout_query_id=pre_checkout_query_id,
            ok=ok,
            error_message=error_message,
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
        If you sent an invoice requesting a shipping address and the parameter *is_flexible* was specified, the Bot API will send an :class:`aiogram.types.update.Update` with a *shipping_query* field to the bot. Use this method to reply to shipping queries. On success, :code:`True` is returned.

        Source: https://core.telegram.org/bots/api#{'anchor': 'answershippingquery', 'name': 'answerShippingQuery', 'description': 'If you sent an invoice requesting a shipping address and the parameter is_flexible was specified, the Bot API will send an Update with a shipping_query field to the bot. Use this method to reply to shipping queries. On success, True is returned.', 'html_description': '<p>If you sent an invoice requesting a shipping address and the parameter <em>is_flexible</em> was specified, the Bot API will send an <a href="#update">Update</a> with a <em>shipping_query</em> field to the bot. Use this method to reply to shipping queries. On success, <em>True</em> is returned.</p>', 'rst_description': 'If you sent an invoice requesting a shipping address and the parameter *is_flexible* was specified, the Bot API will send an :class:`aiogram.types.update.Update` with a *shipping_query* field to the bot. Use this method to reply to shipping queries. On success, :code:`True` is returned.', 'annotations': [{'type': 'String', 'required': True, 'description': 'Unique identifier for the query to be answered', 'html_description': '<td>Unique identifier for the query to be answered</td>', 'rst_description': 'Unique identifier for the query to be answered\n', 'name': 'shipping_query_id', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'Boolean', 'required': True, 'description': 'Pass True if delivery to the specified address is possible and False if there are any problems (for example, if delivery to the specified address is not possible)', 'html_description': '<td>Pass <em>True</em> if delivery to the specified address is possible and <em>False</em> if there are any problems (for example, if delivery to the specified address is not possible)</td>', 'rst_description': 'Pass :code:`True` if delivery to the specified address is possible and :code:`False` if there are any problems (for example, if delivery to the specified address is not possible)\n', 'name': 'ok', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Array of ShippingOption', 'required': False, 'description': 'Required if ok is True. A JSON-serialized array of available shipping options.', 'html_description': '<td>Required if <em>ok</em> is <em>True</em>. A JSON-serialized array of available shipping options.</td>', 'rst_description': 'Required if *ok* is :code:`True`. A JSON-serialized array of available shipping options.\n', 'name': 'shipping_options', 'parsed_type': {'type': 'array', 'items': {'type': 'entity', 'references': {'category': 'types', 'name': 'ShippingOption'}}}}, {'type': 'String', 'required': False, 'description': 'Required if ok is False. Error message in human readable form that explains why it is impossible to complete the order (e.g. "Sorry, delivery to your desired address is unavailable\'). Telegram will display this message to the user.', 'html_description': '<td>Required if <em>ok</em> is <em>False</em>. Error message in human readable form that explains why it is impossible to complete the order (e.g. "Sorry, delivery to your desired address is unavailable\'). Telegram will display this message to the user.</td>', 'rst_description': 'Required if *ok* is :code:`False`. Error message in human readable form that explains why it is impossible to complete the order (e.g. "Sorry, delivery to your desired address is unavailable\'). Telegram will display this message to the user.\n', 'name': 'error_message', 'parsed_type': {'type': 'std', 'name': 'str'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'On success, True is returned.'}, 'bases': ['TelegramMethod']}

        :param shipping_query_id: Unique identifier for the query to be answered
        :param ok: Pass :code:`True` if delivery to the specified address is possible and :code:`False` if there are any problems (for example, if delivery to the specified address is not possible)
        :param shipping_options: Required if *ok* is :code:`True`. A JSON-serialized array of available shipping options.
        :param error_message: Required if *ok* is :code:`False`. Error message in human readable form that explains why it is impossible to complete the order (e.g. "Sorry, delivery to your desired address is unavailable'). Telegram will display this message to the user.
        :param request_timeout: Request timeout
        :return: On success, :code:`True` is returned.
        """

        call = AnswerShippingQuery(
            shipping_query_id=shipping_query_id,
            ok=ok,
            shipping_options=shipping_options,
            error_message=error_message,
        )
        return await self(call, request_timeout=request_timeout)

    async def answer_web_app_query(
        self,
        web_app_query_id: str,
        result: InlineQueryResult,
        request_timeout: Optional[int] = None,
    ) -> SentWebAppMessage:
        """
        Use this method to set the result of an interaction with a `Web App <https://core.telegram.org/bots/webapps>`_ and send a corresponding message on behalf of the user to the chat from which the query originated. On success, a :class:`aiogram.types.sent_web_app_message.SentWebAppMessage` object is returned.

        Source: https://core.telegram.org/bots/api#{'anchor': 'answerwebappquery', 'name': 'answerWebAppQuery', 'description': 'Use this method to set the result of an interaction with a Web App and send a corresponding message on behalf of the user to the chat from which the query originated. On success, a SentWebAppMessage object is returned.', 'html_description': '<p>Use this method to set the result of an interaction with a <a href="/bots/webapps">Web App</a> and send a corresponding message on behalf of the user to the chat from which the query originated. On success, a <a href="#sentwebappmessage">SentWebAppMessage</a> object is returned.</p>', 'rst_description': 'Use this method to set the result of an interaction with a `Web App <https://core.telegram.org/bots/webapps>`_ and send a corresponding message on behalf of the user to the chat from which the query originated. On success, a :class:`aiogram.types.sent_web_app_message.SentWebAppMessage` object is returned.', 'annotations': [{'type': 'String', 'required': True, 'description': 'Unique identifier for the query to be answered', 'html_description': '<td>Unique identifier for the query to be answered</td>', 'rst_description': 'Unique identifier for the query to be answered\n', 'name': 'web_app_query_id', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'InlineQueryResult', 'required': True, 'description': 'A JSON-serialized object describing the message to be sent', 'html_description': '<td>A JSON-serialized object describing the message to be sent</td>', 'rst_description': 'A JSON-serialized object describing the message to be sent\n', 'name': 'result', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'InlineQueryResult'}}}], 'category': 'methods', 'returning': {'type': 'SentWebAppMessage', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'SentWebAppMessage'}}, 'description': 'On success, a SentWebAppMessage object is returned.'}, 'bases': ['TelegramMethod']}

        :param web_app_query_id: Unique identifier for the query to be answered
        :param result: A JSON-serialized object describing the message to be sent
        :param request_timeout: Request timeout
        :return: On success, a :class:`aiogram.types.sent_web_app_message.SentWebAppMessage` object is returned.
        """

        call = AnswerWebAppQuery(
            web_app_query_id=web_app_query_id,
            result=result,
        )
        return await self(call, request_timeout=request_timeout)

    async def approve_chat_join_request(
        self,
        chat_id: Union[int, str],
        user_id: int,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to approve a chat join request. The bot must be an administrator in the chat for this to work and must have the *can_invite_users* administrator right. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'approvechatjoinrequest', 'name': 'approveChatJoinRequest', 'description': 'Use this method to approve a chat join request. The bot must be an administrator in the chat for this to work and must have the can_invite_users administrator right. Returns True on success.', 'html_description': '<p>Use this method to approve a chat join request. The bot must be an administrator in the chat for this to work and must have the <em>can_invite_users</em> administrator right. Returns <em>True</em> on success.</p>', 'rst_description': 'Use this method to approve a chat join request. The bot must be an administrator in the chat for this to work and must have the *can_invite_users* administrator right. Returns :code:`True` on success.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': True, 'description': 'Unique identifier of the target user', 'html_description': '<td>Unique identifier of the target user</td>', 'rst_description': 'Unique identifier of the target user\n', 'name': 'user_id', 'parsed_type': {'type': 'std', 'name': 'int'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param user_id: Unique identifier of the target user
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = ApproveChatJoinRequest(
            chat_id=chat_id,
            user_id=user_id,
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
        Use this method to ban a user in a group, a supergroup or a channel. In the case of supergroups and channels, the user will not be able to return to the chat on their own using invite links, etc., unless `unbanned <https://core.telegram.org/bots/api#unbanchatmember>`_ first. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'banchatmember', 'name': 'banChatMember', 'description': 'Use this method to ban a user in a group, a supergroup or a channel. In the case of supergroups and channels, the user will not be able to return to the chat on their own using invite links, etc., unless unbanned first. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns True on success.', 'html_description': '<p>Use this method to ban a user in a group, a supergroup or a channel. In the case of supergroups and channels, the user will not be able to return to the chat on their own using invite links, etc., unless <a href="#unbanchatmember">unbanned</a> first. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns <em>True</em> on success.</p>', 'rst_description': 'Use this method to ban a user in a group, a supergroup or a channel. In the case of supergroups and channels, the user will not be able to return to the chat on their own using invite links, etc., unless `unbanned <https://core.telegram.org/bots/api#unbanchatmember>`_ first. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns :code:`True` on success.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target group or username of the target supergroup or channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target group or username of the target supergroup or channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target group or username of the target supergroup or channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': True, 'description': 'Unique identifier of the target user', 'html_description': '<td>Unique identifier of the target user</td>', 'rst_description': 'Unique identifier of the target user\n', 'name': 'user_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Integer', 'required': False, 'description': 'Date when the user will be unbanned, unix time. If user is banned for more than 366 days or less than 30 seconds from the current time they are considered to be banned forever. Applied for supergroups and channels only.', 'html_description': '<td>Date when the user will be unbanned, unix time. If user is banned for more than 366 days or less than 30 seconds from the current time they are considered to be banned forever. Applied for supergroups and channels only.</td>', 'rst_description': 'Date when the user will be unbanned, unix time. If user is banned for more than 366 days or less than 30 seconds from the current time they are considered to be banned forever. Applied for supergroups and channels only.\n', 'name': 'until_date', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'datetime.datetime'}, {'type': 'std', 'name': 'datetime.timedelta'}, {'type': 'std', 'name': 'int'}]}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True to delete all messages from the chat for the user that is being removed. If False, the user will be able to see messages in the group that were sent before the user was removed. Always True for supergroups and channels.', 'html_description': '<td>Pass <em>True</em> to delete all messages from the chat for the user that is being removed. If <em>False</em>, the user will be able to see messages in the group that were sent before the user was removed. Always <em>True</em> for supergroups and channels.</td>', 'rst_description': 'Pass :code:`True` to delete all messages from the chat for the user that is being removed. If :code:`False`, the user will be able to see messages in the group that were sent before the user was removed. Always :code:`True` for supergroups and channels.\n', 'name': 'revoke_messages', 'parsed_type': {'type': 'std', 'name': 'bool'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'In the case of supergroups and channels, the user will not be able to return to the chat on their own using invite links, etc. Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target group or username of the target supergroup or channel (in the format :code:`@channelusername`)
        :param user_id: Unique identifier of the target user
        :param until_date: Date when the user will be unbanned, unix time. If user is banned for more than 366 days or less than 30 seconds from the current time they are considered to be banned forever. Applied for supergroups and channels only.
        :param revoke_messages: Pass :code:`True` to delete all messages from the chat for the user that is being removed. If :code:`False`, the user will be able to see messages in the group that were sent before the user was removed. Always :code:`True` for supergroups and channels.
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = BanChatMember(
            chat_id=chat_id,
            user_id=user_id,
            until_date=until_date,
            revoke_messages=revoke_messages,
        )
        return await self(call, request_timeout=request_timeout)

    async def ban_chat_sender_chat(
        self,
        chat_id: Union[int, str],
        sender_chat_id: int,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to ban a channel chat in a supergroup or a channel. Until the chat is `unbanned <https://core.telegram.org/bots/api#unbanchatsenderchat>`_, the owner of the banned chat won't be able to send messages on behalf of **any of their channels**. The bot must be an administrator in the supergroup or channel for this to work and must have the appropriate administrator rights. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'banchatsenderchat', 'name': 'banChatSenderChat', 'description': "Use this method to ban a channel chat in a supergroup or a channel. Until the chat is unbanned, the owner of the banned chat won't be able to send messages on behalf of any of their channels. The bot must be an administrator in the supergroup or channel for this to work and must have the appropriate administrator rights. Returns True on success.", 'html_description': '<p>Use this method to ban a channel chat in a supergroup or a channel. Until the chat is <a href="#unbanchatsenderchat">unbanned</a>, the owner of the banned chat won\'t be able to send messages on behalf of <strong>any of their channels</strong>. The bot must be an administrator in the supergroup or channel for this to work and must have the appropriate administrator rights. Returns <em>True</em> on success.</p>', 'rst_description': "Use this method to ban a channel chat in a supergroup or a channel. Until the chat is `unbanned <https://core.telegram.org/bots/api#unbanchatsenderchat>`_, the owner of the banned chat won't be able to send messages on behalf of **any of their channels**. The bot must be an administrator in the supergroup or channel for this to work and must have the appropriate administrator rights. Returns :code:`True` on success.", 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': True, 'description': 'Unique identifier of the target sender chat', 'html_description': '<td>Unique identifier of the target sender chat</td>', 'rst_description': 'Unique identifier of the target sender chat\n', 'name': 'sender_chat_id', 'parsed_type': {'type': 'std', 'name': 'int'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param sender_chat_id: Unique identifier of the target sender chat
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = BanChatSenderChat(
            chat_id=chat_id,
            sender_chat_id=sender_chat_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def close(
        self,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to close the bot instance before moving it from one local server to another. You need to delete the webhook before calling this method to ensure that the bot isn't launched again after server restart. The method will return error 429 in the first 10 minutes after the bot is launched. Returns :code:`True` on success. Requires no parameters.

        Source: https://core.telegram.org/bots/api#{'anchor': 'close', 'name': 'close', 'description': "Use this method to close the bot instance before moving it from one local server to another. You need to delete the webhook before calling this method to ensure that the bot isn't launched again after server restart. The method will return error 429 in the first 10 minutes after the bot is launched. Returns True on success. Requires no parameters.", 'html_description': "<p>Use this method to close the bot instance before moving it from one local server to another. You need to delete the webhook before calling this method to ensure that the bot isn't launched again after server restart. The method will return error 429 in the first 10 minutes after the bot is launched. Returns <em>True</em> on success. Requires no parameters.</p>", 'rst_description': "Use this method to close the bot instance before moving it from one local server to another. You need to delete the webhook before calling this method to ensure that the bot isn't launched again after server restart. The method will return error 429 in the first 10 minutes after the bot is launched. Returns :code:`True` on success. Requires no parameters.", 'annotations': [], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'The method will return error 429 in the first 10 minutes after the bot is launched. Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param request_timeout: Request timeout
        :return: Requires no parameters.
        """

        call = Close()
        return await self(call, request_timeout=request_timeout)

    async def close_forum_topic(
        self,
        chat_id: Union[int, str],
        message_thread_id: int,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to close an open topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the *can_manage_topics* administrator rights, unless it is the creator of the topic. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'closeforumtopic', 'name': 'closeForumTopic', 'description': 'Use this method to close an open topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the can_manage_topics administrator rights, unless it is the creator of the topic. Returns True on success.', 'html_description': '<p>Use this method to close an open topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the <em>can_manage_topics</em> administrator rights, unless it is the creator of the topic. Returns <em>True</em> on success.</p>', 'rst_description': 'Use this method to close an open topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the *can_manage_topics* administrator rights, unless it is the creator of the topic. Returns :code:`True` on success.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target supergroup (in the format @supergroupusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target supergroup (in the format <code>@supergroupusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': True, 'description': 'Unique identifier for the target message thread of the forum topic', 'html_description': '<td>Unique identifier for the target message thread of the forum topic</td>', 'rst_description': 'Unique identifier for the target message thread of the forum topic\n', 'name': 'message_thread_id', 'parsed_type': {'type': 'std', 'name': 'int'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)
        :param message_thread_id: Unique identifier for the target message thread of the forum topic
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = CloseForumTopic(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def copy_message(
        self,
        chat_id: Union[int, str],
        from_chat_id: Union[int, str],
        message_id: int,
        message_thread_id: Optional[int] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET,
        caption_entities: Optional[List[MessageEntity]] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        request_timeout: Optional[int] = None,
    ) -> MessageId:
        """
        Use this method to copy messages of any kind. Service messages and invoice messages can't be copied. A quiz :class:`aiogram.methods.poll.Poll` can be copied only if the value of the field *correct_option_id* is known to the bot. The method is analogous to the method :class:`aiogram.methods.forward_message.ForwardMessage`, but the copied message doesn't have a link to the original message. Returns the :class:`aiogram.types.message_id.MessageId` of the sent message on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'copymessage', 'name': 'copyMessage', 'description': "Use this method to copy messages of any kind. Service messages and invoice messages can't be copied. A quiz poll can be copied only if the value of the field correct_option_id is known to the bot. The method is analogous to the method forwardMessage, but the copied message doesn't have a link to the original message. Returns the MessageId of the sent message on success.", 'html_description': '<p>Use this method to copy messages of any kind. Service messages and invoice messages can\'t be copied. A quiz <a href="#poll">poll</a> can be copied only if the value of the field <em>correct_option_id</em> is known to the bot. The method is analogous to the method <a href="#forwardmessage">forwardMessage</a>, but the copied message doesn\'t have a link to the original message. Returns the <a href="#messageid">MessageId</a> of the sent message on success.</p>', 'rst_description': "Use this method to copy messages of any kind. Service messages and invoice messages can't be copied. A quiz :class:`aiogram.methods.poll.Poll` can be copied only if the value of the field *correct_option_id* is known to the bot. The method is analogous to the method :class:`aiogram.methods.forward_message.ForwardMessage`, but the copied message doesn't have a link to the original message. Returns the :class:`aiogram.types.message_id.MessageId` of the sent message on success.", 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the chat where the original message was sent (or channel username in the format @channelusername)', 'html_description': '<td>Unique identifier for the chat where the original message was sent (or channel username in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the chat where the original message was sent (or channel username in the format :code:`@channelusername`)\n', 'name': 'from_chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': True, 'description': 'Message identifier in the chat specified in from_chat_id', 'html_description': '<td>Message identifier in the chat specified in <em>from_chat_id</em></td>', 'rst_description': 'Message identifier in the chat specified in *from_chat_id*\n', 'name': 'message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Integer', 'required': False, 'description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only', 'html_description': '<td>Unique identifier for the target message thread (topic) of the forum; for forum supergroups only</td>', 'rst_description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only\n', 'name': 'message_thread_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'String', 'required': False, 'description': 'New caption for media, 0-1024 characters after entities parsing. If not specified, the original caption is kept', 'html_description': '<td>New caption for media, 0-1024 characters after entities parsing. If not specified, the original caption is kept</td>', 'rst_description': 'New caption for media, 0-1024 characters after entities parsing. If not specified, the original caption is kept\n', 'name': 'caption', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': False, 'description': 'Mode for parsing entities in the new caption. See formatting options for more details.', 'html_description': '<td>Mode for parsing entities in the new caption. See <a href="#formatting-options">formatting options</a> for more details.</td>', 'rst_description': 'Mode for parsing entities in the new caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.\n', 'name': 'parse_mode', 'parsed_type': {'type': 'std', 'name': 'str'}, 'value': 'UNSET'}, {'type': 'Array of MessageEntity', 'required': False, 'description': 'A JSON-serialized list of special entities that appear in the new caption, which can be specified instead of parse_mode', 'html_description': '<td>A JSON-serialized list of special entities that appear in the new caption, which can be specified instead of <em>parse_mode</em></td>', 'rst_description': 'A JSON-serialized list of special entities that appear in the new caption, which can be specified instead of *parse_mode*\n', 'name': 'caption_entities', 'parsed_type': {'type': 'array', 'items': {'type': 'entity', 'references': {'category': 'types', 'name': 'MessageEntity'}}}}, {'type': 'Boolean', 'required': False, 'description': 'Sends the message silently. Users will receive a notification with no sound.', 'html_description': '<td>Sends the message <a href="https://telegram.org/blog/channels-2-0#silent-messages">silently</a>. Users will receive a notification with no sound.</td>', 'rst_description': 'Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.\n', 'name': 'disable_notification', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Protects the contents of the sent message from forwarding and saving', 'html_description': '<td>Protects the contents of the sent message from forwarding and saving</td>', 'rst_description': 'Protects the contents of the sent message from forwarding and saving\n', 'name': 'protect_content', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Integer', 'required': False, 'description': 'If the message is a reply, ID of the original message', 'html_description': '<td>If the message is a reply, ID of the original message</td>', 'rst_description': 'If the message is a reply, ID of the original message\n', 'name': 'reply_to_message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the message should be sent even if the specified replied-to message is not found', 'html_description': '<td>Pass <em>True</em> if the message should be sent even if the specified replied-to message is not found</td>', 'rst_description': 'Pass :code:`True` if the message should be sent even if the specified replied-to message is not found\n', 'name': 'allow_sending_without_reply', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply', 'required': False, 'description': 'Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.', 'html_description': '<td>Additional interface options. A JSON-serialized object for an <a href="/bots/features#inline-keyboards">inline keyboard</a>, <a href="/bots/features#keyboards">custom reply keyboard</a>, instructions to remove reply keyboard or to force a reply from the user.</td>', 'rst_description': 'Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.\n', 'name': 'reply_markup', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InlineKeyboardMarkup'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ReplyKeyboardMarkup'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ReplyKeyboardRemove'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ForceReply'}}]}}], 'category': 'methods', 'returning': {'type': 'MessageId', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'MessageId'}}, 'description': 'Returns the MessageId of the sent message on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param from_chat_id: Unique identifier for the chat where the original message was sent (or channel username in the format :code:`@channelusername`)
        :param message_id: Message identifier in the chat specified in *from_chat_id*
        :param message_thread_id: Unique identifier for the target message thread (topic) of the forum; for forum supergroups only
        :param caption: New caption for media, 0-1024 characters after entities parsing. If not specified, the original caption is kept
        :param parse_mode: Mode for parsing entities in the new caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: A JSON-serialized list of special entities that appear in the new caption, which can be specified instead of *parse_mode*
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.
        :param request_timeout: Request timeout
        :return: Returns the :class:`aiogram.types.message_id.MessageId` of the sent message on success.
        """

        call = CopyMessage(
            chat_id=chat_id,
            from_chat_id=from_chat_id,
            message_id=message_id,
            message_thread_id=message_thread_id,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            disable_notification=disable_notification,
            protect_content=protect_content,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def create_chat_invite_link(
        self,
        chat_id: Union[int, str],
        name: Optional[str] = None,
        expire_date: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None,
        member_limit: Optional[int] = None,
        creates_join_request: Optional[bool] = None,
        request_timeout: Optional[int] = None,
    ) -> ChatInviteLink:
        """
        Use this method to create an additional invite link for a chat. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. The link can be revoked using the method :class:`aiogram.methods.revoke_chat_invite_link.RevokeChatInviteLink`. Returns the new invite link as :class:`aiogram.types.chat_invite_link.ChatInviteLink` object.

        Source: https://core.telegram.org/bots/api#{'anchor': 'createchatinvitelink', 'name': 'createChatInviteLink', 'description': 'Use this method to create an additional invite link for a chat. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. The link can be revoked using the method revokeChatInviteLink. Returns the new invite link as ChatInviteLink object.', 'html_description': '<p>Use this method to create an additional invite link for a chat. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. The link can be revoked using the method <a href="#revokechatinvitelink">revokeChatInviteLink</a>. Returns the new invite link as <a href="#chatinvitelink">ChatInviteLink</a> object.</p>', 'rst_description': 'Use this method to create an additional invite link for a chat. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. The link can be revoked using the method :class:`aiogram.methods.revoke_chat_invite_link.RevokeChatInviteLink`. Returns the new invite link as :class:`aiogram.types.chat_invite_link.ChatInviteLink` object.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'String', 'required': False, 'description': 'Invite link name; 0-32 characters', 'html_description': '<td>Invite link name; 0-32 characters</td>', 'rst_description': 'Invite link name; 0-32 characters\n', 'name': 'name', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'Integer', 'required': False, 'description': 'Point in time (Unix timestamp) when the link will expire', 'html_description': '<td>Point in time (Unix timestamp) when the link will expire</td>', 'rst_description': 'Point in time (Unix timestamp) when the link will expire\n', 'name': 'expire_date', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'datetime.datetime'}, {'type': 'std', 'name': 'datetime.timedelta'}, {'type': 'std', 'name': 'int'}]}}, {'type': 'Integer', 'required': False, 'description': 'The maximum number of users that can be members of the chat simultaneously after joining the chat via this invite link; 1-99999', 'html_description': '<td>The maximum number of users that can be members of the chat simultaneously after joining the chat via this invite link; 1-99999</td>', 'rst_description': 'The maximum number of users that can be members of the chat simultaneously after joining the chat via this invite link; 1-99999\n', 'name': 'member_limit', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': "True, if users joining the chat via the link need to be approved by chat administrators. If True, member_limit can't be specified", 'html_description': "<td><em>True</em>, if users joining the chat via the link need to be approved by chat administrators. If <em>True</em>, <em>member_limit</em> can't be specified</td>", 'rst_description': ":code:`True`, if users joining the chat via the link need to be approved by chat administrators. If :code:`True`, *member_limit* can't be specified\n", 'name': 'creates_join_request', 'parsed_type': {'type': 'std', 'name': 'bool'}}], 'category': 'methods', 'returning': {'type': 'ChatInviteLink', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'ChatInviteLink'}}, 'description': 'Returns the new invite link as ChatInviteLink object.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param name: Invite link name; 0-32 characters
        :param expire_date: Point in time (Unix timestamp) when the link will expire
        :param member_limit: The maximum number of users that can be members of the chat simultaneously after joining the chat via this invite link; 1-99999
        :param creates_join_request: :code:`True`, if users joining the chat via the link need to be approved by chat administrators. If :code:`True`, *member_limit* can't be specified
        :param request_timeout: Request timeout
        :return: Returns the new invite link as :class:`aiogram.types.chat_invite_link.ChatInviteLink` object.
        """

        call = CreateChatInviteLink(
            chat_id=chat_id,
            name=name,
            expire_date=expire_date,
            member_limit=member_limit,
            creates_join_request=creates_join_request,
        )
        return await self(call, request_timeout=request_timeout)

    async def create_forum_topic(
        self,
        chat_id: Union[int, str],
        name: str,
        icon_color: Optional[int] = None,
        icon_custom_emoji_id: Optional[str] = None,
        request_timeout: Optional[int] = None,
    ) -> ForumTopic:
        """
        Use this method to create a topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the *can_manage_topics* administrator rights. Returns information about the created topic as a :class:`aiogram.types.forum_topic.ForumTopic` object.

        Source: https://core.telegram.org/bots/api#{'anchor': 'createforumtopic', 'name': 'createForumTopic', 'description': 'Use this method to create a topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the can_manage_topics administrator rights. Returns information about the created topic as a ForumTopic object.', 'html_description': '<p>Use this method to create a topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the <em>can_manage_topics</em> administrator rights. Returns information about the created topic as a <a href="#forumtopic">ForumTopic</a> object.</p>', 'rst_description': 'Use this method to create a topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the *can_manage_topics* administrator rights. Returns information about the created topic as a :class:`aiogram.types.forum_topic.ForumTopic` object.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target supergroup (in the format @supergroupusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target supergroup (in the format <code>@supergroupusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'String', 'required': True, 'description': 'Topic name, 1-128 characters', 'html_description': '<td>Topic name, 1-128 characters</td>', 'rst_description': 'Topic name, 1-128 characters\n', 'name': 'name', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'Integer', 'required': False, 'description': 'Color of the topic icon in RGB format. Currently, must be one of 7322096 (0x6FB9F0), 16766590 (0xFFD67E), 13338331 (0xCB86DB), 9367192 (0x8EEE98), 16749490 (0xFF93B2), or 16478047 (0xFB6F5F)', 'html_description': '<td>Color of the topic icon in RGB format. Currently, must be one of 7322096 (0x6FB9F0), 16766590 (0xFFD67E), 13338331 (0xCB86DB), 9367192 (0x8EEE98), 16749490 (0xFF93B2), or 16478047 (0xFB6F5F)</td>', 'rst_description': 'Color of the topic icon in RGB format. Currently, must be one of 7322096 (0x6FB9F0), 16766590 (0xFFD67E), 13338331 (0xCB86DB), 9367192 (0x8EEE98), 16749490 (0xFF93B2), or 16478047 (0xFB6F5F)\n', 'name': 'icon_color', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'String', 'required': False, 'description': 'Unique identifier of the custom emoji shown as the topic icon. Use getForumTopicIconStickers to get all allowed custom emoji identifiers.', 'html_description': '<td>Unique identifier of the custom emoji shown as the topic icon. Use <a href="#getforumtopiciconstickers">getForumTopicIconStickers</a> to get all allowed custom emoji identifiers.</td>', 'rst_description': 'Unique identifier of the custom emoji shown as the topic icon. Use :class:`aiogram.methods.get_forum_topic_icon_stickers.GetForumTopicIconStickers` to get all allowed custom emoji identifiers.\n', 'name': 'icon_custom_emoji_id', 'parsed_type': {'type': 'std', 'name': 'str'}}], 'category': 'methods', 'returning': {'type': 'ForumTopic', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'ForumTopic'}}, 'description': 'Returns information about the created topic as a ForumTopic object.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)
        :param name: Topic name, 1-128 characters
        :param icon_color: Color of the topic icon in RGB format. Currently, must be one of 7322096 (0x6FB9F0), 16766590 (0xFFD67E), 13338331 (0xCB86DB), 9367192 (0x8EEE98), 16749490 (0xFF93B2), or 16478047 (0xFB6F5F)
        :param icon_custom_emoji_id: Unique identifier of the custom emoji shown as the topic icon. Use :class:`aiogram.methods.get_forum_topic_icon_stickers.GetForumTopicIconStickers` to get all allowed custom emoji identifiers.
        :param request_timeout: Request timeout
        :return: Returns information about the created topic as a :class:`aiogram.types.forum_topic.ForumTopic` object.
        """

        call = CreateForumTopic(
            chat_id=chat_id,
            name=name,
            icon_color=icon_color,
            icon_custom_emoji_id=icon_custom_emoji_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def create_invoice_link(
        self,
        title: str,
        description: str,
        payload: str,
        provider_token: str,
        currency: str,
        prices: List[LabeledPrice],
        max_tip_amount: Optional[int] = None,
        suggested_tip_amounts: Optional[List[int]] = None,
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
        request_timeout: Optional[int] = None,
    ) -> str:
        """
        Use this method to create a link for an invoice. Returns the created invoice link as *String* on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'createinvoicelink', 'name': 'createInvoiceLink', 'description': 'Use this method to create a link for an invoice. Returns the created invoice link as String on success.', 'html_description': '<p>Use this method to create a link for an invoice. Returns the created invoice link as <em>String</em> on success.</p>', 'rst_description': 'Use this method to create a link for an invoice. Returns the created invoice link as *String* on success.', 'annotations': [{'type': 'String', 'required': True, 'description': 'Product name, 1-32 characters', 'html_description': '<td>Product name, 1-32 characters</td>', 'rst_description': 'Product name, 1-32 characters\n', 'name': 'title', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': True, 'description': 'Product description, 1-255 characters', 'html_description': '<td>Product description, 1-255 characters</td>', 'rst_description': 'Product description, 1-255 characters\n', 'name': 'description', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': True, 'description': 'Bot-defined invoice payload, 1-128 bytes. This will not be displayed to the user, use for your internal processes.', 'html_description': '<td>Bot-defined invoice payload, 1-128 bytes. This will not be displayed to the user, use for your internal processes.</td>', 'rst_description': 'Bot-defined invoice payload, 1-128 bytes. This will not be displayed to the user, use for your internal processes.\n', 'name': 'payload', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': True, 'description': 'Payment provider token, obtained via BotFather', 'html_description': '<td>Payment provider token, obtained via <a href="https://t.me/botfather">BotFather</a></td>', 'rst_description': 'Payment provider token, obtained via `BotFather <https://t.me/botfather>`_\n', 'name': 'provider_token', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': True, 'description': 'Three-letter ISO 4217 currency code, see more on currencies', 'html_description': '<td>Three-letter ISO 4217 currency code, see <a href="/bots/payments#supported-currencies">more on currencies</a></td>', 'rst_description': 'Three-letter ISO 4217 currency code, see `more on currencies <https://core.telegram.org/bots/payments#supported-currencies>`_\n', 'name': 'currency', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'Array of LabeledPrice', 'required': True, 'description': 'Price breakdown, a JSON-serialized list of components (e.g. product price, tax, discount, delivery cost, delivery tax, bonus, etc.)', 'html_description': '<td>Price breakdown, a JSON-serialized list of components (e.g. product price, tax, discount, delivery cost, delivery tax, bonus, etc.)</td>', 'rst_description': 'Price breakdown, a JSON-serialized list of components (e.g. product price, tax, discount, delivery cost, delivery tax, bonus, etc.)\n', 'name': 'prices', 'parsed_type': {'type': 'array', 'items': {'type': 'entity', 'references': {'category': 'types', 'name': 'LabeledPrice'}}}}, {'type': 'Integer', 'required': False, 'description': 'The maximum accepted amount for tips in the smallest units of the currency (integer, not float/double). For example, for a maximum tip of US$ 1.45 pass max_tip_amount = 145. See the exp parameter in currencies.json, it shows the number of digits past the decimal point for each currency (2 for the majority of currencies). Defaults to 0', 'html_description': '<td>The maximum accepted amount for tips in the <em>smallest units</em> of the currency (integer, <strong>not</strong> float/double). For example, for a maximum tip of <code>US$ 1.45</code> pass <code>max_tip_amount = 145</code>. See the <em>exp</em> parameter in <a href="/bots/payments/currencies.json">currencies.json</a>, it shows the number of digits past the decimal point for each currency (2 for the majority of currencies). Defaults to 0</td>', 'rst_description': 'The maximum accepted amount for tips in the *smallest units* of the currency (integer, **not** float/double). For example, for a maximum tip of :code:`US$ 1.45` pass :code:`max_tip_amount = 145`. See the *exp* parameter in `currencies.json <https://core.telegram.org/bots/payments/currencies.json>`_, it shows the number of digits past the decimal point for each currency (2 for the majority of currencies). Defaults to 0\n', 'name': 'max_tip_amount', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Array of Integer', 'required': False, 'description': 'A JSON-serialized array of suggested amounts of tips in the smallest units of the currency (integer, not float/double). At most 4 suggested tip amounts can be specified. The suggested tip amounts must be positive, passed in a strictly increased order and must not exceed max_tip_amount.', 'html_description': '<td>A JSON-serialized array of suggested amounts of tips in the <em>smallest units</em> of the currency (integer, <strong>not</strong> float/double). At most 4 suggested tip amounts can be specified. The suggested tip amounts must be positive, passed in a strictly increased order and must not exceed <em>max_tip_amount</em>.</td>', 'rst_description': 'A JSON-serialized array of suggested amounts of tips in the *smallest units* of the currency (integer, **not** float/double). At most 4 suggested tip amounts can be specified. The suggested tip amounts must be positive, passed in a strictly increased order and must not exceed *max_tip_amount*.\n', 'name': 'suggested_tip_amounts', 'parsed_type': {'type': 'array', 'items': {'type': 'std', 'name': 'int'}}}, {'type': 'String', 'required': False, 'description': 'JSON-serialized data about the invoice, which will be shared with the payment provider. A detailed description of required fields should be provided by the payment provider.', 'html_description': '<td>JSON-serialized data about the invoice, which will be shared with the payment provider. A detailed description of required fields should be provided by the payment provider.</td>', 'rst_description': 'JSON-serialized data about the invoice, which will be shared with the payment provider. A detailed description of required fields should be provided by the payment provider.\n', 'name': 'provider_data', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': False, 'description': 'URL of the product photo for the invoice. Can be a photo of the goods or a marketing image for a service.', 'html_description': '<td>URL of the product photo for the invoice. Can be a photo of the goods or a marketing image for a service.</td>', 'rst_description': 'URL of the product photo for the invoice. Can be a photo of the goods or a marketing image for a service.\n', 'name': 'photo_url', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'Integer', 'required': False, 'description': 'Photo size in bytes', 'html_description': '<td>Photo size in bytes</td>', 'rst_description': 'Photo size in bytes\n', 'name': 'photo_size', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Integer', 'required': False, 'description': 'Photo width', 'html_description': '<td>Photo width</td>', 'rst_description': 'Photo width\n', 'name': 'photo_width', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Integer', 'required': False, 'description': 'Photo height', 'html_description': '<td>Photo height</td>', 'rst_description': 'Photo height\n', 'name': 'photo_height', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': "Pass True if you require the user's full name to complete the order", 'html_description': "<td>Pass <em>True</em> if you require the user's full name to complete the order</td>", 'rst_description': "Pass :code:`True` if you require the user's full name to complete the order\n", 'name': 'need_name', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': "Pass True if you require the user's phone number to complete the order", 'html_description': "<td>Pass <em>True</em> if you require the user's phone number to complete the order</td>", 'rst_description': "Pass :code:`True` if you require the user's phone number to complete the order\n", 'name': 'need_phone_number', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': "Pass True if you require the user's email address to complete the order", 'html_description': "<td>Pass <em>True</em> if you require the user's email address to complete the order</td>", 'rst_description': "Pass :code:`True` if you require the user's email address to complete the order\n", 'name': 'need_email', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': "Pass True if you require the user's shipping address to complete the order", 'html_description': "<td>Pass <em>True</em> if you require the user's shipping address to complete the order</td>", 'rst_description': "Pass :code:`True` if you require the user's shipping address to complete the order\n", 'name': 'need_shipping_address', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': "Pass True if the user's phone number should be sent to the provider", 'html_description': "<td>Pass <em>True</em> if the user's phone number should be sent to the provider</td>", 'rst_description': "Pass :code:`True` if the user's phone number should be sent to the provider\n", 'name': 'send_phone_number_to_provider', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': "Pass True if the user's email address should be sent to the provider", 'html_description': "<td>Pass <em>True</em> if the user's email address should be sent to the provider</td>", 'rst_description': "Pass :code:`True` if the user's email address should be sent to the provider\n", 'name': 'send_email_to_provider', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the final price depends on the shipping method', 'html_description': '<td>Pass <em>True</em> if the final price depends on the shipping method</td>', 'rst_description': 'Pass :code:`True` if the final price depends on the shipping method\n', 'name': 'is_flexible', 'parsed_type': {'type': 'std', 'name': 'bool'}}], 'category': 'methods', 'returning': {'type': 'String', 'parsed_type': {'type': 'std', 'name': 'str'}, 'description': 'Returns the created invoice link as String on success.'}, 'bases': ['TelegramMethod']}

        :param title: Product name, 1-32 characters
        :param description: Product description, 1-255 characters
        :param payload: Bot-defined invoice payload, 1-128 bytes. This will not be displayed to the user, use for your internal processes.
        :param provider_token: Payment provider token, obtained via `BotFather <https://t.me/botfather>`_
        :param currency: Three-letter ISO 4217 currency code, see `more on currencies <https://core.telegram.org/bots/payments#supported-currencies>`_
        :param prices: Price breakdown, a JSON-serialized list of components (e.g. product price, tax, discount, delivery cost, delivery tax, bonus, etc.)
        :param max_tip_amount: The maximum accepted amount for tips in the *smallest units* of the currency (integer, **not** float/double). For example, for a maximum tip of :code:`US$ 1.45` pass :code:`max_tip_amount = 145`. See the *exp* parameter in `currencies.json <https://core.telegram.org/bots/payments/currencies.json>`_, it shows the number of digits past the decimal point for each currency (2 for the majority of currencies). Defaults to 0
        :param suggested_tip_amounts: A JSON-serialized array of suggested amounts of tips in the *smallest units* of the currency (integer, **not** float/double). At most 4 suggested tip amounts can be specified. The suggested tip amounts must be positive, passed in a strictly increased order and must not exceed *max_tip_amount*.
        :param provider_data: JSON-serialized data about the invoice, which will be shared with the payment provider. A detailed description of required fields should be provided by the payment provider.
        :param photo_url: URL of the product photo for the invoice. Can be a photo of the goods or a marketing image for a service.
        :param photo_size: Photo size in bytes
        :param photo_width: Photo width
        :param photo_height: Photo height
        :param need_name: Pass :code:`True` if you require the user's full name to complete the order
        :param need_phone_number: Pass :code:`True` if you require the user's phone number to complete the order
        :param need_email: Pass :code:`True` if you require the user's email address to complete the order
        :param need_shipping_address: Pass :code:`True` if you require the user's shipping address to complete the order
        :param send_phone_number_to_provider: Pass :code:`True` if the user's phone number should be sent to the provider
        :param send_email_to_provider: Pass :code:`True` if the user's email address should be sent to the provider
        :param is_flexible: Pass :code:`True` if the final price depends on the shipping method
        :param request_timeout: Request timeout
        :return: Returns the created invoice link as *String* on success.
        """

        call = CreateInvoiceLink(
            title=title,
            description=description,
            payload=payload,
            provider_token=provider_token,
            currency=currency,
            prices=prices,
            max_tip_amount=max_tip_amount,
            suggested_tip_amounts=suggested_tip_amounts,
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
        webm_sticker: Optional[InputFile] = None,
        sticker_type: Optional[str] = None,
        mask_position: Optional[MaskPosition] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to create a new sticker set owned by a user. The bot will be able to edit the sticker set thus created. You **must** use exactly one of the fields *png_sticker*, *tgs_sticker*, or *webm_sticker*. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'createnewstickerset', 'name': 'createNewStickerSet', 'description': 'Use this method to create a new sticker set owned by a user. The bot will be able to edit the sticker set thus created. You must use exactly one of the fields png_sticker, tgs_sticker, or webm_sticker. Returns True on success.', 'html_description': '<p>Use this method to create a new sticker set owned by a user. The bot will be able to edit the sticker set thus created. You <strong>must</strong> use exactly one of the fields <em>png_sticker</em>, <em>tgs_sticker</em>, or <em>webm_sticker</em>. Returns <em>True</em> on success.</p>', 'rst_description': 'Use this method to create a new sticker set owned by a user. The bot will be able to edit the sticker set thus created. You **must** use exactly one of the fields *png_sticker*, *tgs_sticker*, or *webm_sticker*. Returns :code:`True` on success.', 'annotations': [{'type': 'Integer', 'required': True, 'description': 'User identifier of created sticker set owner', 'html_description': '<td>User identifier of created sticker set owner</td>', 'rst_description': 'User identifier of created sticker set owner\n', 'name': 'user_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'String', 'required': True, 'description': 'Short name of sticker set, to be used in t.me/addstickers/ URLs (e.g., animals). Can contain only English letters, digits and underscores. Must begin with a letter, can\'t contain consecutive underscores and must end in "_by_<bot_username>". <bot_username> is case insensitive. 1-64 characters.', 'html_description': '<td>Short name of sticker set, to be used in <code>t.me/addstickers/</code> URLs (e.g., <em>animals</em>). Can contain only English letters, digits and underscores. Must begin with a letter, can\'t contain consecutive underscores and must end in <code>"_by_&lt;bot_username&gt;"</code>. <code>&lt;bot_username&gt;</code> is case insensitive. 1-64 characters.</td>', 'rst_description': 'Short name of sticker set, to be used in :code:`t.me/addstickers/` URLs (e.g., *animals*). Can contain only English letters, digits and underscores. Must begin with a letter, can\'t contain consecutive underscores and must end in :code:`"_by_<bot_username>"`. :code:`<bot_username>` is case insensitive. 1-64 characters.\n', 'name': 'name', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': True, 'description': 'Sticker set title, 1-64 characters', 'html_description': '<td>Sticker set title, 1-64 characters</td>', 'rst_description': 'Sticker set title, 1-64 characters\n', 'name': 'title', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': True, 'description': 'One or more emoji corresponding to the sticker', 'html_description': '<td>One or more emoji corresponding to the sticker</td>', 'rst_description': 'One or more emoji corresponding to the sticker\n', 'name': 'emojis', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'InputFile or String', 'required': False, 'description': 'PNG image with the sticker, must be up to 512 kilobytes in size, dimensions must not exceed 512px, and either width or height must be exactly 512px. Pass a file_id as a String to send a file that already exists on the Telegram servers, pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. More information on Sending Files', 'html_description': '<td><strong>PNG</strong> image with the sticker, must be up to 512 kilobytes in size, dimensions must not exceed 512px, and either width or height must be exactly 512px. Pass a <em>file_id</em> as a String to send a file that already exists on the Telegram servers, pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. <a href="#sending-files">More information on Sending Files &#187;</a></td>', 'rst_description': '**PNG** image with the sticker, must be up to 512 kilobytes in size, dimensions must not exceed 512px, and either width or height must be exactly 512px. Pass a *file_id* as a String to send a file that already exists on the Telegram servers, pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`\n', 'name': 'png_sticker', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InputFile'}}, {'type': 'std', 'name': 'str'}]}}, {'type': 'InputFile', 'required': False, 'description': 'TGS animation with the sticker, uploaded using multipart/form-data. See https://core.telegram.org/stickers#animated-sticker-requirements for technical requirements', 'html_description': '<td><strong>TGS</strong> animation with the sticker, uploaded using multipart/form-data. See <a href="/stickers#animated-sticker-requirements"/><a href="https://core.telegram.org/stickers#animated-sticker-requirements">https://core.telegram.org/stickers#animated-sticker-requirements</a> for technical requirements</td>', 'rst_description': '**TGS** animation with the sticker, uploaded using multipart/form-data. See `https://core.telegram.org/stickers#animated-sticker-requirements <https://core.telegram.org/stickers#animated-sticker-requirements>`_`https://core.telegram.org/stickers#animated-sticker-requirements <https://core.telegram.org/stickers#animated-sticker-requirements>`_ for technical requirements\n', 'name': 'tgs_sticker', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'InputFile'}}}, {'type': 'InputFile', 'required': False, 'description': 'WEBM video with the sticker, uploaded using multipart/form-data. See https://core.telegram.org/stickers#video-sticker-requirements for technical requirements', 'html_description': '<td><strong>WEBM</strong> video with the sticker, uploaded using multipart/form-data. See <a href="/stickers#video-sticker-requirements"/><a href="https://core.telegram.org/stickers#video-sticker-requirements">https://core.telegram.org/stickers#video-sticker-requirements</a> for technical requirements</td>', 'rst_description': '**WEBM** video with the sticker, uploaded using multipart/form-data. See `https://core.telegram.org/stickers#video-sticker-requirements <https://core.telegram.org/stickers#video-sticker-requirements>`_`https://core.telegram.org/stickers#video-sticker-requirements <https://core.telegram.org/stickers#video-sticker-requirements>`_ for technical requirements\n', 'name': 'webm_sticker', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'InputFile'}}}, {'type': 'String', 'required': False, 'description': "Type of stickers in the set, pass 'regular' or 'mask'. Custom emoji sticker sets can't be created via the Bot API at the moment. By default, a regular sticker set is created.", 'html_description': "<td>Type of stickers in the set, pass &#8220;regular&#8221; or &#8220;mask&#8221;. Custom emoji sticker sets can't be created via the Bot API at the moment. By default, a regular sticker set is created.</td>", 'rst_description': "Type of stickers in the set, pass 'regular' or 'mask'. Custom emoji sticker sets can't be created via the Bot API at the moment. By default, a regular sticker set is created.\n", 'name': 'sticker_type', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'MaskPosition', 'required': False, 'description': 'A JSON-serialized object for position where the mask should be placed on faces', 'html_description': '<td>A JSON-serialized object for position where the mask should be placed on faces</td>', 'rst_description': 'A JSON-serialized object for position where the mask should be placed on faces\n', 'name': 'mask_position', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'MaskPosition'}}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param user_id: User identifier of created sticker set owner
        :param name: Short name of sticker set, to be used in :code:`t.me/addstickers/` URLs (e.g., *animals*). Can contain only English letters, digits and underscores. Must begin with a letter, can't contain consecutive underscores and must end in :code:`"_by_<bot_username>"`. :code:`<bot_username>` is case insensitive. 1-64 characters.
        :param title: Sticker set title, 1-64 characters
        :param emojis: One or more emoji corresponding to the sticker
        :param png_sticker: **PNG** image with the sticker, must be up to 512 kilobytes in size, dimensions must not exceed 512px, and either width or height must be exactly 512px. Pass a *file_id* as a String to send a file that already exists on the Telegram servers, pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`
        :param tgs_sticker: **TGS** animation with the sticker, uploaded using multipart/form-data. See `https://core.telegram.org/stickers#animated-sticker-requirements <https://core.telegram.org/stickers#animated-sticker-requirements>`_`https://core.telegram.org/stickers#animated-sticker-requirements <https://core.telegram.org/stickers#animated-sticker-requirements>`_ for technical requirements
        :param webm_sticker: **WEBM** video with the sticker, uploaded using multipart/form-data. See `https://core.telegram.org/stickers#video-sticker-requirements <https://core.telegram.org/stickers#video-sticker-requirements>`_`https://core.telegram.org/stickers#video-sticker-requirements <https://core.telegram.org/stickers#video-sticker-requirements>`_ for technical requirements
        :param sticker_type: Type of stickers in the set, pass 'regular' or 'mask'. Custom emoji sticker sets can't be created via the Bot API at the moment. By default, a regular sticker set is created.
        :param mask_position: A JSON-serialized object for position where the mask should be placed on faces
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = CreateNewStickerSet(
            user_id=user_id,
            name=name,
            title=title,
            emojis=emojis,
            png_sticker=png_sticker,
            tgs_sticker=tgs_sticker,
            webm_sticker=webm_sticker,
            sticker_type=sticker_type,
            mask_position=mask_position,
        )
        return await self(call, request_timeout=request_timeout)

    async def decline_chat_join_request(
        self,
        chat_id: Union[int, str],
        user_id: int,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to decline a chat join request. The bot must be an administrator in the chat for this to work and must have the *can_invite_users* administrator right. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'declinechatjoinrequest', 'name': 'declineChatJoinRequest', 'description': 'Use this method to decline a chat join request. The bot must be an administrator in the chat for this to work and must have the can_invite_users administrator right. Returns True on success.', 'html_description': '<p>Use this method to decline a chat join request. The bot must be an administrator in the chat for this to work and must have the <em>can_invite_users</em> administrator right. Returns <em>True</em> on success.</p>', 'rst_description': 'Use this method to decline a chat join request. The bot must be an administrator in the chat for this to work and must have the *can_invite_users* administrator right. Returns :code:`True` on success.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': True, 'description': 'Unique identifier of the target user', 'html_description': '<td>Unique identifier of the target user</td>', 'rst_description': 'Unique identifier of the target user\n', 'name': 'user_id', 'parsed_type': {'type': 'std', 'name': 'int'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param user_id: Unique identifier of the target user
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = DeclineChatJoinRequest(
            chat_id=chat_id,
            user_id=user_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def delete_chat_photo(
        self,
        chat_id: Union[int, str],
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to delete a chat photo. Photos can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'deletechatphoto', 'name': 'deleteChatPhoto', 'description': "Use this method to delete a chat photo. Photos can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns True on success.", 'html_description': "<p>Use this method to delete a chat photo. Photos can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns <em>True</em> on success.</p>", 'rst_description': "Use this method to delete a chat photo. Photos can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns :code:`True` on success.", 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = DeleteChatPhoto(
            chat_id=chat_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def delete_chat_sticker_set(
        self,
        chat_id: Union[int, str],
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to delete a group sticker set from a supergroup. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Use the field *can_set_sticker_set* optionally returned in :class:`aiogram.methods.get_chat.GetChat` requests to check if the bot can use this method. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'deletechatstickerset', 'name': 'deleteChatStickerSet', 'description': 'Use this method to delete a group sticker set from a supergroup. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Use the field can_set_sticker_set optionally returned in getChat requests to check if the bot can use this method. Returns True on success.', 'html_description': '<p>Use this method to delete a group sticker set from a supergroup. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Use the field <em>can_set_sticker_set</em> optionally returned in <a href="#getchat">getChat</a> requests to check if the bot can use this method. Returns <em>True</em> on success.</p>', 'rst_description': 'Use this method to delete a group sticker set from a supergroup. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Use the field *can_set_sticker_set* optionally returned in :class:`aiogram.methods.get_chat.GetChat` requests to check if the bot can use this method. Returns :code:`True` on success.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target supergroup (in the format @supergroupusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target supergroup (in the format <code>@supergroupusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Use the field can_set_sticker_set optionally returned in getChat requests to check if the bot can use this method. Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = DeleteChatStickerSet(
            chat_id=chat_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def delete_forum_topic(
        self,
        chat_id: Union[int, str],
        message_thread_id: int,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to delete a forum topic along with all its messages in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the *can_delete_messages* administrator rights. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'deleteforumtopic', 'name': 'deleteForumTopic', 'description': 'Use this method to delete a forum topic along with all its messages in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the can_delete_messages administrator rights. Returns True on success.', 'html_description': '<p>Use this method to delete a forum topic along with all its messages in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the <em>can_delete_messages</em> administrator rights. Returns <em>True</em> on success.</p>', 'rst_description': 'Use this method to delete a forum topic along with all its messages in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the *can_delete_messages* administrator rights. Returns :code:`True` on success.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target supergroup (in the format @supergroupusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target supergroup (in the format <code>@supergroupusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': True, 'description': 'Unique identifier for the target message thread of the forum topic', 'html_description': '<td>Unique identifier for the target message thread of the forum topic</td>', 'rst_description': 'Unique identifier for the target message thread of the forum topic\n', 'name': 'message_thread_id', 'parsed_type': {'type': 'std', 'name': 'int'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)
        :param message_thread_id: Unique identifier for the target message thread of the forum topic
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = DeleteForumTopic(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
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

        - Service messages about a supergroup, channel, or forum topic creation can't be deleted.

        - A dice message in a private chat can only be deleted if it was sent more than 24 hours ago.

        - Bots can delete outgoing messages in private chats, groups, and supergroups.

        - Bots can delete incoming messages in private chats.

        - Bots granted *can_post_messages* permissions can delete outgoing messages in channels.

        - If the bot is an administrator of a group, it can delete any message there.

        - If the bot has *can_delete_messages* permission in a supergroup or a channel, it can delete any message there.

        Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'deletemessage', 'name': 'deleteMessage', 'description': "Use this method to delete a message, including service messages, with the following limitations:\n- A message can only be deleted if it was sent less than 48 hours ago.\n- Service messages about a supergroup, channel, or forum topic creation can't be deleted.\n- A dice message in a private chat can only be deleted if it was sent more than 24 hours ago.\n- Bots can delete outgoing messages in private chats, groups, and supergroups.\n- Bots can delete incoming messages in private chats.\n- Bots granted can_post_messages permissions can delete outgoing messages in channels.\n- If the bot is an administrator of a group, it can delete any message there.\n- If the bot has can_delete_messages permission in a supergroup or a channel, it can delete any message there.\nReturns True on success.", 'html_description': "<p>Use this method to delete a message, including service messages, with the following limitations:<br/>\n- A message can only be deleted if it was sent less than 48 hours ago.<br/>\n- Service messages about a supergroup, channel, or forum topic creation can't be deleted.<br/>\n- A dice message in a private chat can only be deleted if it was sent more than 24 hours ago.<br/>\n- Bots can delete outgoing messages in private chats, groups, and supergroups.<br/>\n- Bots can delete incoming messages in private chats.<br/>\n- Bots granted <em>can_post_messages</em> permissions can delete outgoing messages in channels.<br/>\n- If the bot is an administrator of a group, it can delete any message there.<br/>\n- If the bot has <em>can_delete_messages</em> permission in a supergroup or a channel, it can delete any message there.<br/>\nReturns <em>True</em> on success.</p>", 'rst_description': "Use this method to delete a message, including service messages, with the following limitations:\n\n- A message can only be deleted if it was sent less than 48 hours ago.\n\n- Service messages about a supergroup, channel, or forum topic creation can't be deleted.\n\n- A dice message in a private chat can only be deleted if it was sent more than 24 hours ago.\n\n- Bots can delete outgoing messages in private chats, groups, and supergroups.\n\n- Bots can delete incoming messages in private chats.\n\n- Bots granted *can_post_messages* permissions can delete outgoing messages in channels.\n\n- If the bot is an administrator of a group, it can delete any message there.\n\n- If the bot has *can_delete_messages* permission in a supergroup or a channel, it can delete any message there.\n\nReturns :code:`True` on success.", 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': True, 'description': 'Identifier of the message to delete', 'html_description': '<td>Identifier of the message to delete</td>', 'rst_description': 'Identifier of the message to delete\n', 'name': 'message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param message_id: Identifier of the message to delete
        :param request_timeout: Request timeout
        :return: Use this method to delete a message, including service messages, with the following limitations:
        """

        call = DeleteMessage(
            chat_id=chat_id,
            message_id=message_id,
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

        Source: https://core.telegram.org/bots/api#{'anchor': 'deletemycommands', 'name': 'deleteMyCommands', 'description': "Use this method to delete the list of the bot's commands for the given scope and user language. After deletion, higher level commands will be shown to affected users. Returns True on success.", 'html_description': '<p>Use this method to delete the list of the bot\'s commands for the given scope and user language. After deletion, <a href="#determining-list-of-commands">higher level commands</a> will be shown to affected users. Returns <em>True</em> on success.</p>', 'rst_description': "Use this method to delete the list of the bot's commands for the given scope and user language. After deletion, `higher level commands <https://core.telegram.org/bots/api#determining-list-of-commands>`_ will be shown to affected users. Returns :code:`True` on success.", 'annotations': [{'type': 'BotCommandScope', 'required': False, 'description': 'A JSON-serialized object, describing scope of users for which the commands are relevant. Defaults to BotCommandScopeDefault.', 'html_description': '<td>A JSON-serialized object, describing scope of users for which the commands are relevant. Defaults to <a href="#botcommandscopedefault">BotCommandScopeDefault</a>.</td>', 'rst_description': 'A JSON-serialized object, describing scope of users for which the commands are relevant. Defaults to :class:`aiogram.types.bot_command_scope_default.BotCommandScopeDefault`.\n', 'name': 'scope', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'BotCommandScope'}}}, {'type': 'String', 'required': False, 'description': 'A two-letter ISO 639-1 language code. If empty, commands will be applied to all users from the given scope, for whose language there are no dedicated commands', 'html_description': '<td>A two-letter ISO 639-1 language code. If empty, commands will be applied to all users from the given scope, for whose language there are no dedicated commands</td>', 'rst_description': 'A two-letter ISO 639-1 language code. If empty, commands will be applied to all users from the given scope, for whose language there are no dedicated commands\n', 'name': 'language_code', 'parsed_type': {'type': 'std', 'name': 'str'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param scope: A JSON-serialized object, describing scope of users for which the commands are relevant. Defaults to :class:`aiogram.types.bot_command_scope_default.BotCommandScopeDefault`.
        :param language_code: A two-letter ISO 639-1 language code. If empty, commands will be applied to all users from the given scope, for whose language there are no dedicated commands
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = DeleteMyCommands(
            scope=scope,
            language_code=language_code,
        )
        return await self(call, request_timeout=request_timeout)

    async def delete_sticker_from_set(
        self,
        sticker: str,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to delete a sticker from a set created by the bot. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'deletestickerfromset', 'name': 'deleteStickerFromSet', 'description': 'Use this method to delete a sticker from a set created by the bot. Returns True on success.', 'html_description': '<p>Use this method to delete a sticker from a set created by the bot. Returns <em>True</em> on success.</p>', 'rst_description': 'Use this method to delete a sticker from a set created by the bot. Returns :code:`True` on success.', 'annotations': [{'type': 'String', 'required': True, 'description': 'File identifier of the sticker', 'html_description': '<td>File identifier of the sticker</td>', 'rst_description': 'File identifier of the sticker\n', 'name': 'sticker', 'parsed_type': {'type': 'std', 'name': 'str'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param sticker: File identifier of the sticker
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = DeleteStickerFromSet(
            sticker=sticker,
        )
        return await self(call, request_timeout=request_timeout)

    async def delete_webhook(
        self,
        drop_pending_updates: Optional[bool] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to remove webhook integration if you decide to switch back to :class:`aiogram.methods.get_updates.GetUpdates`. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'deletewebhook', 'name': 'deleteWebhook', 'description': 'Use this method to remove webhook integration if you decide to switch back to getUpdates. Returns True on success.', 'html_description': '<p>Use this method to remove webhook integration if you decide to switch back to <a href="#getupdates">getUpdates</a>. Returns <em>True</em> on success.</p>', 'rst_description': 'Use this method to remove webhook integration if you decide to switch back to :class:`aiogram.methods.get_updates.GetUpdates`. Returns :code:`True` on success.', 'annotations': [{'type': 'Boolean', 'required': False, 'description': 'Pass True to drop all pending updates', 'html_description': '<td>Pass <em>True</em> to drop all pending updates</td>', 'rst_description': 'Pass :code:`True` to drop all pending updates\n', 'name': 'drop_pending_updates', 'parsed_type': {'type': 'std', 'name': 'bool'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param drop_pending_updates: Pass :code:`True` to drop all pending updates
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = DeleteWebhook(
            drop_pending_updates=drop_pending_updates,
        )
        return await self(call, request_timeout=request_timeout)

    async def edit_chat_invite_link(
        self,
        chat_id: Union[int, str],
        invite_link: str,
        name: Optional[str] = None,
        expire_date: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None,
        member_limit: Optional[int] = None,
        creates_join_request: Optional[bool] = None,
        request_timeout: Optional[int] = None,
    ) -> ChatInviteLink:
        """
        Use this method to edit a non-primary invite link created by the bot. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns the edited invite link as a :class:`aiogram.types.chat_invite_link.ChatInviteLink` object.

        Source: https://core.telegram.org/bots/api#{'anchor': 'editchatinvitelink', 'name': 'editChatInviteLink', 'description': 'Use this method to edit a non-primary invite link created by the bot. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns the edited invite link as a ChatInviteLink object.', 'html_description': '<p>Use this method to edit a non-primary invite link created by the bot. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns the edited invite link as a <a href="#chatinvitelink">ChatInviteLink</a> object.</p>', 'rst_description': 'Use this method to edit a non-primary invite link created by the bot. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns the edited invite link as a :class:`aiogram.types.chat_invite_link.ChatInviteLink` object.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'String', 'required': True, 'description': 'The invite link to edit', 'html_description': '<td>The invite link to edit</td>', 'rst_description': 'The invite link to edit\n', 'name': 'invite_link', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': False, 'description': 'Invite link name; 0-32 characters', 'html_description': '<td>Invite link name; 0-32 characters</td>', 'rst_description': 'Invite link name; 0-32 characters\n', 'name': 'name', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'Integer', 'required': False, 'description': 'Point in time (Unix timestamp) when the link will expire', 'html_description': '<td>Point in time (Unix timestamp) when the link will expire</td>', 'rst_description': 'Point in time (Unix timestamp) when the link will expire\n', 'name': 'expire_date', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'datetime.datetime'}, {'type': 'std', 'name': 'datetime.timedelta'}, {'type': 'std', 'name': 'int'}]}}, {'type': 'Integer', 'required': False, 'description': 'The maximum number of users that can be members of the chat simultaneously after joining the chat via this invite link; 1-99999', 'html_description': '<td>The maximum number of users that can be members of the chat simultaneously after joining the chat via this invite link; 1-99999</td>', 'rst_description': 'The maximum number of users that can be members of the chat simultaneously after joining the chat via this invite link; 1-99999\n', 'name': 'member_limit', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': "True, if users joining the chat via the link need to be approved by chat administrators. If True, member_limit can't be specified", 'html_description': "<td><em>True</em>, if users joining the chat via the link need to be approved by chat administrators. If <em>True</em>, <em>member_limit</em> can't be specified</td>", 'rst_description': ":code:`True`, if users joining the chat via the link need to be approved by chat administrators. If :code:`True`, *member_limit* can't be specified\n", 'name': 'creates_join_request', 'parsed_type': {'type': 'std', 'name': 'bool'}}], 'category': 'methods', 'returning': {'type': 'ChatInviteLink', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'ChatInviteLink'}}, 'description': 'Returns the edited invite link as a ChatInviteLink object.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param invite_link: The invite link to edit
        :param name: Invite link name; 0-32 characters
        :param expire_date: Point in time (Unix timestamp) when the link will expire
        :param member_limit: The maximum number of users that can be members of the chat simultaneously after joining the chat via this invite link; 1-99999
        :param creates_join_request: :code:`True`, if users joining the chat via the link need to be approved by chat administrators. If :code:`True`, *member_limit* can't be specified
        :param request_timeout: Request timeout
        :return: Returns the edited invite link as a :class:`aiogram.types.chat_invite_link.ChatInviteLink` object.
        """

        call = EditChatInviteLink(
            chat_id=chat_id,
            invite_link=invite_link,
            name=name,
            expire_date=expire_date,
            member_limit=member_limit,
            creates_join_request=creates_join_request,
        )
        return await self(call, request_timeout=request_timeout)

    async def edit_forum_topic(
        self,
        chat_id: Union[int, str],
        message_thread_id: int,
        name: Optional[str] = None,
        icon_custom_emoji_id: Optional[str] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to edit name and icon of a topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have *can_manage_topics* administrator rights, unless it is the creator of the topic. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'editforumtopic', 'name': 'editForumTopic', 'description': 'Use this method to edit name and icon of a topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have can_manage_topics administrator rights, unless it is the creator of the topic. Returns True on success.', 'html_description': '<p>Use this method to edit name and icon of a topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have <em>can_manage_topics</em> administrator rights, unless it is the creator of the topic. Returns <em>True</em> on success.</p>', 'rst_description': 'Use this method to edit name and icon of a topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have *can_manage_topics* administrator rights, unless it is the creator of the topic. Returns :code:`True` on success.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target supergroup (in the format @supergroupusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target supergroup (in the format <code>@supergroupusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': True, 'description': 'Unique identifier for the target message thread of the forum topic', 'html_description': '<td>Unique identifier for the target message thread of the forum topic</td>', 'rst_description': 'Unique identifier for the target message thread of the forum topic\n', 'name': 'message_thread_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'String', 'required': False, 'description': 'New topic name, 0-128 characters. If not specified or empty, the current name of the topic will be kept', 'html_description': '<td>New topic name, 0-128 characters. If not specified or empty, the current name of the topic will be kept</td>', 'rst_description': 'New topic name, 0-128 characters. If not specified or empty, the current name of the topic will be kept\n', 'name': 'name', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': False, 'description': 'New unique identifier of the custom emoji shown as the topic icon. Use getForumTopicIconStickers to get all allowed custom emoji identifiers. Pass an empty string to remove the icon. If not specified, the current icon will be kept', 'html_description': '<td>New unique identifier of the custom emoji shown as the topic icon. Use <a href="#getforumtopiciconstickers">getForumTopicIconStickers</a> to get all allowed custom emoji identifiers. Pass an empty string to remove the icon. If not specified, the current icon will be kept</td>', 'rst_description': 'New unique identifier of the custom emoji shown as the topic icon. Use :class:`aiogram.methods.get_forum_topic_icon_stickers.GetForumTopicIconStickers` to get all allowed custom emoji identifiers. Pass an empty string to remove the icon. If not specified, the current icon will be kept\n', 'name': 'icon_custom_emoji_id', 'parsed_type': {'type': 'std', 'name': 'str'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)
        :param message_thread_id: Unique identifier for the target message thread of the forum topic
        :param name: New topic name, 0-128 characters. If not specified or empty, the current name of the topic will be kept
        :param icon_custom_emoji_id: New unique identifier of the custom emoji shown as the topic icon. Use :class:`aiogram.methods.get_forum_topic_icon_stickers.GetForumTopicIconStickers` to get all allowed custom emoji identifiers. Pass an empty string to remove the icon. If not specified, the current icon will be kept
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = EditForumTopic(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            name=name,
            icon_custom_emoji_id=icon_custom_emoji_id,
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

        Source: https://core.telegram.org/bots/api#{'anchor': 'editmessagecaption', 'name': 'editMessageCaption', 'description': 'Use this method to edit captions of messages. On success, if the edited message is not an inline message, the edited Message is returned, otherwise True is returned.', 'html_description': '<p>Use this method to edit captions of messages. On success, if the edited message is not an inline message, the edited <a href="#message">Message</a> is returned, otherwise <em>True</em> is returned.</p>', 'rst_description': 'Use this method to edit captions of messages. On success, if the edited message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned.', 'annotations': [{'type': 'Integer or String', 'required': False, 'description': 'Required if inline_message_id is not specified. Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Required if <em>inline_message_id</em> is not specified. Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': False, 'description': 'Required if inline_message_id is not specified. Identifier of the message to edit', 'html_description': '<td>Required if <em>inline_message_id</em> is not specified. Identifier of the message to edit</td>', 'rst_description': 'Required if *inline_message_id* is not specified. Identifier of the message to edit\n', 'name': 'message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'String', 'required': False, 'description': 'Required if chat_id and message_id are not specified. Identifier of the inline message', 'html_description': '<td>Required if <em>chat_id</em> and <em>message_id</em> are not specified. Identifier of the inline message</td>', 'rst_description': 'Required if *chat_id* and *message_id* are not specified. Identifier of the inline message\n', 'name': 'inline_message_id', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': False, 'description': 'New caption of the message, 0-1024 characters after entities parsing', 'html_description': '<td>New caption of the message, 0-1024 characters after entities parsing</td>', 'rst_description': 'New caption of the message, 0-1024 characters after entities parsing\n', 'name': 'caption', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': False, 'description': 'Mode for parsing entities in the message caption. See formatting options for more details.', 'html_description': '<td>Mode for parsing entities in the message caption. See <a href="#formatting-options">formatting options</a> for more details.</td>', 'rst_description': 'Mode for parsing entities in the message caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.\n', 'name': 'parse_mode', 'parsed_type': {'type': 'std', 'name': 'str'}, 'value': 'UNSET'}, {'type': 'Array of MessageEntity', 'required': False, 'description': 'A JSON-serialized list of special entities that appear in the caption, which can be specified instead of parse_mode', 'html_description': '<td>A JSON-serialized list of special entities that appear in the caption, which can be specified instead of <em>parse_mode</em></td>', 'rst_description': 'A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*\n', 'name': 'caption_entities', 'parsed_type': {'type': 'array', 'items': {'type': 'entity', 'references': {'category': 'types', 'name': 'MessageEntity'}}}}, {'type': 'InlineKeyboardMarkup', 'required': False, 'description': 'A JSON-serialized object for an inline keyboard.', 'html_description': '<td>A JSON-serialized object for an <a href="/bots/features#inline-keyboards">inline keyboard</a>.</td>', 'rst_description': 'A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_.\n', 'name': 'reply_markup', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'InlineKeyboardMarkup'}}}], 'category': 'methods', 'returning': {'type': 'Message or True', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'Message'}}, {'type': 'std', 'name': 'bool', 'value': True}]}, 'description': 'On success, if the edited message is not an inline message, the edited Message is returned, otherwise True is returned.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param message_id: Required if *inline_message_id* is not specified. Identifier of the message to edit
        :param inline_message_id: Required if *chat_id* and *message_id* are not specified. Identifier of the inline message
        :param caption: New caption of the message, 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the message caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*
        :param reply_markup: A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_.
        :param request_timeout: Request timeout
        :return: On success, if the edited message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned.
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

        Source: https://core.telegram.org/bots/api#{'anchor': 'editmessagelivelocation', 'name': 'editMessageLiveLocation', 'description': 'Use this method to edit live location messages. A location can be edited until its live_period expires or editing is explicitly disabled by a call to stopMessageLiveLocation. On success, if the edited message is not an inline message, the edited Message is returned, otherwise True is returned.', 'html_description': '<p>Use this method to edit live location messages. A location can be edited until its <em>live_period</em> expires or editing is explicitly disabled by a call to <a href="#stopmessagelivelocation">stopMessageLiveLocation</a>. On success, if the edited message is not an inline message, the edited <a href="#message">Message</a> is returned, otherwise <em>True</em> is returned.</p>', 'rst_description': 'Use this method to edit live location messages. A location can be edited until its *live_period* expires or editing is explicitly disabled by a call to :class:`aiogram.methods.stop_message_live_location.StopMessageLiveLocation`. On success, if the edited message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned.', 'annotations': [{'type': 'Float number', 'required': True, 'description': 'Latitude of new location', 'html_description': '<td>Latitude of new location</td>', 'rst_description': 'Latitude of new location\n', 'name': 'latitude', 'parsed_type': {'type': 'std', 'name': 'float'}}, {'type': 'Float number', 'required': True, 'description': 'Longitude of new location', 'html_description': '<td>Longitude of new location</td>', 'rst_description': 'Longitude of new location\n', 'name': 'longitude', 'parsed_type': {'type': 'std', 'name': 'float'}}, {'type': 'Integer or String', 'required': False, 'description': 'Required if inline_message_id is not specified. Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Required if <em>inline_message_id</em> is not specified. Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': False, 'description': 'Required if inline_message_id is not specified. Identifier of the message to edit', 'html_description': '<td>Required if <em>inline_message_id</em> is not specified. Identifier of the message to edit</td>', 'rst_description': 'Required if *inline_message_id* is not specified. Identifier of the message to edit\n', 'name': 'message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'String', 'required': False, 'description': 'Required if chat_id and message_id are not specified. Identifier of the inline message', 'html_description': '<td>Required if <em>chat_id</em> and <em>message_id</em> are not specified. Identifier of the inline message</td>', 'rst_description': 'Required if *chat_id* and *message_id* are not specified. Identifier of the inline message\n', 'name': 'inline_message_id', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'Float number', 'required': False, 'description': 'The radius of uncertainty for the location, measured in meters; 0-1500', 'html_description': '<td>The radius of uncertainty for the location, measured in meters; 0-1500</td>', 'rst_description': 'The radius of uncertainty for the location, measured in meters; 0-1500\n', 'name': 'horizontal_accuracy', 'parsed_type': {'type': 'std', 'name': 'float'}}, {'type': 'Integer', 'required': False, 'description': 'Direction in which the user is moving, in degrees. Must be between 1 and 360 if specified.', 'html_description': '<td>Direction in which the user is moving, in degrees. Must be between 1 and 360 if specified.</td>', 'rst_description': 'Direction in which the user is moving, in degrees. Must be between 1 and 360 if specified.\n', 'name': 'heading', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Integer', 'required': False, 'description': 'The maximum distance for proximity alerts about approaching another chat member, in meters. Must be between 1 and 100000 if specified.', 'html_description': '<td>The maximum distance for proximity alerts about approaching another chat member, in meters. Must be between 1 and 100000 if specified.</td>', 'rst_description': 'The maximum distance for proximity alerts about approaching another chat member, in meters. Must be between 1 and 100000 if specified.\n', 'name': 'proximity_alert_radius', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'InlineKeyboardMarkup', 'required': False, 'description': 'A JSON-serialized object for a new inline keyboard.', 'html_description': '<td>A JSON-serialized object for a new <a href="/bots/features#inline-keyboards">inline keyboard</a>.</td>', 'rst_description': 'A JSON-serialized object for a new `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_.\n', 'name': 'reply_markup', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'InlineKeyboardMarkup'}}}], 'category': 'methods', 'returning': {'type': 'Message or True', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'Message'}}, {'type': 'std', 'name': 'bool', 'value': True}]}, 'description': 'On success, if the edited message is not an inline message, the edited Message is returned, otherwise True is returned.'}, 'bases': ['TelegramMethod']}

        :param latitude: Latitude of new location
        :param longitude: Longitude of new location
        :param chat_id: Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param message_id: Required if *inline_message_id* is not specified. Identifier of the message to edit
        :param inline_message_id: Required if *chat_id* and *message_id* are not specified. Identifier of the inline message
        :param horizontal_accuracy: The radius of uncertainty for the location, measured in meters; 0-1500
        :param heading: Direction in which the user is moving, in degrees. Must be between 1 and 360 if specified.
        :param proximity_alert_radius: The maximum distance for proximity alerts about approaching another chat member, in meters. Must be between 1 and 100000 if specified.
        :param reply_markup: A JSON-serialized object for a new `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_.
        :param request_timeout: Request timeout
        :return: On success, if the edited message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned.
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
        Use this method to edit animation, audio, document, photo, or video messages. If a message is part of a message album, then it can be edited only to an audio for audio albums, only to a document for document albums and to a photo or a video otherwise. When an inline message is edited, a new file can't be uploaded; use a previously uploaded file via its file_id or specify a URL. On success, if the edited message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned.

        Source: https://core.telegram.org/bots/api#{'anchor': 'editmessagemedia', 'name': 'editMessageMedia', 'description': "Use this method to edit animation, audio, document, photo, or video messages. If a message is part of a message album, then it can be edited only to an audio for audio albums, only to a document for document albums and to a photo or a video otherwise. When an inline message is edited, a new file can't be uploaded; use a previously uploaded file via its file_id or specify a URL. On success, if the edited message is not an inline message, the edited Message is returned, otherwise True is returned.", 'html_description': '<p>Use this method to edit animation, audio, document, photo, or video messages. If a message is part of a message album, then it can be edited only to an audio for audio albums, only to a document for document albums and to a photo or a video otherwise. When an inline message is edited, a new file can\'t be uploaded; use a previously uploaded file via its file_id or specify a URL. On success, if the edited message is not an inline message, the edited <a href="#message">Message</a> is returned, otherwise <em>True</em> is returned.</p>', 'rst_description': "Use this method to edit animation, audio, document, photo, or video messages. If a message is part of a message album, then it can be edited only to an audio for audio albums, only to a document for document albums and to a photo or a video otherwise. When an inline message is edited, a new file can't be uploaded; use a previously uploaded file via its file_id or specify a URL. On success, if the edited message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned.", 'annotations': [{'type': 'InputMedia', 'required': True, 'description': 'A JSON-serialized object for a new media content of the message', 'html_description': '<td>A JSON-serialized object for a new media content of the message</td>', 'rst_description': 'A JSON-serialized object for a new media content of the message\n', 'name': 'media', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'InputMedia'}}}, {'type': 'Integer or String', 'required': False, 'description': 'Required if inline_message_id is not specified. Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Required if <em>inline_message_id</em> is not specified. Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': False, 'description': 'Required if inline_message_id is not specified. Identifier of the message to edit', 'html_description': '<td>Required if <em>inline_message_id</em> is not specified. Identifier of the message to edit</td>', 'rst_description': 'Required if *inline_message_id* is not specified. Identifier of the message to edit\n', 'name': 'message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'String', 'required': False, 'description': 'Required if chat_id and message_id are not specified. Identifier of the inline message', 'html_description': '<td>Required if <em>chat_id</em> and <em>message_id</em> are not specified. Identifier of the inline message</td>', 'rst_description': 'Required if *chat_id* and *message_id* are not specified. Identifier of the inline message\n', 'name': 'inline_message_id', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'InlineKeyboardMarkup', 'required': False, 'description': 'A JSON-serialized object for a new inline keyboard.', 'html_description': '<td>A JSON-serialized object for a new <a href="/bots/features#inline-keyboards">inline keyboard</a>.</td>', 'rst_description': 'A JSON-serialized object for a new `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_.\n', 'name': 'reply_markup', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'InlineKeyboardMarkup'}}}], 'category': 'methods', 'returning': {'type': 'Message or True', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'Message'}}, {'type': 'std', 'name': 'bool', 'value': True}]}, 'description': 'On success, if the edited message is not an inline message, the edited Message is returned, otherwise True is returned.'}, 'bases': ['TelegramMethod']}

        :param media: A JSON-serialized object for a new media content of the message
        :param chat_id: Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param message_id: Required if *inline_message_id* is not specified. Identifier of the message to edit
        :param inline_message_id: Required if *chat_id* and *message_id* are not specified. Identifier of the inline message
        :param reply_markup: A JSON-serialized object for a new `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_.
        :param request_timeout: Request timeout
        :return: On success, if the edited message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned.
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

        Source: https://core.telegram.org/bots/api#{'anchor': 'editmessagereplymarkup', 'name': 'editMessageReplyMarkup', 'description': 'Use this method to edit only the reply markup of messages. On success, if the edited message is not an inline message, the edited Message is returned, otherwise True is returned.', 'html_description': '<p>Use this method to edit only the reply markup of messages. On success, if the edited message is not an inline message, the edited <a href="#message">Message</a> is returned, otherwise <em>True</em> is returned.</p>', 'rst_description': 'Use this method to edit only the reply markup of messages. On success, if the edited message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned.', 'annotations': [{'type': 'Integer or String', 'required': False, 'description': 'Required if inline_message_id is not specified. Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Required if <em>inline_message_id</em> is not specified. Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': False, 'description': 'Required if inline_message_id is not specified. Identifier of the message to edit', 'html_description': '<td>Required if <em>inline_message_id</em> is not specified. Identifier of the message to edit</td>', 'rst_description': 'Required if *inline_message_id* is not specified. Identifier of the message to edit\n', 'name': 'message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'String', 'required': False, 'description': 'Required if chat_id and message_id are not specified. Identifier of the inline message', 'html_description': '<td>Required if <em>chat_id</em> and <em>message_id</em> are not specified. Identifier of the inline message</td>', 'rst_description': 'Required if *chat_id* and *message_id* are not specified. Identifier of the inline message\n', 'name': 'inline_message_id', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'InlineKeyboardMarkup', 'required': False, 'description': 'A JSON-serialized object for an inline keyboard.', 'html_description': '<td>A JSON-serialized object for an <a href="/bots/features#inline-keyboards">inline keyboard</a>.</td>', 'rst_description': 'A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_.\n', 'name': 'reply_markup', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'InlineKeyboardMarkup'}}}], 'category': 'methods', 'returning': {'type': 'Message or True', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'Message'}}, {'type': 'std', 'name': 'bool', 'value': True}]}, 'description': 'On success, if the edited message is not an inline message, the edited Message is returned, otherwise True is returned.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param message_id: Required if *inline_message_id* is not specified. Identifier of the message to edit
        :param inline_message_id: Required if *chat_id* and *message_id* are not specified. Identifier of the inline message
        :param reply_markup: A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_.
        :param request_timeout: Request timeout
        :return: On success, if the edited message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned.
        """

        call = EditMessageReplyMarkup(
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

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

        Source: https://core.telegram.org/bots/api#{'anchor': 'editmessagetext', 'name': 'editMessageText', 'description': 'Use this method to edit text and game messages. On success, if the edited message is not an inline message, the edited Message is returned, otherwise True is returned.', 'html_description': '<p>Use this method to edit text and <a href="#games">game</a> messages. On success, if the edited message is not an inline message, the edited <a href="#message">Message</a> is returned, otherwise <em>True</em> is returned.</p>', 'rst_description': 'Use this method to edit text and `game <https://core.telegram.org/bots/api#games>`_ messages. On success, if the edited message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned.', 'annotations': [{'type': 'String', 'required': True, 'description': 'New text of the message, 1-4096 characters after entities parsing', 'html_description': '<td>New text of the message, 1-4096 characters after entities parsing</td>', 'rst_description': 'New text of the message, 1-4096 characters after entities parsing\n', 'name': 'text', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'Integer or String', 'required': False, 'description': 'Required if inline_message_id is not specified. Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Required if <em>inline_message_id</em> is not specified. Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': False, 'description': 'Required if inline_message_id is not specified. Identifier of the message to edit', 'html_description': '<td>Required if <em>inline_message_id</em> is not specified. Identifier of the message to edit</td>', 'rst_description': 'Required if *inline_message_id* is not specified. Identifier of the message to edit\n', 'name': 'message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'String', 'required': False, 'description': 'Required if chat_id and message_id are not specified. Identifier of the inline message', 'html_description': '<td>Required if <em>chat_id</em> and <em>message_id</em> are not specified. Identifier of the inline message</td>', 'rst_description': 'Required if *chat_id* and *message_id* are not specified. Identifier of the inline message\n', 'name': 'inline_message_id', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': False, 'description': 'Mode for parsing entities in the message text. See formatting options for more details.', 'html_description': '<td>Mode for parsing entities in the message text. See <a href="#formatting-options">formatting options</a> for more details.</td>', 'rst_description': 'Mode for parsing entities in the message text. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.\n', 'name': 'parse_mode', 'parsed_type': {'type': 'std', 'name': 'str'}, 'value': 'UNSET'}, {'type': 'Array of MessageEntity', 'required': False, 'description': 'A JSON-serialized list of special entities that appear in message text, which can be specified instead of parse_mode', 'html_description': '<td>A JSON-serialized list of special entities that appear in message text, which can be specified instead of <em>parse_mode</em></td>', 'rst_description': 'A JSON-serialized list of special entities that appear in message text, which can be specified instead of *parse_mode*\n', 'name': 'entities', 'parsed_type': {'type': 'array', 'items': {'type': 'entity', 'references': {'category': 'types', 'name': 'MessageEntity'}}}}, {'type': 'Boolean', 'required': False, 'description': 'Disables link previews for links in this message', 'html_description': '<td>Disables link previews for links in this message</td>', 'rst_description': 'Disables link previews for links in this message\n', 'name': 'disable_web_page_preview', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'InlineKeyboardMarkup', 'required': False, 'description': 'A JSON-serialized object for an inline keyboard.', 'html_description': '<td>A JSON-serialized object for an <a href="/bots/features#inline-keyboards">inline keyboard</a>.</td>', 'rst_description': 'A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_.\n', 'name': 'reply_markup', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'InlineKeyboardMarkup'}}}], 'category': 'methods', 'returning': {'type': 'Message or True', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'Message'}}, {'type': 'std', 'name': 'bool', 'value': True}]}, 'description': 'On success, if the edited message is not an inline message, the edited Message is returned, otherwise True is returned.'}, 'bases': ['TelegramMethod']}

        :param text: New text of the message, 1-4096 characters after entities parsing
        :param chat_id: Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param message_id: Required if *inline_message_id* is not specified. Identifier of the message to edit
        :param inline_message_id: Required if *chat_id* and *message_id* are not specified. Identifier of the inline message
        :param parse_mode: Mode for parsing entities in the message text. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param entities: A JSON-serialized list of special entities that appear in message text, which can be specified instead of *parse_mode*
        :param disable_web_page_preview: Disables link previews for links in this message
        :param reply_markup: A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_.
        :param request_timeout: Request timeout
        :return: On success, if the edited message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned.
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

    async def export_chat_invite_link(
        self,
        chat_id: Union[int, str],
        request_timeout: Optional[int] = None,
    ) -> str:
        """
        Use this method to generate a new primary invite link for a chat; any previously generated primary link is revoked. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns the new invite link as *String* on success.

         Note: Each administrator in a chat generates their own invite links. Bots can't use invite links generated by other administrators. If you want your bot to work with invite links, it will need to generate its own link using :class:`aiogram.methods.export_chat_invite_link.ExportChatInviteLink` or by calling the :class:`aiogram.methods.get_chat.GetChat` method. If your bot needs to generate a new primary invite link replacing its previous one, use :class:`aiogram.methods.export_chat_invite_link.ExportChatInviteLink` again.

        Source: https://core.telegram.org/bots/api#{'anchor': 'exportchatinvitelink', 'name': 'exportChatInviteLink', 'description': "Use this method to generate a new primary invite link for a chat; any previously generated primary link is revoked. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns the new invite link as String on success.\nNote: Each administrator in a chat generates their own invite links. Bots can't use invite links generated by other administrators. If you want your bot to work with invite links, it will need to generate its own link using exportChatInviteLink or by calling the getChat method. If your bot needs to generate a new primary invite link replacing its previous one, use exportChatInviteLink again.", 'html_description': '<p>Use this method to generate a new primary invite link for a chat; any previously generated primary link is revoked. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns the new invite link as <em>String</em> on success.</p><blockquote>\n<p>Note: Each administrator in a chat generates their own invite links. Bots can\'t use invite links generated by other administrators. If you want your bot to work with invite links, it will need to generate its own link using <a href="#exportchatinvitelink">exportChatInviteLink</a> or by calling the <a href="#getchat">getChat</a> method. If your bot needs to generate a new primary invite link replacing its previous one, use <a href="#exportchatinvitelink">exportChatInviteLink</a> again.</p>\n</blockquote>', 'rst_description': "Use this method to generate a new primary invite link for a chat; any previously generated primary link is revoked. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns the new invite link as *String* on success.\n\n Note: Each administrator in a chat generates their own invite links. Bots can't use invite links generated by other administrators. If you want your bot to work with invite links, it will need to generate its own link using :class:`aiogram.methods.export_chat_invite_link.ExportChatInviteLink` or by calling the :class:`aiogram.methods.get_chat.GetChat` method. If your bot needs to generate a new primary invite link replacing its previous one, use :class:`aiogram.methods.export_chat_invite_link.ExportChatInviteLink` again.", 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}], 'category': 'methods', 'returning': {'type': 'String', 'parsed_type': {'type': 'std', 'name': 'str'}, 'description': 'Returns the new invite link as String on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param request_timeout: Request timeout
        :return: If your bot needs to generate a new primary invite link replacing its previous one, use :class:`aiogram.methods.export_chat_invite_link.ExportChatInviteLink` again.
        """

        call = ExportChatInviteLink(
            chat_id=chat_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def forward_message(
        self,
        chat_id: Union[int, str],
        from_chat_id: Union[int, str],
        message_id: int,
        message_thread_id: Optional[int] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        Use this method to forward messages of any kind. Service messages can't be forwarded. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#{'anchor': 'forwardmessage', 'name': 'forwardMessage', 'description': "Use this method to forward messages of any kind. Service messages can't be forwarded. On success, the sent Message is returned.", 'html_description': '<p>Use this method to forward messages of any kind. Service messages can\'t be forwarded. On success, the sent <a href="#message">Message</a> is returned.</p>', 'rst_description': "Use this method to forward messages of any kind. Service messages can't be forwarded. On success, the sent :class:`aiogram.types.message.Message` is returned.", 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the chat where the original message was sent (or channel username in the format @channelusername)', 'html_description': '<td>Unique identifier for the chat where the original message was sent (or channel username in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the chat where the original message was sent (or channel username in the format :code:`@channelusername`)\n', 'name': 'from_chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': True, 'description': 'Message identifier in the chat specified in from_chat_id', 'html_description': '<td>Message identifier in the chat specified in <em>from_chat_id</em></td>', 'rst_description': 'Message identifier in the chat specified in *from_chat_id*\n', 'name': 'message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Integer', 'required': False, 'description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only', 'html_description': '<td>Unique identifier for the target message thread (topic) of the forum; for forum supergroups only</td>', 'rst_description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only\n', 'name': 'message_thread_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': 'Sends the message silently. Users will receive a notification with no sound.', 'html_description': '<td>Sends the message <a href="https://telegram.org/blog/channels-2-0#silent-messages">silently</a>. Users will receive a notification with no sound.</td>', 'rst_description': 'Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.\n', 'name': 'disable_notification', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Protects the contents of the forwarded message from forwarding and saving', 'html_description': '<td>Protects the contents of the forwarded message from forwarding and saving</td>', 'rst_description': 'Protects the contents of the forwarded message from forwarding and saving\n', 'name': 'protect_content', 'parsed_type': {'type': 'std', 'name': 'bool'}}], 'category': 'methods', 'returning': {'type': 'Message', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'Message'}}, 'description': 'On success, the sent Message is returned.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param from_chat_id: Unique identifier for the chat where the original message was sent (or channel username in the format :code:`@channelusername`)
        :param message_id: Message identifier in the chat specified in *from_chat_id*
        :param message_thread_id: Unique identifier for the target message thread (topic) of the forum; for forum supergroups only
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the forwarded message from forwarding and saving
        :param request_timeout: Request timeout
        :return: On success, the sent :class:`aiogram.types.message.Message` is returned.
        """

        call = ForwardMessage(
            chat_id=chat_id,
            from_chat_id=from_chat_id,
            message_id=message_id,
            message_thread_id=message_thread_id,
            disable_notification=disable_notification,
            protect_content=protect_content,
        )
        return await self(call, request_timeout=request_timeout)

    async def get_chat(
        self,
        chat_id: Union[int, str],
        request_timeout: Optional[int] = None,
    ) -> Chat:
        """
        Use this method to get up to date information about the chat (current name of the user for one-on-one conversations, current username of a user, group or channel, etc.). Returns a :class:`aiogram.types.chat.Chat` object on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'getchat', 'name': 'getChat', 'description': 'Use this method to get up to date information about the chat (current name of the user for one-on-one conversations, current username of a user, group or channel, etc.). Returns a Chat object on success.', 'html_description': '<p>Use this method to get up to date information about the chat (current name of the user for one-on-one conversations, current username of a user, group or channel, etc.). Returns a <a href="#chat">Chat</a> object on success.</p>', 'rst_description': 'Use this method to get up to date information about the chat (current name of the user for one-on-one conversations, current username of a user, group or channel, etc.). Returns a :class:`aiogram.types.chat.Chat` object on success.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target supergroup or channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target supergroup or channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target supergroup or channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}], 'category': 'methods', 'returning': {'type': 'Chat', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'Chat'}}, 'description': 'Returns a Chat object on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel (in the format :code:`@channelusername`)
        :param request_timeout: Request timeout
        :return: Returns a :class:`aiogram.types.chat.Chat` object on success.
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
        Use this method to get a list of administrators in a chat, which aren't bots. Returns an Array of :class:`aiogram.types.chat_member.ChatMember` objects.

        Source: https://core.telegram.org/bots/api#{'anchor': 'getchatadministrators', 'name': 'getChatAdministrators', 'description': "Use this method to get a list of administrators in a chat, which aren't bots. Returns an Array of ChatMember objects.", 'html_description': '<p>Use this method to get a list of administrators in a chat, which aren\'t bots. Returns an Array of <a href="#chatmember">ChatMember</a> objects.</p>', 'rst_description': "Use this method to get a list of administrators in a chat, which aren't bots. Returns an Array of :class:`aiogram.types.chat_member.ChatMember` objects.", 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target supergroup or channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target supergroup or channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target supergroup or channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}], 'category': 'methods', 'returning': {'parsed_type': {'type': 'array', 'items': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'ChatMemberOwner'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ChatMemberAdministrator'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ChatMemberMember'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ChatMemberRestricted'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ChatMemberLeft'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ChatMemberBanned'}}]}}}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel (in the format :code:`@channelusername`)
        :param request_timeout: Request timeout
        :return: Returns an Array of :class:`aiogram.types.chat_member.ChatMember` objects.
        """

        call = GetChatAdministrators(
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
        Use this method to get information about a member of a chat. The method is only guaranteed to work for other users if the bot is an administrator in the chat. Returns a :class:`aiogram.types.chat_member.ChatMember` object on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'getchatmember', 'name': 'getChatMember', 'description': 'Use this method to get information about a member of a chat. The method is only guaranteed to work for other users if the bot is an administrator in the chat. Returns a ChatMember object on success.', 'html_description': '<p>Use this method to get information about a member of a chat. The method is only guaranteed to work for other users if the bot is an administrator in the chat. Returns a <a href="#chatmember">ChatMember</a> object on success.</p>', 'rst_description': 'Use this method to get information about a member of a chat. The method is only guaranteed to work for other users if the bot is an administrator in the chat. Returns a :class:`aiogram.types.chat_member.ChatMember` object on success.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target supergroup or channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target supergroup or channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target supergroup or channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': True, 'description': 'Unique identifier of the target user', 'html_description': '<td>Unique identifier of the target user</td>', 'rst_description': 'Unique identifier of the target user\n', 'name': 'user_id', 'parsed_type': {'type': 'std', 'name': 'int'}}], 'category': 'methods', 'returning': {'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'ChatMemberOwner'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ChatMemberAdministrator'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ChatMemberMember'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ChatMemberRestricted'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ChatMemberLeft'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ChatMemberBanned'}}]}}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel (in the format :code:`@channelusername`)
        :param user_id: Unique identifier of the target user
        :param request_timeout: Request timeout
        :return: Returns a :class:`aiogram.types.chat_member.ChatMember` object on success.
        """

        call = GetChatMember(
            chat_id=chat_id,
            user_id=user_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def get_chat_member_count(
        self,
        chat_id: Union[int, str],
        request_timeout: Optional[int] = None,
    ) -> int:
        """
        Use this method to get the number of members in a chat. Returns *Int* on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'getchatmembercount', 'name': 'getChatMemberCount', 'description': 'Use this method to get the number of members in a chat. Returns Int on success.', 'html_description': '<p>Use this method to get the number of members in a chat. Returns <em>Int</em> on success.</p>', 'rst_description': 'Use this method to get the number of members in a chat. Returns *Int* on success.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target supergroup or channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target supergroup or channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target supergroup or channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}], 'category': 'methods', 'returning': {'type': 'Integer', 'parsed_type': {'type': 'std', 'name': 'int'}, 'description': 'Returns Int on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel (in the format :code:`@channelusername`)
        :param request_timeout: Request timeout
        :return: Returns *Int* on success.
        """

        call = GetChatMemberCount(
            chat_id=chat_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def get_chat_menu_button(
        self,
        chat_id: Optional[int] = None,
        request_timeout: Optional[int] = None,
    ) -> Union[MenuButtonDefault, MenuButtonWebApp, MenuButtonCommands]:
        """
        Use this method to get the current value of the bot's menu button in a private chat, or the default menu button. Returns :class:`aiogram.types.menu_button.MenuButton` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'getchatmenubutton', 'name': 'getChatMenuButton', 'description': "Use this method to get the current value of the bot's menu button in a private chat, or the default menu button. Returns MenuButton on success.", 'html_description': '<p>Use this method to get the current value of the bot\'s menu button in a private chat, or the default menu button. Returns <a href="#menubutton">MenuButton</a> on success.</p>', 'rst_description': "Use this method to get the current value of the bot's menu button in a private chat, or the default menu button. Returns :class:`aiogram.types.menu_button.MenuButton` on success.", 'annotations': [{'type': 'Integer', 'required': False, 'description': "Unique identifier for the target private chat. If not specified, default bot's menu button will be returned", 'html_description': "<td>Unique identifier for the target private chat. If not specified, default bot's menu button will be returned</td>", 'rst_description': "Unique identifier for the target private chat. If not specified, default bot's menu button will be returned\n", 'name': 'chat_id', 'parsed_type': {'type': 'std', 'name': 'int'}}], 'category': 'methods', 'returning': {'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'MenuButtonDefault'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'MenuButtonWebApp'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'MenuButtonCommands'}}]}}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target private chat. If not specified, default bot's menu button will be returned
        :param request_timeout: Request timeout
        :return: Returns :class:`aiogram.types.menu_button.MenuButton` on success.
        """

        call = GetChatMenuButton(
            chat_id=chat_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def get_custom_emoji_stickers(
        self,
        custom_emoji_ids: List[str],
        request_timeout: Optional[int] = None,
    ) -> List[Sticker]:
        """
        Use this method to get information about custom emoji stickers by their identifiers. Returns an Array of :class:`aiogram.types.sticker.Sticker` objects.

        Source: https://core.telegram.org/bots/api#{'anchor': 'getcustomemojistickers', 'name': 'getCustomEmojiStickers', 'description': 'Use this method to get information about custom emoji stickers by their identifiers. Returns an Array of Sticker objects.', 'html_description': '<p>Use this method to get information about custom emoji stickers by their identifiers. Returns an Array of <a href="#sticker">Sticker</a> objects.</p>', 'rst_description': 'Use this method to get information about custom emoji stickers by their identifiers. Returns an Array of :class:`aiogram.types.sticker.Sticker` objects.', 'annotations': [{'type': 'Array of String', 'required': True, 'description': 'List of custom emoji identifiers. At most 200 custom emoji identifiers can be specified.', 'html_description': '<td>List of custom emoji identifiers. At most 200 custom emoji identifiers can be specified.</td>', 'rst_description': 'List of custom emoji identifiers. At most 200 custom emoji identifiers can be specified.\n', 'name': 'custom_emoji_ids', 'parsed_type': {'type': 'array', 'items': {'type': 'std', 'name': 'str'}}}], 'category': 'methods', 'returning': {'type': 'Array of Sticker', 'parsed_type': {'type': 'array', 'items': {'type': 'entity', 'references': {'category': 'types', 'name': 'Sticker'}}}, 'description': 'Returns an Array of Sticker objects.'}, 'bases': ['TelegramMethod']}

        :param custom_emoji_ids: List of custom emoji identifiers. At most 200 custom emoji identifiers can be specified.
        :param request_timeout: Request timeout
        :return: Returns an Array of :class:`aiogram.types.sticker.Sticker` objects.
        """

        call = GetCustomEmojiStickers(
            custom_emoji_ids=custom_emoji_ids,
        )
        return await self(call, request_timeout=request_timeout)

    async def get_file(
        self,
        file_id: str,
        request_timeout: Optional[int] = None,
    ) -> File:
        """
        Use this method to get basic information about a file and prepare it for downloading. For the moment, bots can download files of up to 20MB in size. On success, a :class:`aiogram.types.file.File` object is returned. The file can then be downloaded via the link :code:`https://api.telegram.org/file/bot<token>/<file_path>`, where :code:`<file_path>` is taken from the response. It is guaranteed that the link will be valid for at least 1 hour. When the link expires, a new one can be requested by calling :class:`aiogram.methods.get_file.GetFile` again.
        **Note:** This function may not preserve the original file name and MIME type. You should save the file's MIME type and name (if available) when the File object is received.

        Source: https://core.telegram.org/bots/api#{'anchor': 'getfile', 'name': 'getFile', 'description': "Use this method to get basic information about a file and prepare it for downloading. For the moment, bots can download files of up to 20MB in size. On success, a File object is returned. The file can then be downloaded via the link https://api.telegram.org/file/bot<token>/<file_path>, where <file_path> is taken from the response. It is guaranteed that the link will be valid for at least 1 hour. When the link expires, a new one can be requested by calling getFile again.\nNote: This function may not preserve the original file name and MIME type. You should save the file's MIME type and name (if available) when the File object is received.", 'html_description': '<p>Use this method to get basic information about a file and prepare it for downloading. For the moment, bots can download files of up to 20MB in size. On success, a <a href="#file">File</a> object is returned. The file can then be downloaded via the link <code>https://api.telegram.org/file/bot&lt;token&gt;/&lt;file_path&gt;</code>, where <code>&lt;file_path&gt;</code> is taken from the response. It is guaranteed that the link will be valid for at least 1 hour. When the link expires, a new one can be requested by calling <a href="#getfile">getFile</a> again.</p><p><strong>Note:</strong> This function may not preserve the original file name and MIME type. You should save the file\'s MIME type and name (if available) when the File object is received.</p>', 'rst_description': "Use this method to get basic information about a file and prepare it for downloading. For the moment, bots can download files of up to 20MB in size. On success, a :class:`aiogram.types.file.File` object is returned. The file can then be downloaded via the link :code:`https://api.telegram.org/file/bot<token>/<file_path>`, where :code:`<file_path>` is taken from the response. It is guaranteed that the link will be valid for at least 1 hour. When the link expires, a new one can be requested by calling :class:`aiogram.methods.get_file.GetFile` again.\n**Note:** This function may not preserve the original file name and MIME type. You should save the file's MIME type and name (if available) when the File object is received.", 'annotations': [{'type': 'String', 'required': True, 'description': 'File identifier to get information about', 'html_description': '<td>File identifier to get information about</td>', 'rst_description': 'File identifier to get information about\n', 'name': 'file_id', 'parsed_type': {'type': 'std', 'name': 'str'}}], 'category': 'methods', 'returning': {'type': 'File', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'File'}}, 'description': 'On success, a File object is returned.'}, 'bases': ['TelegramMethod']}

        :param file_id: File identifier to get information about
        :param request_timeout: Request timeout
        :return: You should save the file's MIME type and name (if available) when the File object is received.
        """

        call = GetFile(
            file_id=file_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def get_forum_topic_icon_stickers(
        self,
        request_timeout: Optional[int] = None,
    ) -> List[Sticker]:
        """
        Use this method to get custom emoji stickers, which can be used as a forum topic icon by any user. Requires no parameters. Returns an Array of :class:`aiogram.types.sticker.Sticker` objects.

        Source: https://core.telegram.org/bots/api#{'anchor': 'getforumtopiciconstickers', 'name': 'getForumTopicIconStickers', 'description': 'Use this method to get custom emoji stickers, which can be used as a forum topic icon by any user. Requires no parameters. Returns an Array of Sticker objects.', 'html_description': '<p>Use this method to get custom emoji stickers, which can be used as a forum topic icon by any user. Requires no parameters. Returns an Array of <a href="#sticker">Sticker</a> objects.</p>', 'rst_description': 'Use this method to get custom emoji stickers, which can be used as a forum topic icon by any user. Requires no parameters. Returns an Array of :class:`aiogram.types.sticker.Sticker` objects.', 'annotations': [], 'category': 'methods', 'returning': {'type': 'Array of Sticker', 'parsed_type': {'type': 'array', 'items': {'type': 'entity', 'references': {'category': 'types', 'name': 'Sticker'}}}, 'description': 'Returns an Array of Sticker objects.'}, 'bases': ['TelegramMethod']}

        :param request_timeout: Request timeout
        :return: Returns an Array of :class:`aiogram.types.sticker.Sticker` objects.
        """

        call = GetForumTopicIconStickers()
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
        Use this method to get data for high score tables. Will return the score of the specified user and several of their neighbors in a game. Returns an Array of :class:`aiogram.types.game_high_score.GameHighScore` objects.

         This method will currently return scores for the target user, plus two of their closest neighbors on each side. Will also return the top three users if the user and their neighbors are not among them. Please note that this behavior is subject to change.

        Source: https://core.telegram.org/bots/api#{'anchor': 'getgamehighscores', 'name': 'getGameHighScores', 'description': 'Use this method to get data for high score tables. Will return the score of the specified user and several of their neighbors in a game. Returns an Array of GameHighScore objects.\nThis method will currently return scores for the target user, plus two of their closest neighbors on each side. Will also return the top three users if the user and their neighbors are not among them. Please note that this behavior is subject to change.', 'html_description': '<p>Use this method to get data for high score tables. Will return the score of the specified user and several of their neighbors in a game. Returns an Array of <a href="#gamehighscore">GameHighScore</a> objects.</p><blockquote>\n<p>This method will currently return scores for the target user, plus two of their closest neighbors on each side. Will also return the top three users if the user and their neighbors are not among them. Please note that this behavior is subject to change.</p>\n</blockquote>', 'rst_description': 'Use this method to get data for high score tables. Will return the score of the specified user and several of their neighbors in a game. Returns an Array of :class:`aiogram.types.game_high_score.GameHighScore` objects.\n\n This method will currently return scores for the target user, plus two of their closest neighbors on each side. Will also return the top three users if the user and their neighbors are not among them. Please note that this behavior is subject to change.', 'annotations': [{'type': 'Integer', 'required': True, 'description': 'Target user id', 'html_description': '<td>Target user id</td>', 'rst_description': 'Target user id\n', 'name': 'user_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Integer', 'required': False, 'description': 'Required if inline_message_id is not specified. Unique identifier for the target chat', 'html_description': '<td>Required if <em>inline_message_id</em> is not specified. Unique identifier for the target chat</td>', 'rst_description': 'Required if *inline_message_id* is not specified. Unique identifier for the target chat\n', 'name': 'chat_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Integer', 'required': False, 'description': 'Required if inline_message_id is not specified. Identifier of the sent message', 'html_description': '<td>Required if <em>inline_message_id</em> is not specified. Identifier of the sent message</td>', 'rst_description': 'Required if *inline_message_id* is not specified. Identifier of the sent message\n', 'name': 'message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'String', 'required': False, 'description': 'Required if chat_id and message_id are not specified. Identifier of the inline message', 'html_description': '<td>Required if <em>chat_id</em> and <em>message_id</em> are not specified. Identifier of the inline message</td>', 'rst_description': 'Required if *chat_id* and *message_id* are not specified. Identifier of the inline message\n', 'name': 'inline_message_id', 'parsed_type': {'type': 'std', 'name': 'str'}}], 'category': 'methods', 'returning': {'type': 'Array of GameHighScore', 'parsed_type': {'type': 'array', 'items': {'type': 'entity', 'references': {'category': 'types', 'name': 'GameHighScore'}}}, 'description': 'Will return the score of the specified user and several of their neighbors in a game. Returns an Array of GameHighScore objects. This method will currently return scores for the target user, plus two of their closest neighbors on each side. Will also return the top three users if the user and their neighbors are not among them.'}, 'bases': ['TelegramMethod']}

        :param user_id: Target user id
        :param chat_id: Required if *inline_message_id* is not specified. Unique identifier for the target chat
        :param message_id: Required if *inline_message_id* is not specified. Identifier of the sent message
        :param inline_message_id: Required if *chat_id* and *message_id* are not specified. Identifier of the inline message
        :param request_timeout: Request timeout
        :return: Please note that this behavior is subject to change.
        """

        call = GetGameHighScores(
            user_id=user_id,
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def get_me(
        self,
        request_timeout: Optional[int] = None,
    ) -> User:
        """
        A simple method for testing your bot's authentication token. Requires no parameters. Returns basic information about the bot in form of a :class:`aiogram.types.user.User` object.

        Source: https://core.telegram.org/bots/api#{'anchor': 'getme', 'name': 'getMe', 'description': "A simple method for testing your bot's authentication token. Requires no parameters. Returns basic information about the bot in form of a User object.", 'html_description': '<p>A simple method for testing your bot\'s authentication token. Requires no parameters. Returns basic information about the bot in form of a <a href="#user">User</a> object.</p>', 'rst_description': "A simple method for testing your bot's authentication token. Requires no parameters. Returns basic information about the bot in form of a :class:`aiogram.types.user.User` object.", 'annotations': [], 'category': 'methods', 'returning': {'type': 'User', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'User'}}, 'description': 'Returns basic information about the bot in form of a User object.'}, 'bases': ['TelegramMethod']}

        :param request_timeout: Request timeout
        :return: Returns basic information about the bot in form of a :class:`aiogram.types.user.User` object.
        """

        call = GetMe()
        return await self(call, request_timeout=request_timeout)

    async def get_my_commands(
        self,
        scope: Optional[BotCommandScope] = None,
        language_code: Optional[str] = None,
        request_timeout: Optional[int] = None,
    ) -> List[BotCommand]:
        """
        Use this method to get the current list of the bot's commands for the given scope and user language. Returns an Array of :class:`aiogram.types.bot_command.BotCommand` objects. If commands aren't set, an empty list is returned.

        Source: https://core.telegram.org/bots/api#{'anchor': 'getmycommands', 'name': 'getMyCommands', 'description': "Use this method to get the current list of the bot's commands for the given scope and user language. Returns an Array of BotCommand objects. If commands aren't set, an empty list is returned.", 'html_description': '<p>Use this method to get the current list of the bot\'s commands for the given scope and user language. Returns an Array of <a href="#botcommand">BotCommand</a> objects. If commands aren\'t set, an empty list is returned.</p>', 'rst_description': "Use this method to get the current list of the bot's commands for the given scope and user language. Returns an Array of :class:`aiogram.types.bot_command.BotCommand` objects. If commands aren't set, an empty list is returned.", 'annotations': [{'type': 'BotCommandScope', 'required': False, 'description': 'A JSON-serialized object, describing scope of users. Defaults to BotCommandScopeDefault.', 'html_description': '<td>A JSON-serialized object, describing scope of users. Defaults to <a href="#botcommandscopedefault">BotCommandScopeDefault</a>.</td>', 'rst_description': 'A JSON-serialized object, describing scope of users. Defaults to :class:`aiogram.types.bot_command_scope_default.BotCommandScopeDefault`.\n', 'name': 'scope', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'BotCommandScope'}}}, {'type': 'String', 'required': False, 'description': 'A two-letter ISO 639-1 language code or an empty string', 'html_description': '<td>A two-letter ISO 639-1 language code or an empty string</td>', 'rst_description': 'A two-letter ISO 639-1 language code or an empty string\n', 'name': 'language_code', 'parsed_type': {'type': 'std', 'name': 'str'}}], 'category': 'methods', 'returning': {'type': 'Array of BotCommand', 'parsed_type': {'type': 'array', 'items': {'type': 'entity', 'references': {'category': 'types', 'name': 'BotCommand'}}}, 'description': "Returns an Array of BotCommand objects. If commands aren't set, an empty list is returned."}, 'bases': ['TelegramMethod']}

        :param scope: A JSON-serialized object, describing scope of users. Defaults to :class:`aiogram.types.bot_command_scope_default.BotCommandScopeDefault`.
        :param language_code: A two-letter ISO 639-1 language code or an empty string
        :param request_timeout: Request timeout
        :return: If commands aren't set, an empty list is returned.
        """

        call = GetMyCommands(
            scope=scope,
            language_code=language_code,
        )
        return await self(call, request_timeout=request_timeout)

    async def get_my_default_administrator_rights(
        self,
        for_channels: Optional[bool] = None,
        request_timeout: Optional[int] = None,
    ) -> ChatAdministratorRights:
        """
        Use this method to get the current default administrator rights of the bot. Returns :class:`aiogram.types.chat_administrator_rights.ChatAdministratorRights` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'getmydefaultadministratorrights', 'name': 'getMyDefaultAdministratorRights', 'description': 'Use this method to get the current default administrator rights of the bot. Returns ChatAdministratorRights on success.', 'html_description': '<p>Use this method to get the current default administrator rights of the bot. Returns <a href="#chatadministratorrights">ChatAdministratorRights</a> on success.</p>', 'rst_description': 'Use this method to get the current default administrator rights of the bot. Returns :class:`aiogram.types.chat_administrator_rights.ChatAdministratorRights` on success.', 'annotations': [{'type': 'Boolean', 'required': False, 'description': 'Pass True to get default administrator rights of the bot in channels. Otherwise, default administrator rights of the bot for groups and supergroups will be returned.', 'html_description': '<td>Pass <em>True</em> to get default administrator rights of the bot in channels. Otherwise, default administrator rights of the bot for groups and supergroups will be returned.</td>', 'rst_description': 'Pass :code:`True` to get default administrator rights of the bot in channels. Otherwise, default administrator rights of the bot for groups and supergroups will be returned.\n', 'name': 'for_channels', 'parsed_type': {'type': 'std', 'name': 'bool'}}], 'category': 'methods', 'returning': {'type': 'ChatAdministratorRights', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'ChatAdministratorRights'}}, 'description': 'Returns ChatAdministratorRights on success.'}, 'bases': ['TelegramMethod']}

        :param for_channels: Pass :code:`True` to get default administrator rights of the bot in channels. Otherwise, default administrator rights of the bot for groups and supergroups will be returned.
        :param request_timeout: Request timeout
        :return: Returns :class:`aiogram.types.chat_administrator_rights.ChatAdministratorRights` on success.
        """

        call = GetMyDefaultAdministratorRights(
            for_channels=for_channels,
        )
        return await self(call, request_timeout=request_timeout)

    async def get_sticker_set(
        self,
        name: str,
        request_timeout: Optional[int] = None,
    ) -> StickerSet:
        """
        Use this method to get a sticker set. On success, a :class:`aiogram.types.sticker_set.StickerSet` object is returned.

        Source: https://core.telegram.org/bots/api#{'anchor': 'getstickerset', 'name': 'getStickerSet', 'description': 'Use this method to get a sticker set. On success, a StickerSet object is returned.', 'html_description': '<p>Use this method to get a sticker set. On success, a <a href="#stickerset">StickerSet</a> object is returned.</p>', 'rst_description': 'Use this method to get a sticker set. On success, a :class:`aiogram.types.sticker_set.StickerSet` object is returned.', 'annotations': [{'type': 'String', 'required': True, 'description': 'Name of the sticker set', 'html_description': '<td>Name of the sticker set</td>', 'rst_description': 'Name of the sticker set\n', 'name': 'name', 'parsed_type': {'type': 'std', 'name': 'str'}}], 'category': 'methods', 'returning': {'type': 'StickerSet', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'StickerSet'}}, 'description': 'On success, a StickerSet object is returned.'}, 'bases': ['TelegramMethod']}

        :param name: Name of the sticker set
        :param request_timeout: Request timeout
        :return: On success, a :class:`aiogram.types.sticker_set.StickerSet` object is returned.
        """

        call = GetStickerSet(
            name=name,
        )
        return await self(call, request_timeout=request_timeout)

    async def get_updates(
        self,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        timeout: Optional[int] = None,
        allowed_updates: Optional[List[str]] = None,
        request_timeout: Optional[int] = None,
    ) -> List[Update]:
        """
        Use this method to receive incoming updates using long polling (`wiki <https://en.wikipedia.org/wiki/Push_technology#Long_polling>`_). Returns an Array of :class:`aiogram.types.update.Update` objects.

         **Notes**

         **1.** This method will not work if an outgoing webhook is set up.

         **2.** In order to avoid getting duplicate updates, recalculate *offset* after each server response.

        Source: https://core.telegram.org/bots/api#{'anchor': 'getupdates', 'name': 'getUpdates', 'description': 'Use this method to receive incoming updates using long polling (wiki). Returns an Array of Update objects.\nNotes\n1. This method will not work if an outgoing webhook is set up.\n2. In order to avoid getting duplicate updates, recalculate offset after each server response.', 'html_description': '<p>Use this method to receive incoming updates using long polling (<a href="https://en.wikipedia.org/wiki/Push_technology#Long_polling">wiki</a>). Returns an Array of <a href="#update">Update</a> objects.</p><blockquote>\n<p><strong>Notes</strong><br/>\n<strong>1.</strong> This method will not work if an outgoing webhook is set up.<br/>\n<strong>2.</strong> In order to avoid getting duplicate updates, recalculate <em>offset</em> after each server response.</p>\n</blockquote>', 'rst_description': 'Use this method to receive incoming updates using long polling (`wiki <https://en.wikipedia.org/wiki/Push_technology#Long_polling>`_). Returns an Array of :class:`aiogram.types.update.Update` objects.\n\n **Notes**\n \n **1.** This method will not work if an outgoing webhook is set up.\n \n **2.** In order to avoid getting duplicate updates, recalculate *offset* after each server response.', 'annotations': [{'type': 'Integer', 'required': False, 'description': 'Identifier of the first update to be returned. Must be greater by one than the highest among the identifiers of previously received updates. By default, updates starting with the earliest unconfirmed update are returned. An update is considered confirmed as soon as getUpdates is called with an offset higher than its update_id. The negative offset can be specified to retrieve updates starting from -offset update from the end of the updates queue. All previous updates will forgotten.', 'html_description': '<td>Identifier of the first update to be returned. Must be greater by one than the highest among the identifiers of previously received updates. By default, updates starting with the earliest unconfirmed update are returned. An update is considered confirmed as soon as <a href="#getupdates">getUpdates</a> is called with an <em>offset</em> higher than its <em>update_id</em>. The negative offset can be specified to retrieve updates starting from <em>-offset</em> update from the end of the updates queue. All previous updates will forgotten.</td>', 'rst_description': 'Identifier of the first update to be returned. Must be greater by one than the highest among the identifiers of previously received updates. By default, updates starting with the earliest unconfirmed update are returned. An update is considered confirmed as soon as :class:`aiogram.methods.get_updates.GetUpdates` is called with an *offset* higher than its *update_id*. The negative offset can be specified to retrieve updates starting from *-offset* update from the end of the updates queue. All previous updates will forgotten.\n', 'name': 'offset', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Integer', 'required': False, 'description': 'Limits the number of updates to be retrieved. Values between 1-100 are accepted. Defaults to 100.', 'html_description': '<td>Limits the number of updates to be retrieved. Values between 1-100 are accepted. Defaults to 100.</td>', 'rst_description': 'Limits the number of updates to be retrieved. Values between 1-100 are accepted. Defaults to 100.\n', 'name': 'limit', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Integer', 'required': False, 'description': 'Timeout in seconds for long polling. Defaults to 0, i.e. usual short polling. Should be positive, short polling should be used for testing purposes only.', 'html_description': '<td>Timeout in seconds for long polling. Defaults to 0, i.e. usual short polling. Should be positive, short polling should be used for testing purposes only.</td>', 'rst_description': 'Timeout in seconds for long polling. Defaults to 0, i.e. usual short polling. Should be positive, short polling should be used for testing purposes only.\n', 'name': 'timeout', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Array of String', 'required': False, 'description': "A JSON-serialized list of the update types you want your bot to receive. For example, specify ['message', 'edited_channel_post', 'callback_query'] to only receive updates of these types. See Update for a complete list of available update types. Specify an empty list to receive all update types except chat_member (default). If not specified, the previous setting will be used.\n\nPlease note that this parameter doesn't affect updates created before the call to the getUpdates, so unwanted updates may be received for a short period of time.", 'html_description': '<td>A JSON-serialized list of the update types you want your bot to receive. For example, specify [&#8220;message&#8221;, &#8220;edited_channel_post&#8221;, &#8220;callback_query&#8221;] to only receive updates of these types. See <a href="#update">Update</a> for a complete list of available update types. Specify an empty list to receive all update types except <em>chat_member</em> (default). If not specified, the previous setting will be used.<br/>\n<br/>\nPlease note that this parameter doesn\'t affect updates created before the call to the getUpdates, so unwanted updates may be received for a short period of time.</td>', 'rst_description': "A JSON-serialized list of the update types you want your bot to receive. For example, specify ['message', 'edited_channel_post', 'callback_query'] to only receive updates of these types. See :class:`aiogram.types.update.Update` for a complete list of available update types. Specify an empty list to receive all update types except *chat_member* (default). If not specified, the previous setting will be used.\n\n\n\nPlease note that this parameter doesn't affect updates created before the call to the getUpdates, so unwanted updates may be received for a short period of time.\n", 'name': 'allowed_updates', 'parsed_type': {'type': 'array', 'items': {'type': 'std', 'name': 'str'}}}], 'category': 'methods', 'returning': {'type': 'Array of Update', 'parsed_type': {'type': 'array', 'items': {'type': 'entity', 'references': {'category': 'types', 'name': 'Update'}}}, 'description': 'Returns an Array of Update objects.'}, 'bases': ['TelegramMethod']}

        :param offset: Identifier of the first update to be returned. Must be greater by one than the highest among the identifiers of previously received updates. By default, updates starting with the earliest unconfirmed update are returned. An update is considered confirmed as soon as :class:`aiogram.methods.get_updates.GetUpdates` is called with an *offset* higher than its *update_id*. The negative offset can be specified to retrieve updates starting from *-offset* update from the end of the updates queue. All previous updates will forgotten.
        :param limit: Limits the number of updates to be retrieved. Values between 1-100 are accepted. Defaults to 100.
        :param timeout: Timeout in seconds for long polling. Defaults to 0, i.e. usual short polling. Should be positive, short polling should be used for testing purposes only.
        :param allowed_updates: A JSON-serialized list of the update types you want your bot to receive. For example, specify ['message', 'edited_channel_post', 'callback_query'] to only receive updates of these types. See :class:`aiogram.types.update.Update` for a complete list of available update types. Specify an empty list to receive all update types except *chat_member* (default). If not specified, the previous setting will be used.
        :param request_timeout: Request timeout
        :return: Returns an Array of :class:`aiogram.types.update.Update` objects.
        """

        call = GetUpdates(
            offset=offset,
            limit=limit,
            timeout=timeout,
            allowed_updates=allowed_updates,
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

        Source: https://core.telegram.org/bots/api#{'anchor': 'getuserprofilephotos', 'name': 'getUserProfilePhotos', 'description': 'Use this method to get a list of profile pictures for a user. Returns a UserProfilePhotos object.', 'html_description': '<p>Use this method to get a list of profile pictures for a user. Returns a <a href="#userprofilephotos">UserProfilePhotos</a> object.</p>', 'rst_description': 'Use this method to get a list of profile pictures for a user. Returns a :class:`aiogram.types.user_profile_photos.UserProfilePhotos` object.', 'annotations': [{'type': 'Integer', 'required': True, 'description': 'Unique identifier of the target user', 'html_description': '<td>Unique identifier of the target user</td>', 'rst_description': 'Unique identifier of the target user\n', 'name': 'user_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Integer', 'required': False, 'description': 'Sequential number of the first photo to be returned. By default, all photos are returned.', 'html_description': '<td>Sequential number of the first photo to be returned. By default, all photos are returned.</td>', 'rst_description': 'Sequential number of the first photo to be returned. By default, all photos are returned.\n', 'name': 'offset', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Integer', 'required': False, 'description': 'Limits the number of photos to be retrieved. Values between 1-100 are accepted. Defaults to 100.', 'html_description': '<td>Limits the number of photos to be retrieved. Values between 1-100 are accepted. Defaults to 100.</td>', 'rst_description': 'Limits the number of photos to be retrieved. Values between 1-100 are accepted. Defaults to 100.\n', 'name': 'limit', 'parsed_type': {'type': 'std', 'name': 'int'}}], 'category': 'methods', 'returning': {'type': 'UserProfilePhotos', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'UserProfilePhotos'}}, 'description': 'Returns a UserProfilePhotos object.'}, 'bases': ['TelegramMethod']}

        :param user_id: Unique identifier of the target user
        :param offset: Sequential number of the first photo to be returned. By default, all photos are returned.
        :param limit: Limits the number of photos to be retrieved. Values between 1-100 are accepted. Defaults to 100.
        :param request_timeout: Request timeout
        :return: Returns a :class:`aiogram.types.user_profile_photos.UserProfilePhotos` object.
        """

        call = GetUserProfilePhotos(
            user_id=user_id,
            offset=offset,
            limit=limit,
        )
        return await self(call, request_timeout=request_timeout)

    async def get_webhook_info(
        self,
        request_timeout: Optional[int] = None,
    ) -> WebhookInfo:
        """
        Use this method to get current webhook status. Requires no parameters. On success, returns a :class:`aiogram.types.webhook_info.WebhookInfo` object. If the bot is using :class:`aiogram.methods.get_updates.GetUpdates`, will return an object with the *url* field empty.

        Source: https://core.telegram.org/bots/api#{'anchor': 'getwebhookinfo', 'name': 'getWebhookInfo', 'description': 'Use this method to get current webhook status. Requires no parameters. On success, returns a WebhookInfo object. If the bot is using getUpdates, will return an object with the url field empty.', 'html_description': '<p>Use this method to get current webhook status. Requires no parameters. On success, returns a <a href="#webhookinfo">WebhookInfo</a> object. If the bot is using <a href="#getupdates">getUpdates</a>, will return an object with the <em>url</em> field empty.</p>', 'rst_description': 'Use this method to get current webhook status. Requires no parameters. On success, returns a :class:`aiogram.types.webhook_info.WebhookInfo` object. If the bot is using :class:`aiogram.methods.get_updates.GetUpdates`, will return an object with the *url* field empty.', 'annotations': [], 'category': 'methods', 'returning': {'type': 'WebhookInfo', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'WebhookInfo'}}, 'description': 'On success, returns a WebhookInfo object. If the bot is using getUpdates, will return an object with the url field empty.'}, 'bases': ['TelegramMethod']}

        :param request_timeout: Request timeout
        :return: If the bot is using :class:`aiogram.methods.get_updates.GetUpdates`, will return an object with the *url* field empty.
        """

        call = GetWebhookInfo()
        return await self(call, request_timeout=request_timeout)

    async def leave_chat(
        self,
        chat_id: Union[int, str],
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method for your bot to leave a group, supergroup or channel. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'leavechat', 'name': 'leaveChat', 'description': 'Use this method for your bot to leave a group, supergroup or channel. Returns True on success.', 'html_description': '<p>Use this method for your bot to leave a group, supergroup or channel. Returns <em>True</em> on success.</p>', 'rst_description': 'Use this method for your bot to leave a group, supergroup or channel. Returns :code:`True` on success.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target supergroup or channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target supergroup or channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target supergroup or channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel (in the format :code:`@channelusername`)
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = LeaveChat(
            chat_id=chat_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def log_out(
        self,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to log out from the cloud Bot API server before launching the bot locally. You **must** log out the bot before running it locally, otherwise there is no guarantee that the bot will receive updates. After a successful call, you can immediately log in on a local server, but will not be able to log in back to the cloud Bot API server for 10 minutes. Returns :code:`True` on success. Requires no parameters.

        Source: https://core.telegram.org/bots/api#{'anchor': 'logout', 'name': 'logOut', 'description': 'Use this method to log out from the cloud Bot API server before launching the bot locally. You must log out the bot before running it locally, otherwise there is no guarantee that the bot will receive updates. After a successful call, you can immediately log in on a local server, but will not be able to log in back to the cloud Bot API server for 10 minutes. Returns True on success. Requires no parameters.', 'html_description': '<p>Use this method to log out from the cloud Bot API server before launching the bot locally. You <strong>must</strong> log out the bot before running it locally, otherwise there is no guarantee that the bot will receive updates. After a successful call, you can immediately log in on a local server, but will not be able to log in back to the cloud Bot API server for 10 minutes. Returns <em>True</em> on success. Requires no parameters.</p>', 'rst_description': 'Use this method to log out from the cloud Bot API server before launching the bot locally. You **must** log out the bot before running it locally, otherwise there is no guarantee that the bot will receive updates. After a successful call, you can immediately log in on a local server, but will not be able to log in back to the cloud Bot API server for 10 minutes. Returns :code:`True` on success. Requires no parameters.', 'annotations': [], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param request_timeout: Request timeout
        :return: Requires no parameters.
        """

        call = LogOut()
        return await self(call, request_timeout=request_timeout)

    async def pin_chat_message(
        self,
        chat_id: Union[int, str],
        message_id: int,
        disable_notification: Optional[bool] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to add a message to the list of pinned messages in a chat. If the chat is not a private chat, the bot must be an administrator in the chat for this to work and must have the 'can_pin_messages' administrator right in a supergroup or 'can_edit_messages' administrator right in a channel. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'pinchatmessage', 'name': 'pinChatMessage', 'description': "Use this method to add a message to the list of pinned messages in a chat. If the chat is not a private chat, the bot must be an administrator in the chat for this to work and must have the 'can_pin_messages' administrator right in a supergroup or 'can_edit_messages' administrator right in a channel. Returns True on success.", 'html_description': "<p>Use this method to add a message to the list of pinned messages in a chat. If the chat is not a private chat, the bot must be an administrator in the chat for this to work and must have the 'can_pin_messages' administrator right in a supergroup or 'can_edit_messages' administrator right in a channel. Returns <em>True</em> on success.</p>", 'rst_description': "Use this method to add a message to the list of pinned messages in a chat. If the chat is not a private chat, the bot must be an administrator in the chat for this to work and must have the 'can_pin_messages' administrator right in a supergroup or 'can_edit_messages' administrator right in a channel. Returns :code:`True` on success.", 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': True, 'description': 'Identifier of a message to pin', 'html_description': '<td>Identifier of a message to pin</td>', 'rst_description': 'Identifier of a message to pin\n', 'name': 'message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if it is not necessary to send a notification to all chat members about the new pinned message. Notifications are always disabled in channels and private chats.', 'html_description': '<td>Pass <em>True</em> if it is not necessary to send a notification to all chat members about the new pinned message. Notifications are always disabled in channels and private chats.</td>', 'rst_description': 'Pass :code:`True` if it is not necessary to send a notification to all chat members about the new pinned message. Notifications are always disabled in channels and private chats.\n', 'name': 'disable_notification', 'parsed_type': {'type': 'std', 'name': 'bool'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param message_id: Identifier of a message to pin
        :param disable_notification: Pass :code:`True` if it is not necessary to send a notification to all chat members about the new pinned message. Notifications are always disabled in channels and private chats.
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = PinChatMessage(
            chat_id=chat_id,
            message_id=message_id,
            disable_notification=disable_notification,
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
        can_manage_video_chats: Optional[bool] = None,
        can_restrict_members: Optional[bool] = None,
        can_promote_members: Optional[bool] = None,
        can_change_info: Optional[bool] = None,
        can_invite_users: Optional[bool] = None,
        can_pin_messages: Optional[bool] = None,
        can_manage_topics: Optional[bool] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to promote or demote a user in a supergroup or a channel. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Pass :code:`False` for all boolean parameters to demote a user. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'promotechatmember', 'name': 'promoteChatMember', 'description': 'Use this method to promote or demote a user in a supergroup or a channel. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Pass False for all boolean parameters to demote a user. Returns True on success.', 'html_description': '<p>Use this method to promote or demote a user in a supergroup or a channel. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Pass <em>False</em> for all boolean parameters to demote a user. Returns <em>True</em> on success.</p>', 'rst_description': 'Use this method to promote or demote a user in a supergroup or a channel. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Pass :code:`False` for all boolean parameters to demote a user. Returns :code:`True` on success.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': True, 'description': 'Unique identifier of the target user', 'html_description': '<td>Unique identifier of the target user</td>', 'rst_description': 'Unique identifier of the target user\n', 'name': 'user_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': "Pass True if the administrator's presence in the chat is hidden", 'html_description': "<td>Pass <em>True</em> if the administrator's presence in the chat is hidden</td>", 'rst_description': "Pass :code:`True` if the administrator's presence in the chat is hidden\n", 'name': 'is_anonymous', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the administrator can access the chat event log, chat statistics, message statistics in channels, see channel members, see anonymous administrators in supergroups and ignore slow mode. Implied by any other administrator privilege', 'html_description': '<td>Pass <em>True</em> if the administrator can access the chat event log, chat statistics, message statistics in channels, see channel members, see anonymous administrators in supergroups and ignore slow mode. Implied by any other administrator privilege</td>', 'rst_description': 'Pass :code:`True` if the administrator can access the chat event log, chat statistics, message statistics in channels, see channel members, see anonymous administrators in supergroups and ignore slow mode. Implied by any other administrator privilege\n', 'name': 'can_manage_chat', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the administrator can create channel posts, channels only', 'html_description': '<td>Pass <em>True</em> if the administrator can create channel posts, channels only</td>', 'rst_description': 'Pass :code:`True` if the administrator can create channel posts, channels only\n', 'name': 'can_post_messages', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the administrator can edit messages of other users and can pin messages, channels only', 'html_description': '<td>Pass <em>True</em> if the administrator can edit messages of other users and can pin messages, channels only</td>', 'rst_description': 'Pass :code:`True` if the administrator can edit messages of other users and can pin messages, channels only\n', 'name': 'can_edit_messages', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the administrator can delete messages of other users', 'html_description': '<td>Pass <em>True</em> if the administrator can delete messages of other users</td>', 'rst_description': 'Pass :code:`True` if the administrator can delete messages of other users\n', 'name': 'can_delete_messages', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the administrator can manage video chats', 'html_description': '<td>Pass <em>True</em> if the administrator can manage video chats</td>', 'rst_description': 'Pass :code:`True` if the administrator can manage video chats\n', 'name': 'can_manage_video_chats', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the administrator can restrict, ban or unban chat members', 'html_description': '<td>Pass <em>True</em> if the administrator can restrict, ban or unban chat members</td>', 'rst_description': 'Pass :code:`True` if the administrator can restrict, ban or unban chat members\n', 'name': 'can_restrict_members', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the administrator can add new administrators with a subset of their own privileges or demote administrators that they have promoted, directly or indirectly (promoted by administrators that were appointed by him)', 'html_description': '<td>Pass <em>True</em> if the administrator can add new administrators with a subset of their own privileges or demote administrators that they have promoted, directly or indirectly (promoted by administrators that were appointed by him)</td>', 'rst_description': 'Pass :code:`True` if the administrator can add new administrators with a subset of their own privileges or demote administrators that they have promoted, directly or indirectly (promoted by administrators that were appointed by him)\n', 'name': 'can_promote_members', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the administrator can change chat title, photo and other settings', 'html_description': '<td>Pass <em>True</em> if the administrator can change chat title, photo and other settings</td>', 'rst_description': 'Pass :code:`True` if the administrator can change chat title, photo and other settings\n', 'name': 'can_change_info', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the administrator can invite new users to the chat', 'html_description': '<td>Pass <em>True</em> if the administrator can invite new users to the chat</td>', 'rst_description': 'Pass :code:`True` if the administrator can invite new users to the chat\n', 'name': 'can_invite_users', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the administrator can pin messages, supergroups only', 'html_description': '<td>Pass <em>True</em> if the administrator can pin messages, supergroups only</td>', 'rst_description': 'Pass :code:`True` if the administrator can pin messages, supergroups only\n', 'name': 'can_pin_messages', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the user is allowed to create, rename, close, and reopen forum topics, supergroups only', 'html_description': '<td>Pass <em>True</em> if the user is allowed to create, rename, close, and reopen forum topics, supergroups only</td>', 'rst_description': 'Pass :code:`True` if the user is allowed to create, rename, close, and reopen forum topics, supergroups only\n', 'name': 'can_manage_topics', 'parsed_type': {'type': 'std', 'name': 'bool'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param user_id: Unique identifier of the target user
        :param is_anonymous: Pass :code:`True` if the administrator's presence in the chat is hidden
        :param can_manage_chat: Pass :code:`True` if the administrator can access the chat event log, chat statistics, message statistics in channels, see channel members, see anonymous administrators in supergroups and ignore slow mode. Implied by any other administrator privilege
        :param can_post_messages: Pass :code:`True` if the administrator can create channel posts, channels only
        :param can_edit_messages: Pass :code:`True` if the administrator can edit messages of other users and can pin messages, channels only
        :param can_delete_messages: Pass :code:`True` if the administrator can delete messages of other users
        :param can_manage_video_chats: Pass :code:`True` if the administrator can manage video chats
        :param can_restrict_members: Pass :code:`True` if the administrator can restrict, ban or unban chat members
        :param can_promote_members: Pass :code:`True` if the administrator can add new administrators with a subset of their own privileges or demote administrators that they have promoted, directly or indirectly (promoted by administrators that were appointed by him)
        :param can_change_info: Pass :code:`True` if the administrator can change chat title, photo and other settings
        :param can_invite_users: Pass :code:`True` if the administrator can invite new users to the chat
        :param can_pin_messages: Pass :code:`True` if the administrator can pin messages, supergroups only
        :param can_manage_topics: Pass :code:`True` if the user is allowed to create, rename, close, and reopen forum topics, supergroups only
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = PromoteChatMember(
            chat_id=chat_id,
            user_id=user_id,
            is_anonymous=is_anonymous,
            can_manage_chat=can_manage_chat,
            can_post_messages=can_post_messages,
            can_edit_messages=can_edit_messages,
            can_delete_messages=can_delete_messages,
            can_manage_video_chats=can_manage_video_chats,
            can_restrict_members=can_restrict_members,
            can_promote_members=can_promote_members,
            can_change_info=can_change_info,
            can_invite_users=can_invite_users,
            can_pin_messages=can_pin_messages,
            can_manage_topics=can_manage_topics,
        )
        return await self(call, request_timeout=request_timeout)

    async def reopen_forum_topic(
        self,
        chat_id: Union[int, str],
        message_thread_id: int,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to reopen a closed topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the *can_manage_topics* administrator rights, unless it is the creator of the topic. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'reopenforumtopic', 'name': 'reopenForumTopic', 'description': 'Use this method to reopen a closed topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the can_manage_topics administrator rights, unless it is the creator of the topic. Returns True on success.', 'html_description': '<p>Use this method to reopen a closed topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the <em>can_manage_topics</em> administrator rights, unless it is the creator of the topic. Returns <em>True</em> on success.</p>', 'rst_description': 'Use this method to reopen a closed topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the *can_manage_topics* administrator rights, unless it is the creator of the topic. Returns :code:`True` on success.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target supergroup (in the format @supergroupusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target supergroup (in the format <code>@supergroupusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': True, 'description': 'Unique identifier for the target message thread of the forum topic', 'html_description': '<td>Unique identifier for the target message thread of the forum topic</td>', 'rst_description': 'Unique identifier for the target message thread of the forum topic\n', 'name': 'message_thread_id', 'parsed_type': {'type': 'std', 'name': 'int'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)
        :param message_thread_id: Unique identifier for the target message thread of the forum topic
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = ReopenForumTopic(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def restrict_chat_member(
        self,
        chat_id: Union[int, str],
        user_id: int,
        permissions: ChatPermissions,
        use_independent_chat_permissions: Optional[bool] = None,
        until_date: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to restrict a user in a supergroup. The bot must be an administrator in the supergroup for this to work and must have the appropriate administrator rights. Pass :code:`True` for all permissions to lift restrictions from a user. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'restrictchatmember', 'name': 'restrictChatMember', 'description': 'Use this method to restrict a user in a supergroup. The bot must be an administrator in the supergroup for this to work and must have the appropriate administrator rights. Pass True for all permissions to lift restrictions from a user. Returns True on success.', 'html_description': '<p>Use this method to restrict a user in a supergroup. The bot must be an administrator in the supergroup for this to work and must have the appropriate administrator rights. Pass <em>True</em> for all permissions to lift restrictions from a user. Returns <em>True</em> on success.</p>', 'rst_description': 'Use this method to restrict a user in a supergroup. The bot must be an administrator in the supergroup for this to work and must have the appropriate administrator rights. Pass :code:`True` for all permissions to lift restrictions from a user. Returns :code:`True` on success.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target supergroup (in the format @supergroupusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target supergroup (in the format <code>@supergroupusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': True, 'description': 'Unique identifier of the target user', 'html_description': '<td>Unique identifier of the target user</td>', 'rst_description': 'Unique identifier of the target user\n', 'name': 'user_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'ChatPermissions', 'required': True, 'description': 'A JSON-serialized object for new user permissions', 'html_description': '<td>A JSON-serialized object for new user permissions</td>', 'rst_description': 'A JSON-serialized object for new user permissions\n', 'name': 'permissions', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'ChatPermissions'}}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if chat permissions are set independently. Otherwise, the can_send_other_messages and can_add_web_page_previews permissions will imply the can_send_messages, can_send_audios, can_send_documents, can_send_photos, can_send_videos, can_send_video_notes, and can_send_voice_notes permissions; the can_send_polls permission will imply the can_send_messages permission.', 'html_description': '<td>Pass <em>True</em> if chat permissions are set independently. Otherwise, the <em>can_send_other_messages</em> and <em>can_add_web_page_previews</em> permissions will imply the <em>can_send_messages</em>, <em>can_send_audios</em>, <em>can_send_documents</em>, <em>can_send_photos</em>, <em>can_send_videos</em>, <em>can_send_video_notes</em>, and <em>can_send_voice_notes</em> permissions; the <em>can_send_polls</em> permission will imply the <em>can_send_messages</em> permission.</td>', 'rst_description': 'Pass :code:`True` if chat permissions are set independently. Otherwise, the *can_send_other_messages* and *can_add_web_page_previews* permissions will imply the *can_send_messages*, *can_send_audios*, *can_send_documents*, *can_send_photos*, *can_send_videos*, *can_send_video_notes*, and *can_send_voice_notes* permissions; the *can_send_polls* permission will imply the *can_send_messages* permission.\n', 'name': 'use_independent_chat_permissions', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Integer', 'required': False, 'description': 'Date when restrictions will be lifted for the user, unix time. If user is restricted for more than 366 days or less than 30 seconds from the current time, they are considered to be restricted forever', 'html_description': '<td>Date when restrictions will be lifted for the user, unix time. If user is restricted for more than 366 days or less than 30 seconds from the current time, they are considered to be restricted forever</td>', 'rst_description': 'Date when restrictions will be lifted for the user, unix time. If user is restricted for more than 366 days or less than 30 seconds from the current time, they are considered to be restricted forever\n', 'name': 'until_date', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'datetime.datetime'}, {'type': 'std', 'name': 'datetime.timedelta'}, {'type': 'std', 'name': 'int'}]}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)
        :param user_id: Unique identifier of the target user
        :param permissions: A JSON-serialized object for new user permissions
        :param use_independent_chat_permissions: Pass :code:`True` if chat permissions are set independently. Otherwise, the *can_send_other_messages* and *can_add_web_page_previews* permissions will imply the *can_send_messages*, *can_send_audios*, *can_send_documents*, *can_send_photos*, *can_send_videos*, *can_send_video_notes*, and *can_send_voice_notes* permissions; the *can_send_polls* permission will imply the *can_send_messages* permission.
        :param until_date: Date when restrictions will be lifted for the user, unix time. If user is restricted for more than 366 days or less than 30 seconds from the current time, they are considered to be restricted forever
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = RestrictChatMember(
            chat_id=chat_id,
            user_id=user_id,
            permissions=permissions,
            use_independent_chat_permissions=use_independent_chat_permissions,
            until_date=until_date,
        )
        return await self(call, request_timeout=request_timeout)

    async def revoke_chat_invite_link(
        self,
        chat_id: Union[int, str],
        invite_link: str,
        request_timeout: Optional[int] = None,
    ) -> ChatInviteLink:
        """
        Use this method to revoke an invite link created by the bot. If the primary link is revoked, a new link is automatically generated. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns the revoked invite link as :class:`aiogram.types.chat_invite_link.ChatInviteLink` object.

        Source: https://core.telegram.org/bots/api#{'anchor': 'revokechatinvitelink', 'name': 'revokeChatInviteLink', 'description': 'Use this method to revoke an invite link created by the bot. If the primary link is revoked, a new link is automatically generated. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns the revoked invite link as ChatInviteLink object.', 'html_description': '<p>Use this method to revoke an invite link created by the bot. If the primary link is revoked, a new link is automatically generated. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns the revoked invite link as <a href="#chatinvitelink">ChatInviteLink</a> object.</p>', 'rst_description': 'Use this method to revoke an invite link created by the bot. If the primary link is revoked, a new link is automatically generated. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns the revoked invite link as :class:`aiogram.types.chat_invite_link.ChatInviteLink` object.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier of the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier of the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier of the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'String', 'required': True, 'description': 'The invite link to revoke', 'html_description': '<td>The invite link to revoke</td>', 'rst_description': 'The invite link to revoke\n', 'name': 'invite_link', 'parsed_type': {'type': 'std', 'name': 'str'}}], 'category': 'methods', 'returning': {'type': 'ChatInviteLink', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'ChatInviteLink'}}, 'description': 'Returns the revoked invite link as ChatInviteLink object.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier of the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param invite_link: The invite link to revoke
        :param request_timeout: Request timeout
        :return: Returns the revoked invite link as :class:`aiogram.types.chat_invite_link.ChatInviteLink` object.
        """

        call = RevokeChatInviteLink(
            chat_id=chat_id,
            invite_link=invite_link,
        )
        return await self(call, request_timeout=request_timeout)

    async def send_animation(
        self,
        chat_id: Union[int, str],
        animation: Union[InputFile, str],
        message_thread_id: Optional[int] = None,
        duration: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        thumb: Optional[Union[InputFile, str]] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET,
        caption_entities: Optional[List[MessageEntity]] = None,
        has_spoiler: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        Use this method to send animation files (GIF or H.264/MPEG-4 AVC video without sound). On success, the sent :class:`aiogram.types.message.Message` is returned. Bots can currently send animation files of up to 50 MB in size, this limit may be changed in the future.

        Source: https://core.telegram.org/bots/api#{'anchor': 'sendanimation', 'name': 'sendAnimation', 'description': 'Use this method to send animation files (GIF or H.264/MPEG-4 AVC video without sound). On success, the sent Message is returned. Bots can currently send animation files of up to 50 MB in size, this limit may be changed in the future.', 'html_description': '<p>Use this method to send animation files (GIF or H.264/MPEG-4 AVC video without sound). On success, the sent <a href="#message">Message</a> is returned. Bots can currently send animation files of up to 50 MB in size, this limit may be changed in the future.</p>', 'rst_description': 'Use this method to send animation files (GIF or H.264/MPEG-4 AVC video without sound). On success, the sent :class:`aiogram.types.message.Message` is returned. Bots can currently send animation files of up to 50 MB in size, this limit may be changed in the future.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'InputFile or String', 'required': True, 'description': 'Animation to send. Pass a file_id as String to send an animation that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get an animation from the Internet, or upload a new animation using multipart/form-data. More information on Sending Files', 'html_description': '<td>Animation to send. Pass a file_id as String to send an animation that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get an animation from the Internet, or upload a new animation using multipart/form-data. <a href="#sending-files">More information on Sending Files &#187;</a></td>', 'rst_description': 'Animation to send. Pass a file_id as String to send an animation that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get an animation from the Internet, or upload a new animation using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`\n', 'name': 'animation', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InputFile'}}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': False, 'description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only', 'html_description': '<td>Unique identifier for the target message thread (topic) of the forum; for forum supergroups only</td>', 'rst_description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only\n', 'name': 'message_thread_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Integer', 'required': False, 'description': 'Duration of sent animation in seconds', 'html_description': '<td>Duration of sent animation in seconds</td>', 'rst_description': 'Duration of sent animation in seconds\n', 'name': 'duration', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Integer', 'required': False, 'description': 'Animation width', 'html_description': '<td>Animation width</td>', 'rst_description': 'Animation width\n', 'name': 'width', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Integer', 'required': False, 'description': 'Animation height', 'html_description': '<td>Animation height</td>', 'rst_description': 'Animation height\n', 'name': 'height', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'InputFile or String', 'required': False, 'description': "Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. More information on Sending Files", 'html_description': '<td>Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail\'s width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can\'t be reused and can be only uploaded as a new file, so you can pass &#8220;attach://&lt;file_attach_name&gt;&#8221; if the thumbnail was uploaded using multipart/form-data under &lt;file_attach_name&gt;. <a href="#sending-files">More information on Sending Files &#187;</a></td>', 'rst_description': "Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. :ref:`More information on Sending Files » <sending-files>`\n", 'name': 'thumb', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InputFile'}}, {'type': 'std', 'name': 'str'}]}}, {'type': 'String', 'required': False, 'description': 'Animation caption (may also be used when resending animation by file_id), 0-1024 characters after entities parsing', 'html_description': '<td>Animation caption (may also be used when resending animation by <em>file_id</em>), 0-1024 characters after entities parsing</td>', 'rst_description': 'Animation caption (may also be used when resending animation by *file_id*), 0-1024 characters after entities parsing\n', 'name': 'caption', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': False, 'description': 'Mode for parsing entities in the animation caption. See formatting options for more details.', 'html_description': '<td>Mode for parsing entities in the animation caption. See <a href="#formatting-options">formatting options</a> for more details.</td>', 'rst_description': 'Mode for parsing entities in the animation caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.\n', 'name': 'parse_mode', 'parsed_type': {'type': 'std', 'name': 'str'}, 'value': 'UNSET'}, {'type': 'Array of MessageEntity', 'required': False, 'description': 'A JSON-serialized list of special entities that appear in the caption, which can be specified instead of parse_mode', 'html_description': '<td>A JSON-serialized list of special entities that appear in the caption, which can be specified instead of <em>parse_mode</em></td>', 'rst_description': 'A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*\n', 'name': 'caption_entities', 'parsed_type': {'type': 'array', 'items': {'type': 'entity', 'references': {'category': 'types', 'name': 'MessageEntity'}}}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the animation needs to be covered with a spoiler animation', 'html_description': '<td>Pass <em>True</em> if the animation needs to be covered with a spoiler animation</td>', 'rst_description': 'Pass :code:`True` if the animation needs to be covered with a spoiler animation\n', 'name': 'has_spoiler', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Sends the message silently. Users will receive a notification with no sound.', 'html_description': '<td>Sends the message <a href="https://telegram.org/blog/channels-2-0#silent-messages">silently</a>. Users will receive a notification with no sound.</td>', 'rst_description': 'Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.\n', 'name': 'disable_notification', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Protects the contents of the sent message from forwarding and saving', 'html_description': '<td>Protects the contents of the sent message from forwarding and saving</td>', 'rst_description': 'Protects the contents of the sent message from forwarding and saving\n', 'name': 'protect_content', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Integer', 'required': False, 'description': 'If the message is a reply, ID of the original message', 'html_description': '<td>If the message is a reply, ID of the original message</td>', 'rst_description': 'If the message is a reply, ID of the original message\n', 'name': 'reply_to_message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the message should be sent even if the specified replied-to message is not found', 'html_description': '<td>Pass <em>True</em> if the message should be sent even if the specified replied-to message is not found</td>', 'rst_description': 'Pass :code:`True` if the message should be sent even if the specified replied-to message is not found\n', 'name': 'allow_sending_without_reply', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply', 'required': False, 'description': 'Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.', 'html_description': '<td>Additional interface options. A JSON-serialized object for an <a href="/bots/features#inline-keyboards">inline keyboard</a>, <a href="/bots/features#keyboards">custom reply keyboard</a>, instructions to remove reply keyboard or to force a reply from the user.</td>', 'rst_description': 'Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.\n', 'name': 'reply_markup', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InlineKeyboardMarkup'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ReplyKeyboardMarkup'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ReplyKeyboardRemove'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ForceReply'}}]}}], 'category': 'methods', 'returning': {'type': 'Message', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'Message'}}, 'description': 'On success, the sent Message is returned.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param animation: Animation to send. Pass a file_id as String to send an animation that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get an animation from the Internet, or upload a new animation using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`
        :param message_thread_id: Unique identifier for the target message thread (topic) of the forum; for forum supergroups only
        :param duration: Duration of sent animation in seconds
        :param width: Animation width
        :param height: Animation height
        :param thumb: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. :ref:`More information on Sending Files » <sending-files>`
        :param caption: Animation caption (may also be used when resending animation by *file_id*), 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the animation caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*
        :param has_spoiler: Pass :code:`True` if the animation needs to be covered with a spoiler animation
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.
        :param request_timeout: Request timeout
        :return: Bots can currently send animation files of up to 50 MB in size, this limit may be changed in the future.
        """

        call = SendAnimation(
            chat_id=chat_id,
            animation=animation,
            message_thread_id=message_thread_id,
            duration=duration,
            width=width,
            height=height,
            thumb=thumb,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            has_spoiler=has_spoiler,
            disable_notification=disable_notification,
            protect_content=protect_content,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def send_audio(
        self,
        chat_id: Union[int, str],
        audio: Union[InputFile, str],
        message_thread_id: Optional[int] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET,
        caption_entities: Optional[List[MessageEntity]] = None,
        duration: Optional[int] = None,
        performer: Optional[str] = None,
        title: Optional[str] = None,
        thumb: Optional[Union[InputFile, str]] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
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

        Source: https://core.telegram.org/bots/api#{'anchor': 'sendaudio', 'name': 'sendAudio', 'description': 'Use this method to send audio files, if you want Telegram clients to display them in the music player. Your audio must be in the .MP3 or .M4A format. On success, the sent Message is returned. Bots can currently send audio files of up to 50 MB in size, this limit may be changed in the future.\nFor sending voice messages, use the sendVoice method instead.', 'html_description': '<p>Use this method to send audio files, if you want Telegram clients to display them in the music player. Your audio must be in the .MP3 or .M4A format. On success, the sent <a href="#message">Message</a> is returned. Bots can currently send audio files of up to 50 MB in size, this limit may be changed in the future.</p><p>For sending voice messages, use the <a href="#sendvoice">sendVoice</a> method instead.</p>', 'rst_description': 'Use this method to send audio files, if you want Telegram clients to display them in the music player. Your audio must be in the .MP3 or .M4A format. On success, the sent :class:`aiogram.types.message.Message` is returned. Bots can currently send audio files of up to 50 MB in size, this limit may be changed in the future.\nFor sending voice messages, use the :class:`aiogram.methods.send_voice.SendVoice` method instead.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'InputFile or String', 'required': True, 'description': 'Audio file to send. Pass a file_id as String to send an audio file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get an audio file from the Internet, or upload a new one using multipart/form-data. More information on Sending Files', 'html_description': '<td>Audio file to send. Pass a file_id as String to send an audio file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get an audio file from the Internet, or upload a new one using multipart/form-data. <a href="#sending-files">More information on Sending Files &#187;</a></td>', 'rst_description': 'Audio file to send. Pass a file_id as String to send an audio file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get an audio file from the Internet, or upload a new one using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`\n', 'name': 'audio', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InputFile'}}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': False, 'description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only', 'html_description': '<td>Unique identifier for the target message thread (topic) of the forum; for forum supergroups only</td>', 'rst_description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only\n', 'name': 'message_thread_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'String', 'required': False, 'description': 'Audio caption, 0-1024 characters after entities parsing', 'html_description': '<td>Audio caption, 0-1024 characters after entities parsing</td>', 'rst_description': 'Audio caption, 0-1024 characters after entities parsing\n', 'name': 'caption', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': False, 'description': 'Mode for parsing entities in the audio caption. See formatting options for more details.', 'html_description': '<td>Mode for parsing entities in the audio caption. See <a href="#formatting-options">formatting options</a> for more details.</td>', 'rst_description': 'Mode for parsing entities in the audio caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.\n', 'name': 'parse_mode', 'parsed_type': {'type': 'std', 'name': 'str'}, 'value': 'UNSET'}, {'type': 'Array of MessageEntity', 'required': False, 'description': 'A JSON-serialized list of special entities that appear in the caption, which can be specified instead of parse_mode', 'html_description': '<td>A JSON-serialized list of special entities that appear in the caption, which can be specified instead of <em>parse_mode</em></td>', 'rst_description': 'A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*\n', 'name': 'caption_entities', 'parsed_type': {'type': 'array', 'items': {'type': 'entity', 'references': {'category': 'types', 'name': 'MessageEntity'}}}}, {'type': 'Integer', 'required': False, 'description': 'Duration of the audio in seconds', 'html_description': '<td>Duration of the audio in seconds</td>', 'rst_description': 'Duration of the audio in seconds\n', 'name': 'duration', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'String', 'required': False, 'description': 'Performer', 'html_description': '<td>Performer</td>', 'rst_description': 'Performer\n', 'name': 'performer', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': False, 'description': 'Track name', 'html_description': '<td>Track name</td>', 'rst_description': 'Track name\n', 'name': 'title', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'InputFile or String', 'required': False, 'description': "Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. More information on Sending Files", 'html_description': '<td>Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail\'s width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can\'t be reused and can be only uploaded as a new file, so you can pass &#8220;attach://&lt;file_attach_name&gt;&#8221; if the thumbnail was uploaded using multipart/form-data under &lt;file_attach_name&gt;. <a href="#sending-files">More information on Sending Files &#187;</a></td>', 'rst_description': "Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. :ref:`More information on Sending Files » <sending-files>`\n", 'name': 'thumb', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InputFile'}}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Boolean', 'required': False, 'description': 'Sends the message silently. Users will receive a notification with no sound.', 'html_description': '<td>Sends the message <a href="https://telegram.org/blog/channels-2-0#silent-messages">silently</a>. Users will receive a notification with no sound.</td>', 'rst_description': 'Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.\n', 'name': 'disable_notification', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Protects the contents of the sent message from forwarding and saving', 'html_description': '<td>Protects the contents of the sent message from forwarding and saving</td>', 'rst_description': 'Protects the contents of the sent message from forwarding and saving\n', 'name': 'protect_content', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Integer', 'required': False, 'description': 'If the message is a reply, ID of the original message', 'html_description': '<td>If the message is a reply, ID of the original message</td>', 'rst_description': 'If the message is a reply, ID of the original message\n', 'name': 'reply_to_message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the message should be sent even if the specified replied-to message is not found', 'html_description': '<td>Pass <em>True</em> if the message should be sent even if the specified replied-to message is not found</td>', 'rst_description': 'Pass :code:`True` if the message should be sent even if the specified replied-to message is not found\n', 'name': 'allow_sending_without_reply', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply', 'required': False, 'description': 'Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.', 'html_description': '<td>Additional interface options. A JSON-serialized object for an <a href="/bots/features#inline-keyboards">inline keyboard</a>, <a href="/bots/features#keyboards">custom reply keyboard</a>, instructions to remove reply keyboard or to force a reply from the user.</td>', 'rst_description': 'Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.\n', 'name': 'reply_markup', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InlineKeyboardMarkup'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ReplyKeyboardMarkup'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ReplyKeyboardRemove'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ForceReply'}}]}}], 'category': 'methods', 'returning': {'type': 'Message', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'Message'}}, 'description': 'On success, the sent Message is returned.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param audio: Audio file to send. Pass a file_id as String to send an audio file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get an audio file from the Internet, or upload a new one using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`
        :param message_thread_id: Unique identifier for the target message thread (topic) of the forum; for forum supergroups only
        :param caption: Audio caption, 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the audio caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*
        :param duration: Duration of the audio in seconds
        :param performer: Performer
        :param title: Track name
        :param thumb: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. :ref:`More information on Sending Files » <sending-files>`
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.
        :param request_timeout: Request timeout
        :return: Bots can currently send audio files of up to 50 MB in size, this limit may be changed in the future.
        """

        call = SendAudio(
            chat_id=chat_id,
            audio=audio,
            message_thread_id=message_thread_id,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            duration=duration,
            performer=performer,
            title=title,
            thumb=thumb,
            disable_notification=disable_notification,
            protect_content=protect_content,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def send_chat_action(
        self,
        chat_id: Union[int, str],
        action: str,
        message_thread_id: Optional[int] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method when you need to tell the user that something is happening on the bot's side. The status is set for 5 seconds or less (when a message arrives from your bot, Telegram clients clear its typing status). Returns :code:`True` on success.

         Example: The `ImageBot <https://t.me/imagebot>`_ needs some time to process a request and upload the image. Instead of sending a text message along the lines of 'Retrieving image, please wait…', the bot may use :class:`aiogram.methods.send_chat_action.SendChatAction` with *action* = *upload_photo*. The user will see a 'sending photo' status for the bot.

        We only recommend using this method when a response from the bot will take a **noticeable** amount of time to arrive.

        Source: https://core.telegram.org/bots/api#{'anchor': 'sendchataction', 'name': 'sendChatAction', 'description': "Use this method when you need to tell the user that something is happening on the bot's side. The status is set for 5 seconds or less (when a message arrives from your bot, Telegram clients clear its typing status). Returns True on success.\nExample: The ImageBot needs some time to process a request and upload the image. Instead of sending a text message along the lines of 'Retrieving image, please wait…', the bot may use sendChatAction with action = upload_photo. The user will see a 'sending photo' status for the bot.\nWe only recommend using this method when a response from the bot will take a noticeable amount of time to arrive.", 'html_description': '<p>Use this method when you need to tell the user that something is happening on the bot\'s side. The status is set for 5 seconds or less (when a message arrives from your bot, Telegram clients clear its typing status). Returns <em>True</em> on success.</p><blockquote>\n<p>Example: The <a href="https://t.me/imagebot">ImageBot</a> needs some time to process a request and upload the image. Instead of sending a text message along the lines of &#8220;Retrieving image, please wait&#8230;&#8221;, the bot may use <a href="#sendchataction">sendChatAction</a> with <em>action</em> = <em>upload_photo</em>. The user will see a &#8220;sending photo&#8221; status for the bot.</p>\n</blockquote><p>We only recommend using this method when a response from the bot will take a <strong>noticeable</strong> amount of time to arrive.</p>', 'rst_description': "Use this method when you need to tell the user that something is happening on the bot's side. The status is set for 5 seconds or less (when a message arrives from your bot, Telegram clients clear its typing status). Returns :code:`True` on success.\n\n Example: The `ImageBot <https://t.me/imagebot>`_ needs some time to process a request and upload the image. Instead of sending a text message along the lines of 'Retrieving image, please wait…', the bot may use :class:`aiogram.methods.send_chat_action.SendChatAction` with *action* = *upload_photo*. The user will see a 'sending photo' status for the bot.\n\nWe only recommend using this method when a response from the bot will take a **noticeable** amount of time to arrive.", 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'String', 'required': True, 'description': 'Type of action to broadcast. Choose one, depending on what the user is about to receive: typing for text messages, upload_photo for photos, record_video or upload_video for videos, record_voice or upload_voice for voice notes, upload_document for general files, choose_sticker for stickers, find_location for location data, record_video_note or upload_video_note for video notes.', 'html_description': '<td>Type of action to broadcast. Choose one, depending on what the user is about to receive: <em>typing</em> for <a href="#sendmessage">text messages</a>, <em>upload_photo</em> for <a href="#sendphoto">photos</a>, <em>record_video</em> or <em>upload_video</em> for <a href="#sendvideo">videos</a>, <em>record_voice</em> or <em>upload_voice</em> for <a href="#sendvoice">voice notes</a>, <em>upload_document</em> for <a href="#senddocument">general files</a>, <em>choose_sticker</em> for <a href="#sendsticker">stickers</a>, <em>find_location</em> for <a href="#sendlocation">location data</a>, <em>record_video_note</em> or <em>upload_video_note</em> for <a href="#sendvideonote">video notes</a>.</td>', 'rst_description': 'Type of action to broadcast. Choose one, depending on what the user is about to receive: *typing* for `text messages <https://core.telegram.org/bots/api#sendmessage>`_, *upload_photo* for `photos <https://core.telegram.org/bots/api#sendphoto>`_, *record_video* or *upload_video* for `videos <https://core.telegram.org/bots/api#sendvideo>`_, *record_voice* or *upload_voice* for `voice notes <https://core.telegram.org/bots/api#sendvoice>`_, *upload_document* for `general files <https://core.telegram.org/bots/api#senddocument>`_, *choose_sticker* for `stickers <https://core.telegram.org/bots/api#sendsticker>`_, *find_location* for `location data <https://core.telegram.org/bots/api#sendlocation>`_, *record_video_note* or *upload_video_note* for `video notes <https://core.telegram.org/bots/api#sendvideonote>`_.\n', 'name': 'action', 'enum_value': 'ChatAction.UPLOAD_VIDEO_NOTE', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'Integer', 'required': False, 'description': 'Unique identifier for the target message thread; supergroups only', 'html_description': '<td>Unique identifier for the target message thread; supergroups only</td>', 'rst_description': 'Unique identifier for the target message thread; supergroups only\n', 'name': 'message_thread_id', 'parsed_type': {'type': 'std', 'name': 'int'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param action: Type of action to broadcast. Choose one, depending on what the user is about to receive: *typing* for `text messages <https://core.telegram.org/bots/api#sendmessage>`_, *upload_photo* for `photos <https://core.telegram.org/bots/api#sendphoto>`_, *record_video* or *upload_video* for `videos <https://core.telegram.org/bots/api#sendvideo>`_, *record_voice* or *upload_voice* for `voice notes <https://core.telegram.org/bots/api#sendvoice>`_, *upload_document* for `general files <https://core.telegram.org/bots/api#senddocument>`_, *choose_sticker* for `stickers <https://core.telegram.org/bots/api#sendsticker>`_, *find_location* for `location data <https://core.telegram.org/bots/api#sendlocation>`_, *record_video_note* or *upload_video_note* for `video notes <https://core.telegram.org/bots/api#sendvideonote>`_.
        :param message_thread_id: Unique identifier for the target message thread; supergroups only
        :param request_timeout: Request timeout
        :return: The user will see a 'sending photo' status for the bot.
        """

        call = SendChatAction(
            chat_id=chat_id,
            action=action,
            message_thread_id=message_thread_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def send_contact(
        self,
        chat_id: Union[int, str],
        phone_number: str,
        first_name: str,
        message_thread_id: Optional[int] = None,
        last_name: Optional[str] = None,
        vcard: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        Use this method to send phone contacts. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#{'anchor': 'sendcontact', 'name': 'sendContact', 'description': 'Use this method to send phone contacts. On success, the sent Message is returned.', 'html_description': '<p>Use this method to send phone contacts. On success, the sent <a href="#message">Message</a> is returned.</p>', 'rst_description': 'Use this method to send phone contacts. On success, the sent :class:`aiogram.types.message.Message` is returned.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'String', 'required': True, 'description': "Contact's phone number", 'html_description': "<td>Contact's phone number</td>", 'rst_description': "Contact's phone number\n", 'name': 'phone_number', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': True, 'description': "Contact's first name", 'html_description': "<td>Contact's first name</td>", 'rst_description': "Contact's first name\n", 'name': 'first_name', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'Integer', 'required': False, 'description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only', 'html_description': '<td>Unique identifier for the target message thread (topic) of the forum; for forum supergroups only</td>', 'rst_description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only\n', 'name': 'message_thread_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'String', 'required': False, 'description': "Contact's last name", 'html_description': "<td>Contact's last name</td>", 'rst_description': "Contact's last name\n", 'name': 'last_name', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': False, 'description': 'Additional data about the contact in the form of a vCard, 0-2048 bytes', 'html_description': '<td>Additional data about the contact in the form of a <a href="https://en.wikipedia.org/wiki/VCard">vCard</a>, 0-2048 bytes</td>', 'rst_description': 'Additional data about the contact in the form of a `vCard <https://en.wikipedia.org/wiki/VCard>`_, 0-2048 bytes\n', 'name': 'vcard', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'Boolean', 'required': False, 'description': 'Sends the message silently. Users will receive a notification with no sound.', 'html_description': '<td>Sends the message <a href="https://telegram.org/blog/channels-2-0#silent-messages">silently</a>. Users will receive a notification with no sound.</td>', 'rst_description': 'Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.\n', 'name': 'disable_notification', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Protects the contents of the sent message from forwarding and saving', 'html_description': '<td>Protects the contents of the sent message from forwarding and saving</td>', 'rst_description': 'Protects the contents of the sent message from forwarding and saving\n', 'name': 'protect_content', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Integer', 'required': False, 'description': 'If the message is a reply, ID of the original message', 'html_description': '<td>If the message is a reply, ID of the original message</td>', 'rst_description': 'If the message is a reply, ID of the original message\n', 'name': 'reply_to_message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the message should be sent even if the specified replied-to message is not found', 'html_description': '<td>Pass <em>True</em> if the message should be sent even if the specified replied-to message is not found</td>', 'rst_description': 'Pass :code:`True` if the message should be sent even if the specified replied-to message is not found\n', 'name': 'allow_sending_without_reply', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply', 'required': False, 'description': 'Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.', 'html_description': '<td>Additional interface options. A JSON-serialized object for an <a href="/bots/features#inline-keyboards">inline keyboard</a>, <a href="/bots/features#keyboards">custom reply keyboard</a>, instructions to remove reply keyboard or to force a reply from the user.</td>', 'rst_description': 'Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.\n', 'name': 'reply_markup', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InlineKeyboardMarkup'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ReplyKeyboardMarkup'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ReplyKeyboardRemove'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ForceReply'}}]}}], 'category': 'methods', 'returning': {'type': 'Message', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'Message'}}, 'description': 'On success, the sent Message is returned.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param phone_number: Contact's phone number
        :param first_name: Contact's first name
        :param message_thread_id: Unique identifier for the target message thread (topic) of the forum; for forum supergroups only
        :param last_name: Contact's last name
        :param vcard: Additional data about the contact in the form of a `vCard <https://en.wikipedia.org/wiki/VCard>`_, 0-2048 bytes
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.
        :param request_timeout: Request timeout
        :return: On success, the sent :class:`aiogram.types.message.Message` is returned.
        """

        call = SendContact(
            chat_id=chat_id,
            phone_number=phone_number,
            first_name=first_name,
            message_thread_id=message_thread_id,
            last_name=last_name,
            vcard=vcard,
            disable_notification=disable_notification,
            protect_content=protect_content,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def send_dice(
        self,
        chat_id: Union[int, str],
        message_thread_id: Optional[int] = None,
        emoji: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        Use this method to send an animated emoji that will display a random value. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#{'anchor': 'senddice', 'name': 'sendDice', 'description': 'Use this method to send an animated emoji that will display a random value. On success, the sent Message is returned.', 'html_description': '<p>Use this method to send an animated emoji that will display a random value. On success, the sent <a href="#message">Message</a> is returned.</p>', 'rst_description': 'Use this method to send an animated emoji that will display a random value. On success, the sent :class:`aiogram.types.message.Message` is returned.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': False, 'description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only', 'html_description': '<td>Unique identifier for the target message thread (topic) of the forum; for forum supergroups only</td>', 'rst_description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only\n', 'name': 'message_thread_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'String', 'required': False, 'description': "Emoji on which the dice throw animation is based. Currently, must be one of '', '', '', '', '', or ''. Dice can have values 1-6 for '', '' and '', values 1-5 for '' and '', and values 1-64 for ''. Defaults to ''", 'html_description': '<td>Emoji on which the dice throw animation is based. Currently, must be one of &#8220;<img class="emoji" src="//telegram.org/img/emoji/40/F09F8EB2.png" width="20" height="20" alt="&#127922;"/>&#8221;, &#8220;<img class="emoji" src="//telegram.org/img/emoji/40/F09F8EAF.png" width="20" height="20" alt="&#127919;"/>&#8221;, &#8220;<img class="emoji" src="//telegram.org/img/emoji/40/F09F8F80.png" width="20" height="20" alt="&#127936;"/>&#8221;, &#8220;<img class="emoji" src="//telegram.org/img/emoji/40/E29ABD.png" width="20" height="20" alt="&#9917;"/>&#8221;, &#8220;<img class="emoji" src="//telegram.org/img/emoji/40/F09F8EB3.png" width="20" height="20" alt="&#127923;"/>&#8221;, or &#8220;<img class="emoji" src="//telegram.org/img/emoji/40/F09F8EB0.png" width="20" height="20" alt="&#127920;"/>&#8221;. Dice can have values 1-6 for &#8220;<img class="emoji" src="//telegram.org/img/emoji/40/F09F8EB2.png" width="20" height="20" alt="&#127922;"/>&#8221;, &#8220;<img class="emoji" src="//telegram.org/img/emoji/40/F09F8EAF.png" width="20" height="20" alt="&#127919;"/>&#8221; and &#8220;<img class="emoji" src="//telegram.org/img/emoji/40/F09F8EB3.png" width="20" height="20" alt="&#127923;"/>&#8221;, values 1-5 for &#8220;<img class="emoji" src="//telegram.org/img/emoji/40/F09F8F80.png" width="20" height="20" alt="&#127936;"/>&#8221; and &#8220;<img class="emoji" src="//telegram.org/img/emoji/40/E29ABD.png" width="20" height="20" alt="&#9917;"/>&#8221;, and values 1-64 for &#8220;<img class="emoji" src="//telegram.org/img/emoji/40/F09F8EB0.png" width="20" height="20" alt="&#127920;"/>&#8221;. Defaults to &#8220;<img class="emoji" src="//telegram.org/img/emoji/40/F09F8EB2.png" width="20" height="20" alt="&#127922;"/>&#8221;</td>', 'rst_description': "Emoji on which the dice throw animation is based. Currently, must be one of '🎲', '🎯', '🏀', '⚽', '🎳', or '🎰'. Dice can have values 1-6 for '🎲', '🎯' and '🎳', values 1-5 for '🏀' and '⚽', and values 1-64 for '🎰'. Defaults to '🎲'\n", 'name': 'emoji', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'Boolean', 'required': False, 'description': 'Sends the message silently. Users will receive a notification with no sound.', 'html_description': '<td>Sends the message <a href="https://telegram.org/blog/channels-2-0#silent-messages">silently</a>. Users will receive a notification with no sound.</td>', 'rst_description': 'Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.\n', 'name': 'disable_notification', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Protects the contents of the sent message from forwarding', 'html_description': '<td>Protects the contents of the sent message from forwarding</td>', 'rst_description': 'Protects the contents of the sent message from forwarding\n', 'name': 'protect_content', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Integer', 'required': False, 'description': 'If the message is a reply, ID of the original message', 'html_description': '<td>If the message is a reply, ID of the original message</td>', 'rst_description': 'If the message is a reply, ID of the original message\n', 'name': 'reply_to_message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the message should be sent even if the specified replied-to message is not found', 'html_description': '<td>Pass <em>True</em> if the message should be sent even if the specified replied-to message is not found</td>', 'rst_description': 'Pass :code:`True` if the message should be sent even if the specified replied-to message is not found\n', 'name': 'allow_sending_without_reply', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply', 'required': False, 'description': 'Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.', 'html_description': '<td>Additional interface options. A JSON-serialized object for an <a href="/bots/features#inline-keyboards">inline keyboard</a>, <a href="/bots/features#keyboards">custom reply keyboard</a>, instructions to remove reply keyboard or to force a reply from the user.</td>', 'rst_description': 'Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.\n', 'name': 'reply_markup', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InlineKeyboardMarkup'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ReplyKeyboardMarkup'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ReplyKeyboardRemove'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ForceReply'}}]}}], 'category': 'methods', 'returning': {'type': 'Message', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'Message'}}, 'description': 'On success, the sent Message is returned.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param message_thread_id: Unique identifier for the target message thread (topic) of the forum; for forum supergroups only
        :param emoji: Emoji on which the dice throw animation is based. Currently, must be one of '🎲', '🎯', '🏀', '⚽', '🎳', or '🎰'. Dice can have values 1-6 for '🎲', '🎯' and '🎳', values 1-5 for '🏀' and '⚽', and values 1-64 for '🎰'. Defaults to '🎲'
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.
        :param request_timeout: Request timeout
        :return: On success, the sent :class:`aiogram.types.message.Message` is returned.
        """

        call = SendDice(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            emoji=emoji,
            disable_notification=disable_notification,
            protect_content=protect_content,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def send_document(
        self,
        chat_id: Union[int, str],
        document: Union[InputFile, str],
        message_thread_id: Optional[int] = None,
        thumb: Optional[Union[InputFile, str]] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET,
        caption_entities: Optional[List[MessageEntity]] = None,
        disable_content_type_detection: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        Use this method to send general files. On success, the sent :class:`aiogram.types.message.Message` is returned. Bots can currently send files of any type of up to 50 MB in size, this limit may be changed in the future.

        Source: https://core.telegram.org/bots/api#{'anchor': 'senddocument', 'name': 'sendDocument', 'description': 'Use this method to send general files. On success, the sent Message is returned. Bots can currently send files of any type of up to 50 MB in size, this limit may be changed in the future.', 'html_description': '<p>Use this method to send general files. On success, the sent <a href="#message">Message</a> is returned. Bots can currently send files of any type of up to 50 MB in size, this limit may be changed in the future.</p>', 'rst_description': 'Use this method to send general files. On success, the sent :class:`aiogram.types.message.Message` is returned. Bots can currently send files of any type of up to 50 MB in size, this limit may be changed in the future.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'InputFile or String', 'required': True, 'description': 'File to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. More information on Sending Files', 'html_description': '<td>File to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. <a href="#sending-files">More information on Sending Files &#187;</a></td>', 'rst_description': 'File to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`\n', 'name': 'document', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InputFile'}}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': False, 'description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only', 'html_description': '<td>Unique identifier for the target message thread (topic) of the forum; for forum supergroups only</td>', 'rst_description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only\n', 'name': 'message_thread_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'InputFile or String', 'required': False, 'description': "Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. More information on Sending Files", 'html_description': '<td>Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail\'s width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can\'t be reused and can be only uploaded as a new file, so you can pass &#8220;attach://&lt;file_attach_name&gt;&#8221; if the thumbnail was uploaded using multipart/form-data under &lt;file_attach_name&gt;. <a href="#sending-files">More information on Sending Files &#187;</a></td>', 'rst_description': "Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. :ref:`More information on Sending Files » <sending-files>`\n", 'name': 'thumb', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InputFile'}}, {'type': 'std', 'name': 'str'}]}}, {'type': 'String', 'required': False, 'description': 'Document caption (may also be used when resending documents by file_id), 0-1024 characters after entities parsing', 'html_description': '<td>Document caption (may also be used when resending documents by <em>file_id</em>), 0-1024 characters after entities parsing</td>', 'rst_description': 'Document caption (may also be used when resending documents by *file_id*), 0-1024 characters after entities parsing\n', 'name': 'caption', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': False, 'description': 'Mode for parsing entities in the document caption. See formatting options for more details.', 'html_description': '<td>Mode for parsing entities in the document caption. See <a href="#formatting-options">formatting options</a> for more details.</td>', 'rst_description': 'Mode for parsing entities in the document caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.\n', 'name': 'parse_mode', 'parsed_type': {'type': 'std', 'name': 'str'}, 'value': 'UNSET'}, {'type': 'Array of MessageEntity', 'required': False, 'description': 'A JSON-serialized list of special entities that appear in the caption, which can be specified instead of parse_mode', 'html_description': '<td>A JSON-serialized list of special entities that appear in the caption, which can be specified instead of <em>parse_mode</em></td>', 'rst_description': 'A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*\n', 'name': 'caption_entities', 'parsed_type': {'type': 'array', 'items': {'type': 'entity', 'references': {'category': 'types', 'name': 'MessageEntity'}}}}, {'type': 'Boolean', 'required': False, 'description': 'Disables automatic server-side content type detection for files uploaded using multipart/form-data', 'html_description': '<td>Disables automatic server-side content type detection for files uploaded using multipart/form-data</td>', 'rst_description': 'Disables automatic server-side content type detection for files uploaded using multipart/form-data\n', 'name': 'disable_content_type_detection', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Sends the message silently. Users will receive a notification with no sound.', 'html_description': '<td>Sends the message <a href="https://telegram.org/blog/channels-2-0#silent-messages">silently</a>. Users will receive a notification with no sound.</td>', 'rst_description': 'Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.\n', 'name': 'disable_notification', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Protects the contents of the sent message from forwarding and saving', 'html_description': '<td>Protects the contents of the sent message from forwarding and saving</td>', 'rst_description': 'Protects the contents of the sent message from forwarding and saving\n', 'name': 'protect_content', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Integer', 'required': False, 'description': 'If the message is a reply, ID of the original message', 'html_description': '<td>If the message is a reply, ID of the original message</td>', 'rst_description': 'If the message is a reply, ID of the original message\n', 'name': 'reply_to_message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the message should be sent even if the specified replied-to message is not found', 'html_description': '<td>Pass <em>True</em> if the message should be sent even if the specified replied-to message is not found</td>', 'rst_description': 'Pass :code:`True` if the message should be sent even if the specified replied-to message is not found\n', 'name': 'allow_sending_without_reply', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply', 'required': False, 'description': 'Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.', 'html_description': '<td>Additional interface options. A JSON-serialized object for an <a href="/bots/features#inline-keyboards">inline keyboard</a>, <a href="/bots/features#keyboards">custom reply keyboard</a>, instructions to remove reply keyboard or to force a reply from the user.</td>', 'rst_description': 'Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.\n', 'name': 'reply_markup', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InlineKeyboardMarkup'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ReplyKeyboardMarkup'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ReplyKeyboardRemove'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ForceReply'}}]}}], 'category': 'methods', 'returning': {'type': 'Message', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'Message'}}, 'description': 'On success, the sent Message is returned.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param document: File to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`
        :param message_thread_id: Unique identifier for the target message thread (topic) of the forum; for forum supergroups only
        :param thumb: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. :ref:`More information on Sending Files » <sending-files>`
        :param caption: Document caption (may also be used when resending documents by *file_id*), 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the document caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*
        :param disable_content_type_detection: Disables automatic server-side content type detection for files uploaded using multipart/form-data
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.
        :param request_timeout: Request timeout
        :return: Bots can currently send files of any type of up to 50 MB in size, this limit may be changed in the future.
        """

        call = SendDocument(
            chat_id=chat_id,
            document=document,
            message_thread_id=message_thread_id,
            thumb=thumb,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            disable_content_type_detection=disable_content_type_detection,
            disable_notification=disable_notification,
            protect_content=protect_content,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def send_game(
        self,
        chat_id: int,
        game_short_name: str,
        message_thread_id: Optional[int] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        Use this method to send a game. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#{'anchor': 'sendgame', 'name': 'sendGame', 'description': 'Use this method to send a game. On success, the sent Message is returned.', 'html_description': '<p>Use this method to send a game. On success, the sent <a href="#message">Message</a> is returned.</p>', 'rst_description': 'Use this method to send a game. On success, the sent :class:`aiogram.types.message.Message` is returned.', 'annotations': [{'type': 'Integer', 'required': True, 'description': 'Unique identifier for the target chat', 'html_description': '<td>Unique identifier for the target chat</td>', 'rst_description': 'Unique identifier for the target chat\n', 'name': 'chat_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'String', 'required': True, 'description': 'Short name of the game, serves as the unique identifier for the game. Set up your games via @BotFather.', 'html_description': '<td>Short name of the game, serves as the unique identifier for the game. Set up your games via <a href="https://t.me/botfather">@BotFather</a>.</td>', 'rst_description': 'Short name of the game, serves as the unique identifier for the game. Set up your games via `@BotFather <https://t.me/botfather>`_.\n', 'name': 'game_short_name', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'Integer', 'required': False, 'description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only', 'html_description': '<td>Unique identifier for the target message thread (topic) of the forum; for forum supergroups only</td>', 'rst_description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only\n', 'name': 'message_thread_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': 'Sends the message silently. Users will receive a notification with no sound.', 'html_description': '<td>Sends the message <a href="https://telegram.org/blog/channels-2-0#silent-messages">silently</a>. Users will receive a notification with no sound.</td>', 'rst_description': 'Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.\n', 'name': 'disable_notification', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Protects the contents of the sent message from forwarding and saving', 'html_description': '<td>Protects the contents of the sent message from forwarding and saving</td>', 'rst_description': 'Protects the contents of the sent message from forwarding and saving\n', 'name': 'protect_content', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Integer', 'required': False, 'description': 'If the message is a reply, ID of the original message', 'html_description': '<td>If the message is a reply, ID of the original message</td>', 'rst_description': 'If the message is a reply, ID of the original message\n', 'name': 'reply_to_message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the message should be sent even if the specified replied-to message is not found', 'html_description': '<td>Pass <em>True</em> if the message should be sent even if the specified replied-to message is not found</td>', 'rst_description': 'Pass :code:`True` if the message should be sent even if the specified replied-to message is not found\n', 'name': 'allow_sending_without_reply', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'InlineKeyboardMarkup', 'required': False, 'description': "A JSON-serialized object for an inline keyboard. If empty, one 'Play game_title' button will be shown. If not empty, the first button must launch the game.", 'html_description': '<td>A JSON-serialized object for an <a href="/bots/features#inline-keyboards">inline keyboard</a>. If empty, one \'Play game_title\' button will be shown. If not empty, the first button must launch the game.</td>', 'rst_description': "A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_. If empty, one 'Play game_title' button will be shown. If not empty, the first button must launch the game.\n", 'name': 'reply_markup', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'InlineKeyboardMarkup'}}}], 'category': 'methods', 'returning': {'type': 'Message', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'Message'}}, 'description': 'On success, the sent Message is returned.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat
        :param game_short_name: Short name of the game, serves as the unique identifier for the game. Set up your games via `@BotFather <https://t.me/botfather>`_.
        :param message_thread_id: Unique identifier for the target message thread (topic) of the forum; for forum supergroups only
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_. If empty, one 'Play game_title' button will be shown. If not empty, the first button must launch the game.
        :param request_timeout: Request timeout
        :return: On success, the sent :class:`aiogram.types.message.Message` is returned.
        """

        call = SendGame(
            chat_id=chat_id,
            game_short_name=game_short_name,
            message_thread_id=message_thread_id,
            disable_notification=disable_notification,
            protect_content=protect_content,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def send_invoice(
        self,
        chat_id: Union[int, str],
        title: str,
        description: str,
        payload: str,
        provider_token: str,
        currency: str,
        prices: List[LabeledPrice],
        message_thread_id: Optional[int] = None,
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
        protect_content: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        Use this method to send invoices. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#{'anchor': 'sendinvoice', 'name': 'sendInvoice', 'description': 'Use this method to send invoices. On success, the sent Message is returned.', 'html_description': '<p>Use this method to send invoices. On success, the sent <a href="#message">Message</a> is returned.</p>', 'rst_description': 'Use this method to send invoices. On success, the sent :class:`aiogram.types.message.Message` is returned.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'String', 'required': True, 'description': 'Product name, 1-32 characters', 'html_description': '<td>Product name, 1-32 characters</td>', 'rst_description': 'Product name, 1-32 characters\n', 'name': 'title', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': True, 'description': 'Product description, 1-255 characters', 'html_description': '<td>Product description, 1-255 characters</td>', 'rst_description': 'Product description, 1-255 characters\n', 'name': 'description', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': True, 'description': 'Bot-defined invoice payload, 1-128 bytes. This will not be displayed to the user, use for your internal processes.', 'html_description': '<td>Bot-defined invoice payload, 1-128 bytes. This will not be displayed to the user, use for your internal processes.</td>', 'rst_description': 'Bot-defined invoice payload, 1-128 bytes. This will not be displayed to the user, use for your internal processes.\n', 'name': 'payload', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': True, 'description': 'Payment provider token, obtained via @BotFather', 'html_description': '<td>Payment provider token, obtained via <a href="https://t.me/botfather">@BotFather</a></td>', 'rst_description': 'Payment provider token, obtained via `@BotFather <https://t.me/botfather>`_\n', 'name': 'provider_token', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': True, 'description': 'Three-letter ISO 4217 currency code, see more on currencies', 'html_description': '<td>Three-letter ISO 4217 currency code, see <a href="/bots/payments#supported-currencies">more on currencies</a></td>', 'rst_description': 'Three-letter ISO 4217 currency code, see `more on currencies <https://core.telegram.org/bots/payments#supported-currencies>`_\n', 'name': 'currency', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'Array of LabeledPrice', 'required': True, 'description': 'Price breakdown, a JSON-serialized list of components (e.g. product price, tax, discount, delivery cost, delivery tax, bonus, etc.)', 'html_description': '<td>Price breakdown, a JSON-serialized list of components (e.g. product price, tax, discount, delivery cost, delivery tax, bonus, etc.)</td>', 'rst_description': 'Price breakdown, a JSON-serialized list of components (e.g. product price, tax, discount, delivery cost, delivery tax, bonus, etc.)\n', 'name': 'prices', 'parsed_type': {'type': 'array', 'items': {'type': 'entity', 'references': {'category': 'types', 'name': 'LabeledPrice'}}}}, {'type': 'Integer', 'required': False, 'description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only', 'html_description': '<td>Unique identifier for the target message thread (topic) of the forum; for forum supergroups only</td>', 'rst_description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only\n', 'name': 'message_thread_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Integer', 'required': False, 'description': 'The maximum accepted amount for tips in the smallest units of the currency (integer, not float/double). For example, for a maximum tip of US$ 1.45 pass max_tip_amount = 145. See the exp parameter in currencies.json, it shows the number of digits past the decimal point for each currency (2 for the majority of currencies). Defaults to 0', 'html_description': '<td>The maximum accepted amount for tips in the <em>smallest units</em> of the currency (integer, <strong>not</strong> float/double). For example, for a maximum tip of <code>US$ 1.45</code> pass <code>max_tip_amount = 145</code>. See the <em>exp</em> parameter in <a href="/bots/payments/currencies.json">currencies.json</a>, it shows the number of digits past the decimal point for each currency (2 for the majority of currencies). Defaults to 0</td>', 'rst_description': 'The maximum accepted amount for tips in the *smallest units* of the currency (integer, **not** float/double). For example, for a maximum tip of :code:`US$ 1.45` pass :code:`max_tip_amount = 145`. See the *exp* parameter in `currencies.json <https://core.telegram.org/bots/payments/currencies.json>`_, it shows the number of digits past the decimal point for each currency (2 for the majority of currencies). Defaults to 0\n', 'name': 'max_tip_amount', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Array of Integer', 'required': False, 'description': 'A JSON-serialized array of suggested amounts of tips in the smallest units of the currency (integer, not float/double). At most 4 suggested tip amounts can be specified. The suggested tip amounts must be positive, passed in a strictly increased order and must not exceed max_tip_amount.', 'html_description': '<td>A JSON-serialized array of suggested amounts of tips in the <em>smallest units</em> of the currency (integer, <strong>not</strong> float/double). At most 4 suggested tip amounts can be specified. The suggested tip amounts must be positive, passed in a strictly increased order and must not exceed <em>max_tip_amount</em>.</td>', 'rst_description': 'A JSON-serialized array of suggested amounts of tips in the *smallest units* of the currency (integer, **not** float/double). At most 4 suggested tip amounts can be specified. The suggested tip amounts must be positive, passed in a strictly increased order and must not exceed *max_tip_amount*.\n', 'name': 'suggested_tip_amounts', 'parsed_type': {'type': 'array', 'items': {'type': 'std', 'name': 'int'}}}, {'type': 'String', 'required': False, 'description': 'Unique deep-linking parameter. If left empty, forwarded copies of the sent message will have a Pay button, allowing multiple users to pay directly from the forwarded message, using the same invoice. If non-empty, forwarded copies of the sent message will have a URL button with a deep link to the bot (instead of a Pay button), with the value used as the start parameter', 'html_description': '<td>Unique deep-linking parameter. If left empty, <strong>forwarded copies</strong> of the sent message will have a <em>Pay</em> button, allowing multiple users to pay directly from the forwarded message, using the same invoice. If non-empty, forwarded copies of the sent message will have a <em>URL</em> button with a deep link to the bot (instead of a <em>Pay</em> button), with the value used as the start parameter</td>', 'rst_description': 'Unique deep-linking parameter. If left empty, **forwarded copies** of the sent message will have a *Pay* button, allowing multiple users to pay directly from the forwarded message, using the same invoice. If non-empty, forwarded copies of the sent message will have a *URL* button with a deep link to the bot (instead of a *Pay* button), with the value used as the start parameter\n', 'name': 'start_parameter', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': False, 'description': 'JSON-serialized data about the invoice, which will be shared with the payment provider. A detailed description of required fields should be provided by the payment provider.', 'html_description': '<td>JSON-serialized data about the invoice, which will be shared with the payment provider. A detailed description of required fields should be provided by the payment provider.</td>', 'rst_description': 'JSON-serialized data about the invoice, which will be shared with the payment provider. A detailed description of required fields should be provided by the payment provider.\n', 'name': 'provider_data', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': False, 'description': 'URL of the product photo for the invoice. Can be a photo of the goods or a marketing image for a service. People like it better when they see what they are paying for.', 'html_description': '<td>URL of the product photo for the invoice. Can be a photo of the goods or a marketing image for a service. People like it better when they see what they are paying for.</td>', 'rst_description': 'URL of the product photo for the invoice. Can be a photo of the goods or a marketing image for a service. People like it better when they see what they are paying for.\n', 'name': 'photo_url', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'Integer', 'required': False, 'description': 'Photo size in bytes', 'html_description': '<td>Photo size in bytes</td>', 'rst_description': 'Photo size in bytes\n', 'name': 'photo_size', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Integer', 'required': False, 'description': 'Photo width', 'html_description': '<td>Photo width</td>', 'rst_description': 'Photo width\n', 'name': 'photo_width', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Integer', 'required': False, 'description': 'Photo height', 'html_description': '<td>Photo height</td>', 'rst_description': 'Photo height\n', 'name': 'photo_height', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': "Pass True if you require the user's full name to complete the order", 'html_description': "<td>Pass <em>True</em> if you require the user's full name to complete the order</td>", 'rst_description': "Pass :code:`True` if you require the user's full name to complete the order\n", 'name': 'need_name', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': "Pass True if you require the user's phone number to complete the order", 'html_description': "<td>Pass <em>True</em> if you require the user's phone number to complete the order</td>", 'rst_description': "Pass :code:`True` if you require the user's phone number to complete the order\n", 'name': 'need_phone_number', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': "Pass True if you require the user's email address to complete the order", 'html_description': "<td>Pass <em>True</em> if you require the user's email address to complete the order</td>", 'rst_description': "Pass :code:`True` if you require the user's email address to complete the order\n", 'name': 'need_email', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': "Pass True if you require the user's shipping address to complete the order", 'html_description': "<td>Pass <em>True</em> if you require the user's shipping address to complete the order</td>", 'rst_description': "Pass :code:`True` if you require the user's shipping address to complete the order\n", 'name': 'need_shipping_address', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': "Pass True if the user's phone number should be sent to provider", 'html_description': "<td>Pass <em>True</em> if the user's phone number should be sent to provider</td>", 'rst_description': "Pass :code:`True` if the user's phone number should be sent to provider\n", 'name': 'send_phone_number_to_provider', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': "Pass True if the user's email address should be sent to provider", 'html_description': "<td>Pass <em>True</em> if the user's email address should be sent to provider</td>", 'rst_description': "Pass :code:`True` if the user's email address should be sent to provider\n", 'name': 'send_email_to_provider', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the final price depends on the shipping method', 'html_description': '<td>Pass <em>True</em> if the final price depends on the shipping method</td>', 'rst_description': 'Pass :code:`True` if the final price depends on the shipping method\n', 'name': 'is_flexible', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Sends the message silently. Users will receive a notification with no sound.', 'html_description': '<td>Sends the message <a href="https://telegram.org/blog/channels-2-0#silent-messages">silently</a>. Users will receive a notification with no sound.</td>', 'rst_description': 'Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.\n', 'name': 'disable_notification', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Protects the contents of the sent message from forwarding and saving', 'html_description': '<td>Protects the contents of the sent message from forwarding and saving</td>', 'rst_description': 'Protects the contents of the sent message from forwarding and saving\n', 'name': 'protect_content', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Integer', 'required': False, 'description': 'If the message is a reply, ID of the original message', 'html_description': '<td>If the message is a reply, ID of the original message</td>', 'rst_description': 'If the message is a reply, ID of the original message\n', 'name': 'reply_to_message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the message should be sent even if the specified replied-to message is not found', 'html_description': '<td>Pass <em>True</em> if the message should be sent even if the specified replied-to message is not found</td>', 'rst_description': 'Pass :code:`True` if the message should be sent even if the specified replied-to message is not found\n', 'name': 'allow_sending_without_reply', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'InlineKeyboardMarkup', 'required': False, 'description': "A JSON-serialized object for an inline keyboard. If empty, one 'Pay total price' button will be shown. If not empty, the first button must be a Pay button.", 'html_description': '<td>A JSON-serialized object for an <a href="/bots/features#inline-keyboards">inline keyboard</a>. If empty, one \'Pay <code>total price</code>\' button will be shown. If not empty, the first button must be a Pay button.</td>', 'rst_description': "A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_. If empty, one 'Pay :code:`total price`' button will be shown. If not empty, the first button must be a Pay button.\n", 'name': 'reply_markup', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'InlineKeyboardMarkup'}}}], 'category': 'methods', 'returning': {'type': 'Message', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'Message'}}, 'description': 'On success, the sent Message is returned.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param title: Product name, 1-32 characters
        :param description: Product description, 1-255 characters
        :param payload: Bot-defined invoice payload, 1-128 bytes. This will not be displayed to the user, use for your internal processes.
        :param provider_token: Payment provider token, obtained via `@BotFather <https://t.me/botfather>`_
        :param currency: Three-letter ISO 4217 currency code, see `more on currencies <https://core.telegram.org/bots/payments#supported-currencies>`_
        :param prices: Price breakdown, a JSON-serialized list of components (e.g. product price, tax, discount, delivery cost, delivery tax, bonus, etc.)
        :param message_thread_id: Unique identifier for the target message thread (topic) of the forum; for forum supergroups only
        :param max_tip_amount: The maximum accepted amount for tips in the *smallest units* of the currency (integer, **not** float/double). For example, for a maximum tip of :code:`US$ 1.45` pass :code:`max_tip_amount = 145`. See the *exp* parameter in `currencies.json <https://core.telegram.org/bots/payments/currencies.json>`_, it shows the number of digits past the decimal point for each currency (2 for the majority of currencies). Defaults to 0
        :param suggested_tip_amounts: A JSON-serialized array of suggested amounts of tips in the *smallest units* of the currency (integer, **not** float/double). At most 4 suggested tip amounts can be specified. The suggested tip amounts must be positive, passed in a strictly increased order and must not exceed *max_tip_amount*.
        :param start_parameter: Unique deep-linking parameter. If left empty, **forwarded copies** of the sent message will have a *Pay* button, allowing multiple users to pay directly from the forwarded message, using the same invoice. If non-empty, forwarded copies of the sent message will have a *URL* button with a deep link to the bot (instead of a *Pay* button), with the value used as the start parameter
        :param provider_data: JSON-serialized data about the invoice, which will be shared with the payment provider. A detailed description of required fields should be provided by the payment provider.
        :param photo_url: URL of the product photo for the invoice. Can be a photo of the goods or a marketing image for a service. People like it better when they see what they are paying for.
        :param photo_size: Photo size in bytes
        :param photo_width: Photo width
        :param photo_height: Photo height
        :param need_name: Pass :code:`True` if you require the user's full name to complete the order
        :param need_phone_number: Pass :code:`True` if you require the user's phone number to complete the order
        :param need_email: Pass :code:`True` if you require the user's email address to complete the order
        :param need_shipping_address: Pass :code:`True` if you require the user's shipping address to complete the order
        :param send_phone_number_to_provider: Pass :code:`True` if the user's phone number should be sent to provider
        :param send_email_to_provider: Pass :code:`True` if the user's email address should be sent to provider
        :param is_flexible: Pass :code:`True` if the final price depends on the shipping method
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_. If empty, one 'Pay :code:`total price`' button will be shown. If not empty, the first button must be a Pay button.
        :param request_timeout: Request timeout
        :return: On success, the sent :class:`aiogram.types.message.Message` is returned.
        """

        call = SendInvoice(
            chat_id=chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token=provider_token,
            currency=currency,
            prices=prices,
            message_thread_id=message_thread_id,
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
            protect_content=protect_content,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def send_location(
        self,
        chat_id: Union[int, str],
        latitude: float,
        longitude: float,
        message_thread_id: Optional[int] = None,
        horizontal_accuracy: Optional[float] = None,
        live_period: Optional[int] = None,
        heading: Optional[int] = None,
        proximity_alert_radius: Optional[int] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        Use this method to send point on the map. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#{'anchor': 'sendlocation', 'name': 'sendLocation', 'description': 'Use this method to send point on the map. On success, the sent Message is returned.', 'html_description': '<p>Use this method to send point on the map. On success, the sent <a href="#message">Message</a> is returned.</p>', 'rst_description': 'Use this method to send point on the map. On success, the sent :class:`aiogram.types.message.Message` is returned.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Float number', 'required': True, 'description': 'Latitude of the location', 'html_description': '<td>Latitude of the location</td>', 'rst_description': 'Latitude of the location\n', 'name': 'latitude', 'parsed_type': {'type': 'std', 'name': 'float'}}, {'type': 'Float number', 'required': True, 'description': 'Longitude of the location', 'html_description': '<td>Longitude of the location</td>', 'rst_description': 'Longitude of the location\n', 'name': 'longitude', 'parsed_type': {'type': 'std', 'name': 'float'}}, {'type': 'Integer', 'required': False, 'description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only', 'html_description': '<td>Unique identifier for the target message thread (topic) of the forum; for forum supergroups only</td>', 'rst_description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only\n', 'name': 'message_thread_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Float number', 'required': False, 'description': 'The radius of uncertainty for the location, measured in meters; 0-1500', 'html_description': '<td>The radius of uncertainty for the location, measured in meters; 0-1500</td>', 'rst_description': 'The radius of uncertainty for the location, measured in meters; 0-1500\n', 'name': 'horizontal_accuracy', 'parsed_type': {'type': 'std', 'name': 'float'}}, {'type': 'Integer', 'required': False, 'description': 'Period in seconds for which the location will be updated (see Live Locations, should be between 60 and 86400.', 'html_description': '<td>Period in seconds for which the location will be updated (see <a href="https://telegram.org/blog/live-locations">Live Locations</a>, should be between 60 and 86400.</td>', 'rst_description': 'Period in seconds for which the location will be updated (see `Live Locations <https://telegram.org/blog/live-locations>`_, should be between 60 and 86400.\n', 'name': 'live_period', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Integer', 'required': False, 'description': 'For live locations, a direction in which the user is moving, in degrees. Must be between 1 and 360 if specified.', 'html_description': '<td>For live locations, a direction in which the user is moving, in degrees. Must be between 1 and 360 if specified.</td>', 'rst_description': 'For live locations, a direction in which the user is moving, in degrees. Must be between 1 and 360 if specified.\n', 'name': 'heading', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Integer', 'required': False, 'description': 'For live locations, a maximum distance for proximity alerts about approaching another chat member, in meters. Must be between 1 and 100000 if specified.', 'html_description': '<td>For live locations, a maximum distance for proximity alerts about approaching another chat member, in meters. Must be between 1 and 100000 if specified.</td>', 'rst_description': 'For live locations, a maximum distance for proximity alerts about approaching another chat member, in meters. Must be between 1 and 100000 if specified.\n', 'name': 'proximity_alert_radius', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': 'Sends the message silently. Users will receive a notification with no sound.', 'html_description': '<td>Sends the message <a href="https://telegram.org/blog/channels-2-0#silent-messages">silently</a>. Users will receive a notification with no sound.</td>', 'rst_description': 'Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.\n', 'name': 'disable_notification', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Protects the contents of the sent message from forwarding and saving', 'html_description': '<td>Protects the contents of the sent message from forwarding and saving</td>', 'rst_description': 'Protects the contents of the sent message from forwarding and saving\n', 'name': 'protect_content', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Integer', 'required': False, 'description': 'If the message is a reply, ID of the original message', 'html_description': '<td>If the message is a reply, ID of the original message</td>', 'rst_description': 'If the message is a reply, ID of the original message\n', 'name': 'reply_to_message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the message should be sent even if the specified replied-to message is not found', 'html_description': '<td>Pass <em>True</em> if the message should be sent even if the specified replied-to message is not found</td>', 'rst_description': 'Pass :code:`True` if the message should be sent even if the specified replied-to message is not found\n', 'name': 'allow_sending_without_reply', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply', 'required': False, 'description': 'Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.', 'html_description': '<td>Additional interface options. A JSON-serialized object for an <a href="/bots/features#inline-keyboards">inline keyboard</a>, <a href="/bots/features#keyboards">custom reply keyboard</a>, instructions to remove reply keyboard or to force a reply from the user.</td>', 'rst_description': 'Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.\n', 'name': 'reply_markup', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InlineKeyboardMarkup'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ReplyKeyboardMarkup'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ReplyKeyboardRemove'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ForceReply'}}]}}], 'category': 'methods', 'returning': {'type': 'Message', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'Message'}}, 'description': 'On success, the sent Message is returned.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param latitude: Latitude of the location
        :param longitude: Longitude of the location
        :param message_thread_id: Unique identifier for the target message thread (topic) of the forum; for forum supergroups only
        :param horizontal_accuracy: The radius of uncertainty for the location, measured in meters; 0-1500
        :param live_period: Period in seconds for which the location will be updated (see `Live Locations <https://telegram.org/blog/live-locations>`_, should be between 60 and 86400.
        :param heading: For live locations, a direction in which the user is moving, in degrees. Must be between 1 and 360 if specified.
        :param proximity_alert_radius: For live locations, a maximum distance for proximity alerts about approaching another chat member, in meters. Must be between 1 and 100000 if specified.
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.
        :param request_timeout: Request timeout
        :return: On success, the sent :class:`aiogram.types.message.Message` is returned.
        """

        call = SendLocation(
            chat_id=chat_id,
            latitude=latitude,
            longitude=longitude,
            message_thread_id=message_thread_id,
            horizontal_accuracy=horizontal_accuracy,
            live_period=live_period,
            heading=heading,
            proximity_alert_radius=proximity_alert_radius,
            disable_notification=disable_notification,
            protect_content=protect_content,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def send_media_group(
        self,
        chat_id: Union[int, str],
        media: List[Union[InputMediaAudio, InputMediaDocument, InputMediaPhoto, InputMediaVideo]],
        message_thread_id: Optional[int] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        request_timeout: Optional[int] = None,
    ) -> List[Message]:
        """
        Use this method to send a group of photos, videos, documents or audios as an album. Documents and audio files can be only grouped in an album with messages of the same type. On success, an array of `Messages <https://core.telegram.org/bots/api#message>`_ that were sent is returned.

        Source: https://core.telegram.org/bots/api#{'anchor': 'sendmediagroup', 'name': 'sendMediaGroup', 'description': 'Use this method to send a group of photos, videos, documents or audios as an album. Documents and audio files can be only grouped in an album with messages of the same type. On success, an array of Messages that were sent is returned.', 'html_description': '<p>Use this method to send a group of photos, videos, documents or audios as an album. Documents and audio files can be only grouped in an album with messages of the same type. On success, an array of <a href="#message">Messages</a> that were sent is returned.</p>', 'rst_description': 'Use this method to send a group of photos, videos, documents or audios as an album. Documents and audio files can be only grouped in an album with messages of the same type. On success, an array of `Messages <https://core.telegram.org/bots/api#message>`_ that were sent is returned.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Array of InputMediaAudio, InputMediaDocument, InputMediaPhoto and InputMediaVideo', 'required': True, 'description': 'A JSON-serialized array describing messages to be sent, must include 2-10 items', 'html_description': '<td>A JSON-serialized array describing messages to be sent, must include 2-10 items</td>', 'rst_description': 'A JSON-serialized array describing messages to be sent, must include 2-10 items\n', 'name': 'media', 'parsed_type': {'type': 'array', 'items': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InputMediaAudio, InputMediaDocument, InputMediaPhoto'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'InputMediaVideo'}}]}}}, {'type': 'Integer', 'required': False, 'description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only', 'html_description': '<td>Unique identifier for the target message thread (topic) of the forum; for forum supergroups only</td>', 'rst_description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only\n', 'name': 'message_thread_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': 'Sends messages silently. Users will receive a notification with no sound.', 'html_description': '<td>Sends messages <a href="https://telegram.org/blog/channels-2-0#silent-messages">silently</a>. Users will receive a notification with no sound.</td>', 'rst_description': 'Sends messages `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.\n', 'name': 'disable_notification', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Protects the contents of the sent messages from forwarding and saving', 'html_description': '<td>Protects the contents of the sent messages from forwarding and saving</td>', 'rst_description': 'Protects the contents of the sent messages from forwarding and saving\n', 'name': 'protect_content', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Integer', 'required': False, 'description': 'If the messages are a reply, ID of the original message', 'html_description': '<td>If the messages are a reply, ID of the original message</td>', 'rst_description': 'If the messages are a reply, ID of the original message\n', 'name': 'reply_to_message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the message should be sent even if the specified replied-to message is not found', 'html_description': '<td>Pass <em>True</em> if the message should be sent even if the specified replied-to message is not found</td>', 'rst_description': 'Pass :code:`True` if the message should be sent even if the specified replied-to message is not found\n', 'name': 'allow_sending_without_reply', 'parsed_type': {'type': 'std', 'name': 'bool'}}], 'category': 'methods', 'returning': {'type': 'array of Message', 'parsed_type': {'type': 'array', 'items': {'type': 'entity', 'references': {'category': 'types', 'name': 'Message'}}}, 'description': 'On success, an array of Messages that were sent is returned.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param media: A JSON-serialized array describing messages to be sent, must include 2-10 items
        :param message_thread_id: Unique identifier for the target message thread (topic) of the forum; for forum supergroups only
        :param disable_notification: Sends messages `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent messages from forwarding and saving
        :param reply_to_message_id: If the messages are a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param request_timeout: Request timeout
        :return: On success, an array of `Messages <https://core.telegram.org/bots/api#message>`_ that were sent is returned.
        """

        call = SendMediaGroup(
            chat_id=chat_id,
            media=media,
            message_thread_id=message_thread_id,
            disable_notification=disable_notification,
            protect_content=protect_content,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
        )
        return await self(call, request_timeout=request_timeout)

    async def send_message(
        self,
        chat_id: Union[int, str],
        text: str,
        message_thread_id: Optional[int] = None,
        parse_mode: Optional[str] = UNSET,
        entities: Optional[List[MessageEntity]] = None,
        disable_web_page_preview: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        Use this method to send text messages. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#{'anchor': 'sendmessage', 'name': 'sendMessage', 'description': 'Use this method to send text messages. On success, the sent Message is returned.', 'html_description': '<p>Use this method to send text messages. On success, the sent <a href="#message">Message</a> is returned.</p>', 'rst_description': 'Use this method to send text messages. On success, the sent :class:`aiogram.types.message.Message` is returned.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'String', 'required': True, 'description': 'Text of the message to be sent, 1-4096 characters after entities parsing', 'html_description': '<td>Text of the message to be sent, 1-4096 characters after entities parsing</td>', 'rst_description': 'Text of the message to be sent, 1-4096 characters after entities parsing\n', 'name': 'text', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'Integer', 'required': False, 'description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only', 'html_description': '<td>Unique identifier for the target message thread (topic) of the forum; for forum supergroups only</td>', 'rst_description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only\n', 'name': 'message_thread_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'String', 'required': False, 'description': 'Mode for parsing entities in the message text. See formatting options for more details.', 'html_description': '<td>Mode for parsing entities in the message text. See <a href="#formatting-options">formatting options</a> for more details.</td>', 'rst_description': 'Mode for parsing entities in the message text. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.\n', 'name': 'parse_mode', 'parsed_type': {'type': 'std', 'name': 'str'}, 'value': 'UNSET'}, {'type': 'Array of MessageEntity', 'required': False, 'description': 'A JSON-serialized list of special entities that appear in message text, which can be specified instead of parse_mode', 'html_description': '<td>A JSON-serialized list of special entities that appear in message text, which can be specified instead of <em>parse_mode</em></td>', 'rst_description': 'A JSON-serialized list of special entities that appear in message text, which can be specified instead of *parse_mode*\n', 'name': 'entities', 'parsed_type': {'type': 'array', 'items': {'type': 'entity', 'references': {'category': 'types', 'name': 'MessageEntity'}}}}, {'type': 'Boolean', 'required': False, 'description': 'Disables link previews for links in this message', 'html_description': '<td>Disables link previews for links in this message</td>', 'rst_description': 'Disables link previews for links in this message\n', 'name': 'disable_web_page_preview', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Sends the message silently. Users will receive a notification with no sound.', 'html_description': '<td>Sends the message <a href="https://telegram.org/blog/channels-2-0#silent-messages">silently</a>. Users will receive a notification with no sound.</td>', 'rst_description': 'Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.\n', 'name': 'disable_notification', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Protects the contents of the sent message from forwarding and saving', 'html_description': '<td>Protects the contents of the sent message from forwarding and saving</td>', 'rst_description': 'Protects the contents of the sent message from forwarding and saving\n', 'name': 'protect_content', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Integer', 'required': False, 'description': 'If the message is a reply, ID of the original message', 'html_description': '<td>If the message is a reply, ID of the original message</td>', 'rst_description': 'If the message is a reply, ID of the original message\n', 'name': 'reply_to_message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the message should be sent even if the specified replied-to message is not found', 'html_description': '<td>Pass <em>True</em> if the message should be sent even if the specified replied-to message is not found</td>', 'rst_description': 'Pass :code:`True` if the message should be sent even if the specified replied-to message is not found\n', 'name': 'allow_sending_without_reply', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply', 'required': False, 'description': 'Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.', 'html_description': '<td>Additional interface options. A JSON-serialized object for an <a href="/bots/features#inline-keyboards">inline keyboard</a>, <a href="/bots/features#keyboards">custom reply keyboard</a>, instructions to remove reply keyboard or to force a reply from the user.</td>', 'rst_description': 'Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.\n', 'name': 'reply_markup', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InlineKeyboardMarkup'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ReplyKeyboardMarkup'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ReplyKeyboardRemove'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ForceReply'}}]}}], 'category': 'methods', 'returning': {'type': 'Message', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'Message'}}, 'description': 'On success, the sent Message is returned.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param text: Text of the message to be sent, 1-4096 characters after entities parsing
        :param message_thread_id: Unique identifier for the target message thread (topic) of the forum; for forum supergroups only
        :param parse_mode: Mode for parsing entities in the message text. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param entities: A JSON-serialized list of special entities that appear in message text, which can be specified instead of *parse_mode*
        :param disable_web_page_preview: Disables link previews for links in this message
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.
        :param request_timeout: Request timeout
        :return: On success, the sent :class:`aiogram.types.message.Message` is returned.
        """

        call = SendMessage(
            chat_id=chat_id,
            text=text,
            message_thread_id=message_thread_id,
            parse_mode=parse_mode,
            entities=entities,
            disable_web_page_preview=disable_web_page_preview,
            disable_notification=disable_notification,
            protect_content=protect_content,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def send_photo(
        self,
        chat_id: Union[int, str],
        photo: Union[InputFile, str],
        message_thread_id: Optional[int] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET,
        caption_entities: Optional[List[MessageEntity]] = None,
        has_spoiler: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        Use this method to send photos. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#{'anchor': 'sendphoto', 'name': 'sendPhoto', 'description': 'Use this method to send photos. On success, the sent Message is returned.', 'html_description': '<p>Use this method to send photos. On success, the sent <a href="#message">Message</a> is returned.</p>', 'rst_description': 'Use this method to send photos. On success, the sent :class:`aiogram.types.message.Message` is returned.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'InputFile or String', 'required': True, 'description': "Photo to send. Pass a file_id as String to send a photo that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a photo from the Internet, or upload a new photo using multipart/form-data. The photo must be at most 10 MB in size. The photo's width and height must not exceed 10000 in total. Width and height ratio must be at most 20. More information on Sending Files", 'html_description': '<td>Photo to send. Pass a file_id as String to send a photo that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a photo from the Internet, or upload a new photo using multipart/form-data. The photo must be at most 10 MB in size. The photo\'s width and height must not exceed 10000 in total. Width and height ratio must be at most 20. <a href="#sending-files">More information on Sending Files &#187;</a></td>', 'rst_description': "Photo to send. Pass a file_id as String to send a photo that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a photo from the Internet, or upload a new photo using multipart/form-data. The photo must be at most 10 MB in size. The photo's width and height must not exceed 10000 in total. Width and height ratio must be at most 20. :ref:`More information on Sending Files » <sending-files>`\n", 'name': 'photo', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InputFile'}}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': False, 'description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only', 'html_description': '<td>Unique identifier for the target message thread (topic) of the forum; for forum supergroups only</td>', 'rst_description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only\n', 'name': 'message_thread_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'String', 'required': False, 'description': 'Photo caption (may also be used when resending photos by file_id), 0-1024 characters after entities parsing', 'html_description': '<td>Photo caption (may also be used when resending photos by <em>file_id</em>), 0-1024 characters after entities parsing</td>', 'rst_description': 'Photo caption (may also be used when resending photos by *file_id*), 0-1024 characters after entities parsing\n', 'name': 'caption', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': False, 'description': 'Mode for parsing entities in the photo caption. See formatting options for more details.', 'html_description': '<td>Mode for parsing entities in the photo caption. See <a href="#formatting-options">formatting options</a> for more details.</td>', 'rst_description': 'Mode for parsing entities in the photo caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.\n', 'name': 'parse_mode', 'parsed_type': {'type': 'std', 'name': 'str'}, 'value': 'UNSET'}, {'type': 'Array of MessageEntity', 'required': False, 'description': 'A JSON-serialized list of special entities that appear in the caption, which can be specified instead of parse_mode', 'html_description': '<td>A JSON-serialized list of special entities that appear in the caption, which can be specified instead of <em>parse_mode</em></td>', 'rst_description': 'A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*\n', 'name': 'caption_entities', 'parsed_type': {'type': 'array', 'items': {'type': 'entity', 'references': {'category': 'types', 'name': 'MessageEntity'}}}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the photo needs to be covered with a spoiler animation', 'html_description': '<td>Pass <em>True</em> if the photo needs to be covered with a spoiler animation</td>', 'rst_description': 'Pass :code:`True` if the photo needs to be covered with a spoiler animation\n', 'name': 'has_spoiler', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Sends the message silently. Users will receive a notification with no sound.', 'html_description': '<td>Sends the message <a href="https://telegram.org/blog/channels-2-0#silent-messages">silently</a>. Users will receive a notification with no sound.</td>', 'rst_description': 'Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.\n', 'name': 'disable_notification', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Protects the contents of the sent message from forwarding and saving', 'html_description': '<td>Protects the contents of the sent message from forwarding and saving</td>', 'rst_description': 'Protects the contents of the sent message from forwarding and saving\n', 'name': 'protect_content', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Integer', 'required': False, 'description': 'If the message is a reply, ID of the original message', 'html_description': '<td>If the message is a reply, ID of the original message</td>', 'rst_description': 'If the message is a reply, ID of the original message\n', 'name': 'reply_to_message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the message should be sent even if the specified replied-to message is not found', 'html_description': '<td>Pass <em>True</em> if the message should be sent even if the specified replied-to message is not found</td>', 'rst_description': 'Pass :code:`True` if the message should be sent even if the specified replied-to message is not found\n', 'name': 'allow_sending_without_reply', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply', 'required': False, 'description': 'Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.', 'html_description': '<td>Additional interface options. A JSON-serialized object for an <a href="/bots/features#inline-keyboards">inline keyboard</a>, <a href="/bots/features#keyboards">custom reply keyboard</a>, instructions to remove reply keyboard or to force a reply from the user.</td>', 'rst_description': 'Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.\n', 'name': 'reply_markup', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InlineKeyboardMarkup'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ReplyKeyboardMarkup'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ReplyKeyboardRemove'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ForceReply'}}]}}], 'category': 'methods', 'returning': {'type': 'Message', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'Message'}}, 'description': 'On success, the sent Message is returned.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param photo: Photo to send. Pass a file_id as String to send a photo that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a photo from the Internet, or upload a new photo using multipart/form-data. The photo must be at most 10 MB in size. The photo's width and height must not exceed 10000 in total. Width and height ratio must be at most 20. :ref:`More information on Sending Files » <sending-files>`
        :param message_thread_id: Unique identifier for the target message thread (topic) of the forum; for forum supergroups only
        :param caption: Photo caption (may also be used when resending photos by *file_id*), 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the photo caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*
        :param has_spoiler: Pass :code:`True` if the photo needs to be covered with a spoiler animation
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.
        :param request_timeout: Request timeout
        :return: On success, the sent :class:`aiogram.types.message.Message` is returned.
        """

        call = SendPhoto(
            chat_id=chat_id,
            photo=photo,
            message_thread_id=message_thread_id,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            has_spoiler=has_spoiler,
            disable_notification=disable_notification,
            protect_content=protect_content,
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
        message_thread_id: Optional[int] = None,
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
        protect_content: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        Use this method to send a native poll. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#{'anchor': 'sendpoll', 'name': 'sendPoll', 'description': 'Use this method to send a native poll. On success, the sent Message is returned.', 'html_description': '<p>Use this method to send a native poll. On success, the sent <a href="#message">Message</a> is returned.</p>', 'rst_description': 'Use this method to send a native poll. On success, the sent :class:`aiogram.types.message.Message` is returned.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'String', 'required': True, 'description': 'Poll question, 1-300 characters', 'html_description': '<td>Poll question, 1-300 characters</td>', 'rst_description': 'Poll question, 1-300 characters\n', 'name': 'question', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'Array of String', 'required': True, 'description': 'A JSON-serialized list of answer options, 2-10 strings 1-100 characters each', 'html_description': '<td>A JSON-serialized list of answer options, 2-10 strings 1-100 characters each</td>', 'rst_description': 'A JSON-serialized list of answer options, 2-10 strings 1-100 characters each\n', 'name': 'options', 'parsed_type': {'type': 'array', 'items': {'type': 'std', 'name': 'str'}}}, {'type': 'Integer', 'required': False, 'description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only', 'html_description': '<td>Unique identifier for the target message thread (topic) of the forum; for forum supergroups only</td>', 'rst_description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only\n', 'name': 'message_thread_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': 'True, if the poll needs to be anonymous, defaults to True', 'html_description': '<td><em>True</em>, if the poll needs to be anonymous, defaults to <em>True</em></td>', 'rst_description': ':code:`True`, if the poll needs to be anonymous, defaults to :code:`True`\n', 'name': 'is_anonymous', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'String', 'required': False, 'description': "Poll type, 'quiz' or 'regular', defaults to 'regular'", 'html_description': '<td>Poll type, &#8220;quiz&#8221; or &#8220;regular&#8221;, defaults to &#8220;regular&#8221;</td>', 'rst_description': "Poll type, 'quiz' or 'regular', defaults to 'regular'\n", 'name': 'type', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'Boolean', 'required': False, 'description': 'True, if the poll allows multiple answers, ignored for polls in quiz mode, defaults to False', 'html_description': '<td><em>True</em>, if the poll allows multiple answers, ignored for polls in quiz mode, defaults to <em>False</em></td>', 'rst_description': ':code:`True`, if the poll allows multiple answers, ignored for polls in quiz mode, defaults to :code:`False`\n', 'name': 'allows_multiple_answers', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Integer', 'required': False, 'description': '0-based identifier of the correct answer option, required for polls in quiz mode', 'html_description': '<td>0-based identifier of the correct answer option, required for polls in quiz mode</td>', 'rst_description': '0-based identifier of the correct answer option, required for polls in quiz mode\n', 'name': 'correct_option_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'String', 'required': False, 'description': 'Text that is shown when a user chooses an incorrect answer or taps on the lamp icon in a quiz-style poll, 0-200 characters with at most 2 line feeds after entities parsing', 'html_description': '<td>Text that is shown when a user chooses an incorrect answer or taps on the lamp icon in a quiz-style poll, 0-200 characters with at most 2 line feeds after entities parsing</td>', 'rst_description': 'Text that is shown when a user chooses an incorrect answer or taps on the lamp icon in a quiz-style poll, 0-200 characters with at most 2 line feeds after entities parsing\n', 'name': 'explanation', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': False, 'description': 'Mode for parsing entities in the explanation. See formatting options for more details.', 'html_description': '<td>Mode for parsing entities in the explanation. See <a href="#formatting-options">formatting options</a> for more details.</td>', 'rst_description': 'Mode for parsing entities in the explanation. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.\n', 'name': 'explanation_parse_mode', 'parsed_type': {'type': 'std', 'name': 'str'}, 'value': 'UNSET'}, {'type': 'Array of MessageEntity', 'required': False, 'description': 'A JSON-serialized list of special entities that appear in the poll explanation, which can be specified instead of parse_mode', 'html_description': '<td>A JSON-serialized list of special entities that appear in the poll explanation, which can be specified instead of <em>parse_mode</em></td>', 'rst_description': 'A JSON-serialized list of special entities that appear in the poll explanation, which can be specified instead of *parse_mode*\n', 'name': 'explanation_entities', 'parsed_type': {'type': 'array', 'items': {'type': 'entity', 'references': {'category': 'types', 'name': 'MessageEntity'}}}}, {'type': 'Integer', 'required': False, 'description': "Amount of time in seconds the poll will be active after creation, 5-600. Can't be used together with close_date.", 'html_description': "<td>Amount of time in seconds the poll will be active after creation, 5-600. Can't be used together with <em>close_date</em>.</td>", 'rst_description': "Amount of time in seconds the poll will be active after creation, 5-600. Can't be used together with *close_date*.\n", 'name': 'open_period', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Integer', 'required': False, 'description': "Point in time (Unix timestamp) when the poll will be automatically closed. Must be at least 5 and no more than 600 seconds in the future. Can't be used together with open_period.", 'html_description': "<td>Point in time (Unix timestamp) when the poll will be automatically closed. Must be at least 5 and no more than 600 seconds in the future. Can't be used together with <em>open_period</em>.</td>", 'rst_description': "Point in time (Unix timestamp) when the poll will be automatically closed. Must be at least 5 and no more than 600 seconds in the future. Can't be used together with *open_period*.\n", 'name': 'close_date', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'datetime.datetime'}, {'type': 'std', 'name': 'datetime.timedelta'}, {'type': 'std', 'name': 'int'}]}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the poll needs to be immediately closed. This can be useful for poll preview.', 'html_description': '<td>Pass <em>True</em> if the poll needs to be immediately closed. This can be useful for poll preview.</td>', 'rst_description': 'Pass :code:`True` if the poll needs to be immediately closed. This can be useful for poll preview.\n', 'name': 'is_closed', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Sends the message silently. Users will receive a notification with no sound.', 'html_description': '<td>Sends the message <a href="https://telegram.org/blog/channels-2-0#silent-messages">silently</a>. Users will receive a notification with no sound.</td>', 'rst_description': 'Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.\n', 'name': 'disable_notification', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Protects the contents of the sent message from forwarding and saving', 'html_description': '<td>Protects the contents of the sent message from forwarding and saving</td>', 'rst_description': 'Protects the contents of the sent message from forwarding and saving\n', 'name': 'protect_content', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Integer', 'required': False, 'description': 'If the message is a reply, ID of the original message', 'html_description': '<td>If the message is a reply, ID of the original message</td>', 'rst_description': 'If the message is a reply, ID of the original message\n', 'name': 'reply_to_message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the message should be sent even if the specified replied-to message is not found', 'html_description': '<td>Pass <em>True</em> if the message should be sent even if the specified replied-to message is not found</td>', 'rst_description': 'Pass :code:`True` if the message should be sent even if the specified replied-to message is not found\n', 'name': 'allow_sending_without_reply', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply', 'required': False, 'description': 'Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.', 'html_description': '<td>Additional interface options. A JSON-serialized object for an <a href="/bots/features#inline-keyboards">inline keyboard</a>, <a href="/bots/features#keyboards">custom reply keyboard</a>, instructions to remove reply keyboard or to force a reply from the user.</td>', 'rst_description': 'Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.\n', 'name': 'reply_markup', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InlineKeyboardMarkup'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ReplyKeyboardMarkup'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ReplyKeyboardRemove'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ForceReply'}}]}}], 'category': 'methods', 'returning': {'type': 'Message', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'Message'}}, 'description': 'On success, the sent Message is returned.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param question: Poll question, 1-300 characters
        :param options: A JSON-serialized list of answer options, 2-10 strings 1-100 characters each
        :param message_thread_id: Unique identifier for the target message thread (topic) of the forum; for forum supergroups only
        :param is_anonymous: :code:`True`, if the poll needs to be anonymous, defaults to :code:`True`
        :param type: Poll type, 'quiz' or 'regular', defaults to 'regular'
        :param allows_multiple_answers: :code:`True`, if the poll allows multiple answers, ignored for polls in quiz mode, defaults to :code:`False`
        :param correct_option_id: 0-based identifier of the correct answer option, required for polls in quiz mode
        :param explanation: Text that is shown when a user chooses an incorrect answer or taps on the lamp icon in a quiz-style poll, 0-200 characters with at most 2 line feeds after entities parsing
        :param explanation_parse_mode: Mode for parsing entities in the explanation. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param explanation_entities: A JSON-serialized list of special entities that appear in the poll explanation, which can be specified instead of *parse_mode*
        :param open_period: Amount of time in seconds the poll will be active after creation, 5-600. Can't be used together with *close_date*.
        :param close_date: Point in time (Unix timestamp) when the poll will be automatically closed. Must be at least 5 and no more than 600 seconds in the future. Can't be used together with *open_period*.
        :param is_closed: Pass :code:`True` if the poll needs to be immediately closed. This can be useful for poll preview.
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.
        :param request_timeout: Request timeout
        :return: On success, the sent :class:`aiogram.types.message.Message` is returned.
        """

        call = SendPoll(
            chat_id=chat_id,
            question=question,
            options=options,
            message_thread_id=message_thread_id,
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
            protect_content=protect_content,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def send_sticker(
        self,
        chat_id: Union[int, str],
        sticker: Union[InputFile, str],
        message_thread_id: Optional[int] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        Use this method to send static .WEBP, `animated <https://telegram.org/blog/animated-stickers>`_ .TGS, or `video <https://telegram.org/blog/video-stickers-better-reactions>`_ .WEBM stickers. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#{'anchor': 'sendsticker', 'name': 'sendSticker', 'description': 'Use this method to send static .WEBP, animated .TGS, or video .WEBM stickers. On success, the sent Message is returned.', 'html_description': '<p>Use this method to send static .WEBP, <a href="https://telegram.org/blog/animated-stickers">animated</a> .TGS, or <a href="https://telegram.org/blog/video-stickers-better-reactions">video</a> .WEBM stickers. On success, the sent <a href="#message">Message</a> is returned.</p>', 'rst_description': 'Use this method to send static .WEBP, `animated <https://telegram.org/blog/animated-stickers>`_ .TGS, or `video <https://telegram.org/blog/video-stickers-better-reactions>`_ .WEBM stickers. On success, the sent :class:`aiogram.types.message.Message` is returned.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'InputFile or String', 'required': True, 'description': 'Sticker to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a .WEBP file from the Internet, or upload a new one using multipart/form-data. More information on Sending Files', 'html_description': '<td>Sticker to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a .WEBP file from the Internet, or upload a new one using multipart/form-data. <a href="#sending-files">More information on Sending Files &#187;</a></td>', 'rst_description': 'Sticker to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a .WEBP file from the Internet, or upload a new one using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`\n', 'name': 'sticker', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InputFile'}}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': False, 'description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only', 'html_description': '<td>Unique identifier for the target message thread (topic) of the forum; for forum supergroups only</td>', 'rst_description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only\n', 'name': 'message_thread_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': 'Sends the message silently. Users will receive a notification with no sound.', 'html_description': '<td>Sends the message <a href="https://telegram.org/blog/channels-2-0#silent-messages">silently</a>. Users will receive a notification with no sound.</td>', 'rst_description': 'Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.\n', 'name': 'disable_notification', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Protects the contents of the sent message from forwarding and saving', 'html_description': '<td>Protects the contents of the sent message from forwarding and saving</td>', 'rst_description': 'Protects the contents of the sent message from forwarding and saving\n', 'name': 'protect_content', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Integer', 'required': False, 'description': 'If the message is a reply, ID of the original message', 'html_description': '<td>If the message is a reply, ID of the original message</td>', 'rst_description': 'If the message is a reply, ID of the original message\n', 'name': 'reply_to_message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the message should be sent even if the specified replied-to message is not found', 'html_description': '<td>Pass <em>True</em> if the message should be sent even if the specified replied-to message is not found</td>', 'rst_description': 'Pass :code:`True` if the message should be sent even if the specified replied-to message is not found\n', 'name': 'allow_sending_without_reply', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply', 'required': False, 'description': 'Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.', 'html_description': '<td>Additional interface options. A JSON-serialized object for an <a href="/bots/features#inline-keyboards">inline keyboard</a>, <a href="/bots/features#keyboards">custom reply keyboard</a>, instructions to remove reply keyboard or to force a reply from the user.</td>', 'rst_description': 'Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.\n', 'name': 'reply_markup', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InlineKeyboardMarkup'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ReplyKeyboardMarkup'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ReplyKeyboardRemove'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ForceReply'}}]}}], 'category': 'methods', 'returning': {'type': 'Message', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'Message'}}, 'description': 'On success, the sent Message is returned.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param sticker: Sticker to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a .WEBP file from the Internet, or upload a new one using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`
        :param message_thread_id: Unique identifier for the target message thread (topic) of the forum; for forum supergroups only
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.
        :param request_timeout: Request timeout
        :return: On success, the sent :class:`aiogram.types.message.Message` is returned.
        """

        call = SendSticker(
            chat_id=chat_id,
            sticker=sticker,
            message_thread_id=message_thread_id,
            disable_notification=disable_notification,
            protect_content=protect_content,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
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
        message_thread_id: Optional[int] = None,
        foursquare_id: Optional[str] = None,
        foursquare_type: Optional[str] = None,
        google_place_id: Optional[str] = None,
        google_place_type: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        Use this method to send information about a venue. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#{'anchor': 'sendvenue', 'name': 'sendVenue', 'description': 'Use this method to send information about a venue. On success, the sent Message is returned.', 'html_description': '<p>Use this method to send information about a venue. On success, the sent <a href="#message">Message</a> is returned.</p>', 'rst_description': 'Use this method to send information about a venue. On success, the sent :class:`aiogram.types.message.Message` is returned.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Float number', 'required': True, 'description': 'Latitude of the venue', 'html_description': '<td>Latitude of the venue</td>', 'rst_description': 'Latitude of the venue\n', 'name': 'latitude', 'parsed_type': {'type': 'std', 'name': 'float'}}, {'type': 'Float number', 'required': True, 'description': 'Longitude of the venue', 'html_description': '<td>Longitude of the venue</td>', 'rst_description': 'Longitude of the venue\n', 'name': 'longitude', 'parsed_type': {'type': 'std', 'name': 'float'}}, {'type': 'String', 'required': True, 'description': 'Name of the venue', 'html_description': '<td>Name of the venue</td>', 'rst_description': 'Name of the venue\n', 'name': 'title', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': True, 'description': 'Address of the venue', 'html_description': '<td>Address of the venue</td>', 'rst_description': 'Address of the venue\n', 'name': 'address', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'Integer', 'required': False, 'description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only', 'html_description': '<td>Unique identifier for the target message thread (topic) of the forum; for forum supergroups only</td>', 'rst_description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only\n', 'name': 'message_thread_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'String', 'required': False, 'description': 'Foursquare identifier of the venue', 'html_description': '<td>Foursquare identifier of the venue</td>', 'rst_description': 'Foursquare identifier of the venue\n', 'name': 'foursquare_id', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': False, 'description': "Foursquare type of the venue, if known. (For example, 'arts_entertainment/default', 'arts_entertainment/aquarium' or 'food/icecream'.)", 'html_description': '<td>Foursquare type of the venue, if known. (For example, &#8220;arts_entertainment/default&#8221;, &#8220;arts_entertainment/aquarium&#8221; or &#8220;food/icecream&#8221;.)</td>', 'rst_description': "Foursquare type of the venue, if known. (For example, 'arts_entertainment/default', 'arts_entertainment/aquarium' or 'food/icecream'.)\n", 'name': 'foursquare_type', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': False, 'description': 'Google Places identifier of the venue', 'html_description': '<td>Google Places identifier of the venue</td>', 'rst_description': 'Google Places identifier of the venue\n', 'name': 'google_place_id', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': False, 'description': 'Google Places type of the venue. (See supported types.)', 'html_description': '<td>Google Places type of the venue. (See <a href="https://developers.google.com/places/web-service/supported_types">supported types</a>.)</td>', 'rst_description': 'Google Places type of the venue. (See `supported types <https://developers.google.com/places/web-service/supported_types>`_.)\n', 'name': 'google_place_type', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'Boolean', 'required': False, 'description': 'Sends the message silently. Users will receive a notification with no sound.', 'html_description': '<td>Sends the message <a href="https://telegram.org/blog/channels-2-0#silent-messages">silently</a>. Users will receive a notification with no sound.</td>', 'rst_description': 'Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.\n', 'name': 'disable_notification', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Protects the contents of the sent message from forwarding and saving', 'html_description': '<td>Protects the contents of the sent message from forwarding and saving</td>', 'rst_description': 'Protects the contents of the sent message from forwarding and saving\n', 'name': 'protect_content', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Integer', 'required': False, 'description': 'If the message is a reply, ID of the original message', 'html_description': '<td>If the message is a reply, ID of the original message</td>', 'rst_description': 'If the message is a reply, ID of the original message\n', 'name': 'reply_to_message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the message should be sent even if the specified replied-to message is not found', 'html_description': '<td>Pass <em>True</em> if the message should be sent even if the specified replied-to message is not found</td>', 'rst_description': 'Pass :code:`True` if the message should be sent even if the specified replied-to message is not found\n', 'name': 'allow_sending_without_reply', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply', 'required': False, 'description': 'Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.', 'html_description': '<td>Additional interface options. A JSON-serialized object for an <a href="/bots/features#inline-keyboards">inline keyboard</a>, <a href="/bots/features#keyboards">custom reply keyboard</a>, instructions to remove reply keyboard or to force a reply from the user.</td>', 'rst_description': 'Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.\n', 'name': 'reply_markup', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InlineKeyboardMarkup'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ReplyKeyboardMarkup'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ReplyKeyboardRemove'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ForceReply'}}]}}], 'category': 'methods', 'returning': {'type': 'Message', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'Message'}}, 'description': 'On success, the sent Message is returned.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param latitude: Latitude of the venue
        :param longitude: Longitude of the venue
        :param title: Name of the venue
        :param address: Address of the venue
        :param message_thread_id: Unique identifier for the target message thread (topic) of the forum; for forum supergroups only
        :param foursquare_id: Foursquare identifier of the venue
        :param foursquare_type: Foursquare type of the venue, if known. (For example, 'arts_entertainment/default', 'arts_entertainment/aquarium' or 'food/icecream'.)
        :param google_place_id: Google Places identifier of the venue
        :param google_place_type: Google Places type of the venue. (See `supported types <https://developers.google.com/places/web-service/supported_types>`_.)
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.
        :param request_timeout: Request timeout
        :return: On success, the sent :class:`aiogram.types.message.Message` is returned.
        """

        call = SendVenue(
            chat_id=chat_id,
            latitude=latitude,
            longitude=longitude,
            title=title,
            address=address,
            message_thread_id=message_thread_id,
            foursquare_id=foursquare_id,
            foursquare_type=foursquare_type,
            google_place_id=google_place_id,
            google_place_type=google_place_type,
            disable_notification=disable_notification,
            protect_content=protect_content,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def send_video(
        self,
        chat_id: Union[int, str],
        video: Union[InputFile, str],
        message_thread_id: Optional[int] = None,
        duration: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        thumb: Optional[Union[InputFile, str]] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET,
        caption_entities: Optional[List[MessageEntity]] = None,
        has_spoiler: Optional[bool] = None,
        supports_streaming: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        Use this method to send video files, Telegram clients support MPEG4 videos (other formats may be sent as :class:`aiogram.types.document.Document`). On success, the sent :class:`aiogram.types.message.Message` is returned. Bots can currently send video files of up to 50 MB in size, this limit may be changed in the future.

        Source: https://core.telegram.org/bots/api#{'anchor': 'sendvideo', 'name': 'sendVideo', 'description': 'Use this method to send video files, Telegram clients support MPEG4 videos (other formats may be sent as Document). On success, the sent Message is returned. Bots can currently send video files of up to 50 MB in size, this limit may be changed in the future.', 'html_description': '<p>Use this method to send video files, Telegram clients support MPEG4 videos (other formats may be sent as <a href="#document">Document</a>). On success, the sent <a href="#message">Message</a> is returned. Bots can currently send video files of up to 50 MB in size, this limit may be changed in the future.</p>', 'rst_description': 'Use this method to send video files, Telegram clients support MPEG4 videos (other formats may be sent as :class:`aiogram.types.document.Document`). On success, the sent :class:`aiogram.types.message.Message` is returned. Bots can currently send video files of up to 50 MB in size, this limit may be changed in the future.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'InputFile or String', 'required': True, 'description': 'Video to send. Pass a file_id as String to send a video that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a video from the Internet, or upload a new video using multipart/form-data. More information on Sending Files', 'html_description': '<td>Video to send. Pass a file_id as String to send a video that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a video from the Internet, or upload a new video using multipart/form-data. <a href="#sending-files">More information on Sending Files &#187;</a></td>', 'rst_description': 'Video to send. Pass a file_id as String to send a video that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a video from the Internet, or upload a new video using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`\n', 'name': 'video', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InputFile'}}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': False, 'description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only', 'html_description': '<td>Unique identifier for the target message thread (topic) of the forum; for forum supergroups only</td>', 'rst_description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only\n', 'name': 'message_thread_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Integer', 'required': False, 'description': 'Duration of sent video in seconds', 'html_description': '<td>Duration of sent video in seconds</td>', 'rst_description': 'Duration of sent video in seconds\n', 'name': 'duration', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Integer', 'required': False, 'description': 'Video width', 'html_description': '<td>Video width</td>', 'rst_description': 'Video width\n', 'name': 'width', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Integer', 'required': False, 'description': 'Video height', 'html_description': '<td>Video height</td>', 'rst_description': 'Video height\n', 'name': 'height', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'InputFile or String', 'required': False, 'description': "Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. More information on Sending Files", 'html_description': '<td>Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail\'s width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can\'t be reused and can be only uploaded as a new file, so you can pass &#8220;attach://&lt;file_attach_name&gt;&#8221; if the thumbnail was uploaded using multipart/form-data under &lt;file_attach_name&gt;. <a href="#sending-files">More information on Sending Files &#187;</a></td>', 'rst_description': "Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. :ref:`More information on Sending Files » <sending-files>`\n", 'name': 'thumb', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InputFile'}}, {'type': 'std', 'name': 'str'}]}}, {'type': 'String', 'required': False, 'description': 'Video caption (may also be used when resending videos by file_id), 0-1024 characters after entities parsing', 'html_description': '<td>Video caption (may also be used when resending videos by <em>file_id</em>), 0-1024 characters after entities parsing</td>', 'rst_description': 'Video caption (may also be used when resending videos by *file_id*), 0-1024 characters after entities parsing\n', 'name': 'caption', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': False, 'description': 'Mode for parsing entities in the video caption. See formatting options for more details.', 'html_description': '<td>Mode for parsing entities in the video caption. See <a href="#formatting-options">formatting options</a> for more details.</td>', 'rst_description': 'Mode for parsing entities in the video caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.\n', 'name': 'parse_mode', 'parsed_type': {'type': 'std', 'name': 'str'}, 'value': 'UNSET'}, {'type': 'Array of MessageEntity', 'required': False, 'description': 'A JSON-serialized list of special entities that appear in the caption, which can be specified instead of parse_mode', 'html_description': '<td>A JSON-serialized list of special entities that appear in the caption, which can be specified instead of <em>parse_mode</em></td>', 'rst_description': 'A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*\n', 'name': 'caption_entities', 'parsed_type': {'type': 'array', 'items': {'type': 'entity', 'references': {'category': 'types', 'name': 'MessageEntity'}}}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the video needs to be covered with a spoiler animation', 'html_description': '<td>Pass <em>True</em> if the video needs to be covered with a spoiler animation</td>', 'rst_description': 'Pass :code:`True` if the video needs to be covered with a spoiler animation\n', 'name': 'has_spoiler', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the uploaded video is suitable for streaming', 'html_description': '<td>Pass <em>True</em> if the uploaded video is suitable for streaming</td>', 'rst_description': 'Pass :code:`True` if the uploaded video is suitable for streaming\n', 'name': 'supports_streaming', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Sends the message silently. Users will receive a notification with no sound.', 'html_description': '<td>Sends the message <a href="https://telegram.org/blog/channels-2-0#silent-messages">silently</a>. Users will receive a notification with no sound.</td>', 'rst_description': 'Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.\n', 'name': 'disable_notification', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Protects the contents of the sent message from forwarding and saving', 'html_description': '<td>Protects the contents of the sent message from forwarding and saving</td>', 'rst_description': 'Protects the contents of the sent message from forwarding and saving\n', 'name': 'protect_content', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Integer', 'required': False, 'description': 'If the message is a reply, ID of the original message', 'html_description': '<td>If the message is a reply, ID of the original message</td>', 'rst_description': 'If the message is a reply, ID of the original message\n', 'name': 'reply_to_message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the message should be sent even if the specified replied-to message is not found', 'html_description': '<td>Pass <em>True</em> if the message should be sent even if the specified replied-to message is not found</td>', 'rst_description': 'Pass :code:`True` if the message should be sent even if the specified replied-to message is not found\n', 'name': 'allow_sending_without_reply', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply', 'required': False, 'description': 'Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.', 'html_description': '<td>Additional interface options. A JSON-serialized object for an <a href="/bots/features#inline-keyboards">inline keyboard</a>, <a href="/bots/features#keyboards">custom reply keyboard</a>, instructions to remove reply keyboard or to force a reply from the user.</td>', 'rst_description': 'Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.\n', 'name': 'reply_markup', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InlineKeyboardMarkup'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ReplyKeyboardMarkup'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ReplyKeyboardRemove'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ForceReply'}}]}}], 'category': 'methods', 'returning': {'type': 'Message', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'Message'}}, 'description': 'On success, the sent Message is returned.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param video: Video to send. Pass a file_id as String to send a video that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a video from the Internet, or upload a new video using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`
        :param message_thread_id: Unique identifier for the target message thread (topic) of the forum; for forum supergroups only
        :param duration: Duration of sent video in seconds
        :param width: Video width
        :param height: Video height
        :param thumb: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. :ref:`More information on Sending Files » <sending-files>`
        :param caption: Video caption (may also be used when resending videos by *file_id*), 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the video caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*
        :param has_spoiler: Pass :code:`True` if the video needs to be covered with a spoiler animation
        :param supports_streaming: Pass :code:`True` if the uploaded video is suitable for streaming
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.
        :param request_timeout: Request timeout
        :return: Bots can currently send video files of up to 50 MB in size, this limit may be changed in the future.
        """

        call = SendVideo(
            chat_id=chat_id,
            video=video,
            message_thread_id=message_thread_id,
            duration=duration,
            width=width,
            height=height,
            thumb=thumb,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            has_spoiler=has_spoiler,
            supports_streaming=supports_streaming,
            disable_notification=disable_notification,
            protect_content=protect_content,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def send_video_note(
        self,
        chat_id: Union[int, str],
        video_note: Union[InputFile, str],
        message_thread_id: Optional[int] = None,
        duration: Optional[int] = None,
        length: Optional[int] = None,
        thumb: Optional[Union[InputFile, str]] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        As of `v.4.0 <https://telegram.org/blog/video-messages-and-telescope>`_, Telegram clients support rounded square MPEG4 videos of up to 1 minute long. Use this method to send video messages. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#{'anchor': 'sendvideonote', 'name': 'sendVideoNote', 'description': 'As of v.4.0, Telegram clients support rounded square MPEG4 videos of up to 1 minute long. Use this method to send video messages. On success, the sent Message is returned.', 'html_description': '<p>As of <a href="https://telegram.org/blog/video-messages-and-telescope">v.4.0</a>, Telegram clients support rounded square MPEG4 videos of up to 1 minute long. Use this method to send video messages. On success, the sent <a href="#message">Message</a> is returned.</p>', 'rst_description': 'As of `v.4.0 <https://telegram.org/blog/video-messages-and-telescope>`_, Telegram clients support rounded square MPEG4 videos of up to 1 minute long. Use this method to send video messages. On success, the sent :class:`aiogram.types.message.Message` is returned.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'InputFile or String', 'required': True, 'description': 'Video note to send. Pass a file_id as String to send a video note that exists on the Telegram servers (recommended) or upload a new video using multipart/form-data. More information on Sending Files. Sending video notes by a URL is currently unsupported', 'html_description': '<td>Video note to send. Pass a file_id as String to send a video note that exists on the Telegram servers (recommended) or upload a new video using multipart/form-data. <a href="#sending-files">More information on Sending Files &#187;</a>. Sending video notes by a URL is currently unsupported</td>', 'rst_description': 'Video note to send. Pass a file_id as String to send a video note that exists on the Telegram servers (recommended) or upload a new video using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`. Sending video notes by a URL is currently unsupported\n', 'name': 'video_note', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InputFile'}}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': False, 'description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only', 'html_description': '<td>Unique identifier for the target message thread (topic) of the forum; for forum supergroups only</td>', 'rst_description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only\n', 'name': 'message_thread_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Integer', 'required': False, 'description': 'Duration of sent video in seconds', 'html_description': '<td>Duration of sent video in seconds</td>', 'rst_description': 'Duration of sent video in seconds\n', 'name': 'duration', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Integer', 'required': False, 'description': 'Video width and height, i.e. diameter of the video message', 'html_description': '<td>Video width and height, i.e. diameter of the video message</td>', 'rst_description': 'Video width and height, i.e. diameter of the video message\n', 'name': 'length', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'InputFile or String', 'required': False, 'description': "Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. More information on Sending Files", 'html_description': '<td>Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail\'s width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can\'t be reused and can be only uploaded as a new file, so you can pass &#8220;attach://&lt;file_attach_name&gt;&#8221; if the thumbnail was uploaded using multipart/form-data under &lt;file_attach_name&gt;. <a href="#sending-files">More information on Sending Files &#187;</a></td>', 'rst_description': "Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. :ref:`More information on Sending Files » <sending-files>`\n", 'name': 'thumb', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InputFile'}}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Boolean', 'required': False, 'description': 'Sends the message silently. Users will receive a notification with no sound.', 'html_description': '<td>Sends the message <a href="https://telegram.org/blog/channels-2-0#silent-messages">silently</a>. Users will receive a notification with no sound.</td>', 'rst_description': 'Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.\n', 'name': 'disable_notification', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Protects the contents of the sent message from forwarding and saving', 'html_description': '<td>Protects the contents of the sent message from forwarding and saving</td>', 'rst_description': 'Protects the contents of the sent message from forwarding and saving\n', 'name': 'protect_content', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Integer', 'required': False, 'description': 'If the message is a reply, ID of the original message', 'html_description': '<td>If the message is a reply, ID of the original message</td>', 'rst_description': 'If the message is a reply, ID of the original message\n', 'name': 'reply_to_message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the message should be sent even if the specified replied-to message is not found', 'html_description': '<td>Pass <em>True</em> if the message should be sent even if the specified replied-to message is not found</td>', 'rst_description': 'Pass :code:`True` if the message should be sent even if the specified replied-to message is not found\n', 'name': 'allow_sending_without_reply', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply', 'required': False, 'description': 'Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.', 'html_description': '<td>Additional interface options. A JSON-serialized object for an <a href="/bots/features#inline-keyboards">inline keyboard</a>, <a href="/bots/features#keyboards">custom reply keyboard</a>, instructions to remove reply keyboard or to force a reply from the user.</td>', 'rst_description': 'Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.\n', 'name': 'reply_markup', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InlineKeyboardMarkup'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ReplyKeyboardMarkup'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ReplyKeyboardRemove'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ForceReply'}}]}}], 'category': 'methods', 'returning': {'type': 'Message', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'Message'}}, 'description': 'On success, the sent Message is returned.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param video_note: Video note to send. Pass a file_id as String to send a video note that exists on the Telegram servers (recommended) or upload a new video using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`. Sending video notes by a URL is currently unsupported
        :param message_thread_id: Unique identifier for the target message thread (topic) of the forum; for forum supergroups only
        :param duration: Duration of sent video in seconds
        :param length: Video width and height, i.e. diameter of the video message
        :param thumb: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. :ref:`More information on Sending Files » <sending-files>`
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.
        :param request_timeout: Request timeout
        :return: On success, the sent :class:`aiogram.types.message.Message` is returned.
        """

        call = SendVideoNote(
            chat_id=chat_id,
            video_note=video_note,
            message_thread_id=message_thread_id,
            duration=duration,
            length=length,
            thumb=thumb,
            disable_notification=disable_notification,
            protect_content=protect_content,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )
        return await self(call, request_timeout=request_timeout)

    async def send_voice(
        self,
        chat_id: Union[int, str],
        voice: Union[InputFile, str],
        message_thread_id: Optional[int] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET,
        caption_entities: Optional[List[MessageEntity]] = None,
        duration: Optional[int] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        request_timeout: Optional[int] = None,
    ) -> Message:
        """
        Use this method to send audio files, if you want Telegram clients to display the file as a playable voice message. For this to work, your audio must be in an .OGG file encoded with OPUS (other formats may be sent as :class:`aiogram.types.audio.Audio` or :class:`aiogram.types.document.Document`). On success, the sent :class:`aiogram.types.message.Message` is returned. Bots can currently send voice messages of up to 50 MB in size, this limit may be changed in the future.

        Source: https://core.telegram.org/bots/api#{'anchor': 'sendvoice', 'name': 'sendVoice', 'description': 'Use this method to send audio files, if you want Telegram clients to display the file as a playable voice message. For this to work, your audio must be in an .OGG file encoded with OPUS (other formats may be sent as Audio or Document). On success, the sent Message is returned. Bots can currently send voice messages of up to 50 MB in size, this limit may be changed in the future.', 'html_description': '<p>Use this method to send audio files, if you want Telegram clients to display the file as a playable voice message. For this to work, your audio must be in an .OGG file encoded with OPUS (other formats may be sent as <a href="#audio">Audio</a> or <a href="#document">Document</a>). On success, the sent <a href="#message">Message</a> is returned. Bots can currently send voice messages of up to 50 MB in size, this limit may be changed in the future.</p>', 'rst_description': 'Use this method to send audio files, if you want Telegram clients to display the file as a playable voice message. For this to work, your audio must be in an .OGG file encoded with OPUS (other formats may be sent as :class:`aiogram.types.audio.Audio` or :class:`aiogram.types.document.Document`). On success, the sent :class:`aiogram.types.message.Message` is returned. Bots can currently send voice messages of up to 50 MB in size, this limit may be changed in the future.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'InputFile or String', 'required': True, 'description': 'Audio file to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. More information on Sending Files', 'html_description': '<td>Audio file to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. <a href="#sending-files">More information on Sending Files &#187;</a></td>', 'rst_description': 'Audio file to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`\n', 'name': 'voice', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InputFile'}}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': False, 'description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only', 'html_description': '<td>Unique identifier for the target message thread (topic) of the forum; for forum supergroups only</td>', 'rst_description': 'Unique identifier for the target message thread (topic) of the forum; for forum supergroups only\n', 'name': 'message_thread_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'String', 'required': False, 'description': 'Voice message caption, 0-1024 characters after entities parsing', 'html_description': '<td>Voice message caption, 0-1024 characters after entities parsing</td>', 'rst_description': 'Voice message caption, 0-1024 characters after entities parsing\n', 'name': 'caption', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'String', 'required': False, 'description': 'Mode for parsing entities in the voice message caption. See formatting options for more details.', 'html_description': '<td>Mode for parsing entities in the voice message caption. See <a href="#formatting-options">formatting options</a> for more details.</td>', 'rst_description': 'Mode for parsing entities in the voice message caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.\n', 'name': 'parse_mode', 'parsed_type': {'type': 'std', 'name': 'str'}, 'value': 'UNSET'}, {'type': 'Array of MessageEntity', 'required': False, 'description': 'A JSON-serialized list of special entities that appear in the caption, which can be specified instead of parse_mode', 'html_description': '<td>A JSON-serialized list of special entities that appear in the caption, which can be specified instead of <em>parse_mode</em></td>', 'rst_description': 'A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*\n', 'name': 'caption_entities', 'parsed_type': {'type': 'array', 'items': {'type': 'entity', 'references': {'category': 'types', 'name': 'MessageEntity'}}}}, {'type': 'Integer', 'required': False, 'description': 'Duration of the voice message in seconds', 'html_description': '<td>Duration of the voice message in seconds</td>', 'rst_description': 'Duration of the voice message in seconds\n', 'name': 'duration', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': 'Sends the message silently. Users will receive a notification with no sound.', 'html_description': '<td>Sends the message <a href="https://telegram.org/blog/channels-2-0#silent-messages">silently</a>. Users will receive a notification with no sound.</td>', 'rst_description': 'Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.\n', 'name': 'disable_notification', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Protects the contents of the sent message from forwarding and saving', 'html_description': '<td>Protects the contents of the sent message from forwarding and saving</td>', 'rst_description': 'Protects the contents of the sent message from forwarding and saving\n', 'name': 'protect_content', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Integer', 'required': False, 'description': 'If the message is a reply, ID of the original message', 'html_description': '<td>If the message is a reply, ID of the original message</td>', 'rst_description': 'If the message is a reply, ID of the original message\n', 'name': 'reply_to_message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the message should be sent even if the specified replied-to message is not found', 'html_description': '<td>Pass <em>True</em> if the message should be sent even if the specified replied-to message is not found</td>', 'rst_description': 'Pass :code:`True` if the message should be sent even if the specified replied-to message is not found\n', 'name': 'allow_sending_without_reply', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply', 'required': False, 'description': 'Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.', 'html_description': '<td>Additional interface options. A JSON-serialized object for an <a href="/bots/features#inline-keyboards">inline keyboard</a>, <a href="/bots/features#keyboards">custom reply keyboard</a>, instructions to remove reply keyboard or to force a reply from the user.</td>', 'rst_description': 'Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.\n', 'name': 'reply_markup', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InlineKeyboardMarkup'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ReplyKeyboardMarkup'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ReplyKeyboardRemove'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'ForceReply'}}]}}], 'category': 'methods', 'returning': {'type': 'Message', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'Message'}}, 'description': 'On success, the sent Message is returned.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param voice: Audio file to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`
        :param message_thread_id: Unique identifier for the target message thread (topic) of the forum; for forum supergroups only
        :param caption: Voice message caption, 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the voice message caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*
        :param duration: Duration of the voice message in seconds
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user.
        :param request_timeout: Request timeout
        :return: Bots can currently send voice messages of up to 50 MB in size, this limit may be changed in the future.
        """

        call = SendVoice(
            chat_id=chat_id,
            voice=voice,
            message_thread_id=message_thread_id,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            duration=duration,
            disable_notification=disable_notification,
            protect_content=protect_content,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
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

        Source: https://core.telegram.org/bots/api#{'anchor': 'setchatadministratorcustomtitle', 'name': 'setChatAdministratorCustomTitle', 'description': 'Use this method to set a custom title for an administrator in a supergroup promoted by the bot. Returns True on success.', 'html_description': '<p>Use this method to set a custom title for an administrator in a supergroup promoted by the bot. Returns <em>True</em> on success.</p>', 'rst_description': 'Use this method to set a custom title for an administrator in a supergroup promoted by the bot. Returns :code:`True` on success.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target supergroup (in the format @supergroupusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target supergroup (in the format <code>@supergroupusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': True, 'description': 'Unique identifier of the target user', 'html_description': '<td>Unique identifier of the target user</td>', 'rst_description': 'Unique identifier of the target user\n', 'name': 'user_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'String', 'required': True, 'description': 'New custom title for the administrator; 0-16 characters, emoji are not allowed', 'html_description': '<td>New custom title for the administrator; 0-16 characters, emoji are not allowed</td>', 'rst_description': 'New custom title for the administrator; 0-16 characters, emoji are not allowed\n', 'name': 'custom_title', 'parsed_type': {'type': 'std', 'name': 'str'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)
        :param user_id: Unique identifier of the target user
        :param custom_title: New custom title for the administrator; 0-16 characters, emoji are not allowed
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = SetChatAdministratorCustomTitle(
            chat_id=chat_id,
            user_id=user_id,
            custom_title=custom_title,
        )
        return await self(call, request_timeout=request_timeout)

    async def set_chat_description(
        self,
        chat_id: Union[int, str],
        description: Optional[str] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to change the description of a group, a supergroup or a channel. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'setchatdescription', 'name': 'setChatDescription', 'description': 'Use this method to change the description of a group, a supergroup or a channel. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns True on success.', 'html_description': '<p>Use this method to change the description of a group, a supergroup or a channel. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns <em>True</em> on success.</p>', 'rst_description': 'Use this method to change the description of a group, a supergroup or a channel. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns :code:`True` on success.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'String', 'required': False, 'description': 'New chat description, 0-255 characters', 'html_description': '<td>New chat description, 0-255 characters</td>', 'rst_description': 'New chat description, 0-255 characters\n', 'name': 'description', 'parsed_type': {'type': 'std', 'name': 'str'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param description: New chat description, 0-255 characters
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = SetChatDescription(
            chat_id=chat_id,
            description=description,
        )
        return await self(call, request_timeout=request_timeout)

    async def set_chat_menu_button(
        self,
        chat_id: Optional[int] = None,
        menu_button: Optional[
            Union[MenuButtonDefault, MenuButtonWebApp, MenuButtonCommands]
        ] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to change the bot's menu button in a private chat, or the default menu button. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'setchatmenubutton', 'name': 'setChatMenuButton', 'description': "Use this method to change the bot's menu button in a private chat, or the default menu button. Returns True on success.", 'html_description': "<p>Use this method to change the bot's menu button in a private chat, or the default menu button. Returns <em>True</em> on success.</p>", 'rst_description': "Use this method to change the bot's menu button in a private chat, or the default menu button. Returns :code:`True` on success.", 'annotations': [{'type': 'Integer', 'required': False, 'description': "Unique identifier for the target private chat. If not specified, default bot's menu button will be changed", 'html_description': "<td>Unique identifier for the target private chat. If not specified, default bot's menu button will be changed</td>", 'rst_description': "Unique identifier for the target private chat. If not specified, default bot's menu button will be changed\n", 'name': 'chat_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'MenuButton', 'required': False, 'description': "A JSON-serialized object for the bot's new menu button. Defaults to MenuButtonDefault", 'html_description': '<td>A JSON-serialized object for the bot\'s new menu button. Defaults to <a href="#menubuttondefault">MenuButtonDefault</a></td>', 'rst_description': "A JSON-serialized object for the bot's new menu button. Defaults to :class:`aiogram.types.menu_button_default.MenuButtonDefault`\n", 'name': 'menu_button', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'MenuButtonDefault'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'MenuButtonWebApp'}}, {'type': 'entity', 'references': {'category': 'types', 'name': 'MenuButtonCommands'}}]}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target private chat. If not specified, default bot's menu button will be changed
        :param menu_button: A JSON-serialized object for the bot's new menu button. Defaults to :class:`aiogram.types.menu_button_default.MenuButtonDefault`
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = SetChatMenuButton(
            chat_id=chat_id,
            menu_button=menu_button,
        )
        return await self(call, request_timeout=request_timeout)

    async def set_chat_permissions(
        self,
        chat_id: Union[int, str],
        permissions: ChatPermissions,
        use_independent_chat_permissions: Optional[bool] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to set default chat permissions for all members. The bot must be an administrator in the group or a supergroup for this to work and must have the *can_restrict_members* administrator rights. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'setchatpermissions', 'name': 'setChatPermissions', 'description': 'Use this method to set default chat permissions for all members. The bot must be an administrator in the group or a supergroup for this to work and must have the can_restrict_members administrator rights. Returns True on success.', 'html_description': '<p>Use this method to set default chat permissions for all members. The bot must be an administrator in the group or a supergroup for this to work and must have the <em>can_restrict_members</em> administrator rights. Returns <em>True</em> on success.</p>', 'rst_description': 'Use this method to set default chat permissions for all members. The bot must be an administrator in the group or a supergroup for this to work and must have the *can_restrict_members* administrator rights. Returns :code:`True` on success.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target supergroup (in the format @supergroupusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target supergroup (in the format <code>@supergroupusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'ChatPermissions', 'required': True, 'description': 'A JSON-serialized object for new default chat permissions', 'html_description': '<td>A JSON-serialized object for new default chat permissions</td>', 'rst_description': 'A JSON-serialized object for new default chat permissions\n', 'name': 'permissions', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'ChatPermissions'}}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if chat permissions are set independently. Otherwise, the can_send_other_messages and can_add_web_page_previews permissions will imply the can_send_messages, can_send_audios, can_send_documents, can_send_photos, can_send_videos, can_send_video_notes, and can_send_voice_notes permissions; the can_send_polls permission will imply the can_send_messages permission.', 'html_description': '<td>Pass <em>True</em> if chat permissions are set independently. Otherwise, the <em>can_send_other_messages</em> and <em>can_add_web_page_previews</em> permissions will imply the <em>can_send_messages</em>, <em>can_send_audios</em>, <em>can_send_documents</em>, <em>can_send_photos</em>, <em>can_send_videos</em>, <em>can_send_video_notes</em>, and <em>can_send_voice_notes</em> permissions; the <em>can_send_polls</em> permission will imply the <em>can_send_messages</em> permission.</td>', 'rst_description': 'Pass :code:`True` if chat permissions are set independently. Otherwise, the *can_send_other_messages* and *can_add_web_page_previews* permissions will imply the *can_send_messages*, *can_send_audios*, *can_send_documents*, *can_send_photos*, *can_send_videos*, *can_send_video_notes*, and *can_send_voice_notes* permissions; the *can_send_polls* permission will imply the *can_send_messages* permission.\n', 'name': 'use_independent_chat_permissions', 'parsed_type': {'type': 'std', 'name': 'bool'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)
        :param permissions: A JSON-serialized object for new default chat permissions
        :param use_independent_chat_permissions: Pass :code:`True` if chat permissions are set independently. Otherwise, the *can_send_other_messages* and *can_add_web_page_previews* permissions will imply the *can_send_messages*, *can_send_audios*, *can_send_documents*, *can_send_photos*, *can_send_videos*, *can_send_video_notes*, and *can_send_voice_notes* permissions; the *can_send_polls* permission will imply the *can_send_messages* permission.
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = SetChatPermissions(
            chat_id=chat_id,
            permissions=permissions,
            use_independent_chat_permissions=use_independent_chat_permissions,
        )
        return await self(call, request_timeout=request_timeout)

    async def set_chat_photo(
        self,
        chat_id: Union[int, str],
        photo: InputFile,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to set a new profile photo for the chat. Photos can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'setchatphoto', 'name': 'setChatPhoto', 'description': "Use this method to set a new profile photo for the chat. Photos can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns True on success.", 'html_description': "<p>Use this method to set a new profile photo for the chat. Photos can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns <em>True</em> on success.</p>", 'rst_description': "Use this method to set a new profile photo for the chat. Photos can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns :code:`True` on success.", 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'InputFile', 'required': True, 'description': 'New chat photo, uploaded using multipart/form-data', 'html_description': '<td>New chat photo, uploaded using multipart/form-data</td>', 'rst_description': 'New chat photo, uploaded using multipart/form-data\n', 'name': 'photo', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'InputFile'}}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param photo: New chat photo, uploaded using multipart/form-data
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = SetChatPhoto(
            chat_id=chat_id,
            photo=photo,
        )
        return await self(call, request_timeout=request_timeout)

    async def set_chat_sticker_set(
        self,
        chat_id: Union[int, str],
        sticker_set_name: str,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to set a new group sticker set for a supergroup. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Use the field *can_set_sticker_set* optionally returned in :class:`aiogram.methods.get_chat.GetChat` requests to check if the bot can use this method. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'setchatstickerset', 'name': 'setChatStickerSet', 'description': 'Use this method to set a new group sticker set for a supergroup. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Use the field can_set_sticker_set optionally returned in getChat requests to check if the bot can use this method. Returns True on success.', 'html_description': '<p>Use this method to set a new group sticker set for a supergroup. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Use the field <em>can_set_sticker_set</em> optionally returned in <a href="#getchat">getChat</a> requests to check if the bot can use this method. Returns <em>True</em> on success.</p>', 'rst_description': 'Use this method to set a new group sticker set for a supergroup. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Use the field *can_set_sticker_set* optionally returned in :class:`aiogram.methods.get_chat.GetChat` requests to check if the bot can use this method. Returns :code:`True` on success.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target supergroup (in the format @supergroupusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target supergroup (in the format <code>@supergroupusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'String', 'required': True, 'description': 'Name of the sticker set to be set as the group sticker set', 'html_description': '<td>Name of the sticker set to be set as the group sticker set</td>', 'rst_description': 'Name of the sticker set to be set as the group sticker set\n', 'name': 'sticker_set_name', 'parsed_type': {'type': 'std', 'name': 'str'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Use the field can_set_sticker_set optionally returned in getChat requests to check if the bot can use this method. Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)
        :param sticker_set_name: Name of the sticker set to be set as the group sticker set
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = SetChatStickerSet(
            chat_id=chat_id,
            sticker_set_name=sticker_set_name,
        )
        return await self(call, request_timeout=request_timeout)

    async def set_chat_title(
        self,
        chat_id: Union[int, str],
        title: str,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to change the title of a chat. Titles can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'setchattitle', 'name': 'setChatTitle', 'description': "Use this method to change the title of a chat. Titles can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns True on success.", 'html_description': "<p>Use this method to change the title of a chat. Titles can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns <em>True</em> on success.</p>", 'rst_description': "Use this method to change the title of a chat. Titles can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns :code:`True` on success.", 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'String', 'required': True, 'description': 'New chat title, 1-128 characters', 'html_description': '<td>New chat title, 1-128 characters</td>', 'rst_description': 'New chat title, 1-128 characters\n', 'name': 'title', 'parsed_type': {'type': 'std', 'name': 'str'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param title: New chat title, 1-128 characters
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = SetChatTitle(
            chat_id=chat_id,
            title=title,
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
        Use this method to set the score of the specified user in a game message. On success, if the message is not an inline message, the :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned. Returns an error, if the new score is not greater than the user's current score in the chat and *force* is :code:`False`.

        Source: https://core.telegram.org/bots/api#{'anchor': 'setgamescore', 'name': 'setGameScore', 'description': "Use this method to set the score of the specified user in a game message. On success, if the message is not an inline message, the Message is returned, otherwise True is returned. Returns an error, if the new score is not greater than the user's current score in the chat and force is False.", 'html_description': '<p>Use this method to set the score of the specified user in a game message. On success, if the message is not an inline message, the <a href="#message">Message</a> is returned, otherwise <em>True</em> is returned. Returns an error, if the new score is not greater than the user\'s current score in the chat and <em>force</em> is <em>False</em>.</p>', 'rst_description': "Use this method to set the score of the specified user in a game message. On success, if the message is not an inline message, the :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned. Returns an error, if the new score is not greater than the user's current score in the chat and *force* is :code:`False`.", 'annotations': [{'type': 'Integer', 'required': True, 'description': 'User identifier', 'html_description': '<td>User identifier</td>', 'rst_description': 'User identifier\n', 'name': 'user_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Integer', 'required': True, 'description': 'New score, must be non-negative', 'html_description': '<td>New score, must be non-negative</td>', 'rst_description': 'New score, must be non-negative\n', 'name': 'score', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the high score is allowed to decrease. This can be useful when fixing mistakes or banning cheaters', 'html_description': '<td>Pass <em>True</em> if the high score is allowed to decrease. This can be useful when fixing mistakes or banning cheaters</td>', 'rst_description': 'Pass :code:`True` if the high score is allowed to decrease. This can be useful when fixing mistakes or banning cheaters\n', 'name': 'force', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True if the game message should not be automatically edited to include the current scoreboard', 'html_description': '<td>Pass <em>True</em> if the game message should not be automatically edited to include the current scoreboard</td>', 'rst_description': 'Pass :code:`True` if the game message should not be automatically edited to include the current scoreboard\n', 'name': 'disable_edit_message', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'Integer', 'required': False, 'description': 'Required if inline_message_id is not specified. Unique identifier for the target chat', 'html_description': '<td>Required if <em>inline_message_id</em> is not specified. Unique identifier for the target chat</td>', 'rst_description': 'Required if *inline_message_id* is not specified. Unique identifier for the target chat\n', 'name': 'chat_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Integer', 'required': False, 'description': 'Required if inline_message_id is not specified. Identifier of the sent message', 'html_description': '<td>Required if <em>inline_message_id</em> is not specified. Identifier of the sent message</td>', 'rst_description': 'Required if *inline_message_id* is not specified. Identifier of the sent message\n', 'name': 'message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'String', 'required': False, 'description': 'Required if chat_id and message_id are not specified. Identifier of the inline message', 'html_description': '<td>Required if <em>chat_id</em> and <em>message_id</em> are not specified. Identifier of the inline message</td>', 'rst_description': 'Required if *chat_id* and *message_id* are not specified. Identifier of the inline message\n', 'name': 'inline_message_id', 'parsed_type': {'type': 'std', 'name': 'str'}}], 'category': 'methods', 'returning': {'type': 'Message or True', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'Message'}}, {'type': 'std', 'name': 'bool', 'value': True}]}, 'description': "On success, if the message is not an inline message, the Message is returned, otherwise True is returned. Returns an error, if the new score is not greater than the user's current score in the chat and force is False."}, 'bases': ['TelegramMethod']}

        :param user_id: User identifier
        :param score: New score, must be non-negative
        :param force: Pass :code:`True` if the high score is allowed to decrease. This can be useful when fixing mistakes or banning cheaters
        :param disable_edit_message: Pass :code:`True` if the game message should not be automatically edited to include the current scoreboard
        :param chat_id: Required if *inline_message_id* is not specified. Unique identifier for the target chat
        :param message_id: Required if *inline_message_id* is not specified. Identifier of the sent message
        :param inline_message_id: Required if *chat_id* and *message_id* are not specified. Identifier of the inline message
        :param request_timeout: Request timeout
        :return: Returns an error, if the new score is not greater than the user's current score in the chat and *force* is :code:`False`.
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

    async def set_my_commands(
        self,
        commands: List[BotCommand],
        scope: Optional[BotCommandScope] = None,
        language_code: Optional[str] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to change the list of the bot's commands. See `this manual <https://core.telegram.org/bots/features#commands>`_ for more details about bot commands. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'setmycommands', 'name': 'setMyCommands', 'description': "Use this method to change the list of the bot's commands. See this manual for more details about bot commands. Returns True on success.", 'html_description': '<p>Use this method to change the list of the bot\'s commands. See <a href="/bots/features#commands">this manual</a> for more details about bot commands. Returns <em>True</em> on success.</p>', 'rst_description': "Use this method to change the list of the bot's commands. See `this manual <https://core.telegram.org/bots/features#commands>`_ for more details about bot commands. Returns :code:`True` on success.", 'annotations': [{'type': 'Array of BotCommand', 'required': True, 'description': "A JSON-serialized list of bot commands to be set as the list of the bot's commands. At most 100 commands can be specified.", 'html_description': "<td>A JSON-serialized list of bot commands to be set as the list of the bot's commands. At most 100 commands can be specified.</td>", 'rst_description': "A JSON-serialized list of bot commands to be set as the list of the bot's commands. At most 100 commands can be specified.\n", 'name': 'commands', 'parsed_type': {'type': 'array', 'items': {'type': 'entity', 'references': {'category': 'types', 'name': 'BotCommand'}}}}, {'type': 'BotCommandScope', 'required': False, 'description': 'A JSON-serialized object, describing scope of users for which the commands are relevant. Defaults to BotCommandScopeDefault.', 'html_description': '<td>A JSON-serialized object, describing scope of users for which the commands are relevant. Defaults to <a href="#botcommandscopedefault">BotCommandScopeDefault</a>.</td>', 'rst_description': 'A JSON-serialized object, describing scope of users for which the commands are relevant. Defaults to :class:`aiogram.types.bot_command_scope_default.BotCommandScopeDefault`.\n', 'name': 'scope', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'BotCommandScope'}}}, {'type': 'String', 'required': False, 'description': 'A two-letter ISO 639-1 language code. If empty, commands will be applied to all users from the given scope, for whose language there are no dedicated commands', 'html_description': '<td>A two-letter ISO 639-1 language code. If empty, commands will be applied to all users from the given scope, for whose language there are no dedicated commands</td>', 'rst_description': 'A two-letter ISO 639-1 language code. If empty, commands will be applied to all users from the given scope, for whose language there are no dedicated commands\n', 'name': 'language_code', 'parsed_type': {'type': 'std', 'name': 'str'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param commands: A JSON-serialized list of bot commands to be set as the list of the bot's commands. At most 100 commands can be specified.
        :param scope: A JSON-serialized object, describing scope of users for which the commands are relevant. Defaults to :class:`aiogram.types.bot_command_scope_default.BotCommandScopeDefault`.
        :param language_code: A two-letter ISO 639-1 language code. If empty, commands will be applied to all users from the given scope, for whose language there are no dedicated commands
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = SetMyCommands(
            commands=commands,
            scope=scope,
            language_code=language_code,
        )
        return await self(call, request_timeout=request_timeout)

    async def set_my_default_administrator_rights(
        self,
        rights: Optional[ChatAdministratorRights] = None,
        for_channels: Optional[bool] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to change the default administrator rights requested by the bot when it's added as an administrator to groups or channels. These rights will be suggested to users, but they are are free to modify the list before adding the bot. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'setmydefaultadministratorrights', 'name': 'setMyDefaultAdministratorRights', 'description': "Use this method to change the default administrator rights requested by the bot when it's added as an administrator to groups or channels. These rights will be suggested to users, but they are are free to modify the list before adding the bot. Returns True on success.", 'html_description': "<p>Use this method to change the default administrator rights requested by the bot when it's added as an administrator to groups or channels. These rights will be suggested to users, but they are are free to modify the list before adding the bot. Returns <em>True</em> on success.</p>", 'rst_description': "Use this method to change the default administrator rights requested by the bot when it's added as an administrator to groups or channels. These rights will be suggested to users, but they are are free to modify the list before adding the bot. Returns :code:`True` on success.", 'annotations': [{'type': 'ChatAdministratorRights', 'required': False, 'description': 'A JSON-serialized object describing new default administrator rights. If not specified, the default administrator rights will be cleared.', 'html_description': '<td>A JSON-serialized object describing new default administrator rights. If not specified, the default administrator rights will be cleared.</td>', 'rst_description': 'A JSON-serialized object describing new default administrator rights. If not specified, the default administrator rights will be cleared.\n', 'name': 'rights', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'ChatAdministratorRights'}}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True to change the default administrator rights of the bot in channels. Otherwise, the default administrator rights of the bot for groups and supergroups will be changed.', 'html_description': '<td>Pass <em>True</em> to change the default administrator rights of the bot in channels. Otherwise, the default administrator rights of the bot for groups and supergroups will be changed.</td>', 'rst_description': 'Pass :code:`True` to change the default administrator rights of the bot in channels. Otherwise, the default administrator rights of the bot for groups and supergroups will be changed.\n', 'name': 'for_channels', 'parsed_type': {'type': 'std', 'name': 'bool'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param rights: A JSON-serialized object describing new default administrator rights. If not specified, the default administrator rights will be cleared.
        :param for_channels: Pass :code:`True` to change the default administrator rights of the bot in channels. Otherwise, the default administrator rights of the bot for groups and supergroups will be changed.
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = SetMyDefaultAdministratorRights(
            rights=rights,
            for_channels=for_channels,
        )
        return await self(call, request_timeout=request_timeout)

    async def set_passport_data_errors(
        self,
        user_id: int,
        errors: List[PassportElementError],
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Informs a user that some of the Telegram Passport elements they provided contains errors. The user will not be able to re-submit their Passport to you until the errors are fixed (the contents of the field for which you returned the error must change). Returns :code:`True` on success.
        Use this if the data submitted by the user doesn't satisfy the standards your service requires for any reason. For example, if a birthday date seems invalid, a submitted document is blurry, a scan shows evidence of tampering, etc. Supply some details in the error message to make sure the user knows how to correct the issues.

        Source: https://core.telegram.org/bots/api#{'anchor': 'setpassportdataerrors', 'name': 'setPassportDataErrors', 'description': "Informs a user that some of the Telegram Passport elements they provided contains errors. The user will not be able to re-submit their Passport to you until the errors are fixed (the contents of the field for which you returned the error must change). Returns True on success.\nUse this if the data submitted by the user doesn't satisfy the standards your service requires for any reason. For example, if a birthday date seems invalid, a submitted document is blurry, a scan shows evidence of tampering, etc. Supply some details in the error message to make sure the user knows how to correct the issues.", 'html_description': "<p>Informs a user that some of the Telegram Passport elements they provided contains errors. The user will not be able to re-submit their Passport to you until the errors are fixed (the contents of the field for which you returned the error must change). Returns <em>True</em> on success.</p><p>Use this if the data submitted by the user doesn't satisfy the standards your service requires for any reason. For example, if a birthday date seems invalid, a submitted document is blurry, a scan shows evidence of tampering, etc. Supply some details in the error message to make sure the user knows how to correct the issues.</p>", 'rst_description': "Informs a user that some of the Telegram Passport elements they provided contains errors. The user will not be able to re-submit their Passport to you until the errors are fixed (the contents of the field for which you returned the error must change). Returns :code:`True` on success.\nUse this if the data submitted by the user doesn't satisfy the standards your service requires for any reason. For example, if a birthday date seems invalid, a submitted document is blurry, a scan shows evidence of tampering, etc. Supply some details in the error message to make sure the user knows how to correct the issues.", 'annotations': [{'type': 'Integer', 'required': True, 'description': 'User identifier', 'html_description': '<td>User identifier</td>', 'rst_description': 'User identifier\n', 'name': 'user_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Array of PassportElementError', 'required': True, 'description': 'A JSON-serialized array describing the errors', 'html_description': '<td>A JSON-serialized array describing the errors</td>', 'rst_description': 'A JSON-serialized array describing the errors\n', 'name': 'errors', 'parsed_type': {'type': 'array', 'items': {'type': 'entity', 'references': {'category': 'types', 'name': 'PassportElementError'}}}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'The user will not be able to re-submit their Passport to you until the errors are fixed (the contents of the field for which you returned the error must change). Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param user_id: User identifier
        :param errors: A JSON-serialized array describing the errors
        :param request_timeout: Request timeout
        :return: Supply some details in the error message to make sure the user knows how to correct the issues.
        """

        call = SetPassportDataErrors(
            user_id=user_id,
            errors=errors,
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

        Source: https://core.telegram.org/bots/api#{'anchor': 'setstickerpositioninset', 'name': 'setStickerPositionInSet', 'description': 'Use this method to move a sticker in a set created by the bot to a specific position. Returns True on success.', 'html_description': '<p>Use this method to move a sticker in a set created by the bot to a specific position. Returns <em>True</em> on success.</p>', 'rst_description': 'Use this method to move a sticker in a set created by the bot to a specific position. Returns :code:`True` on success.', 'annotations': [{'type': 'String', 'required': True, 'description': 'File identifier of the sticker', 'html_description': '<td>File identifier of the sticker</td>', 'rst_description': 'File identifier of the sticker\n', 'name': 'sticker', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'Integer', 'required': True, 'description': 'New sticker position in the set, zero-based', 'html_description': '<td>New sticker position in the set, zero-based</td>', 'rst_description': 'New sticker position in the set, zero-based\n', 'name': 'position', 'parsed_type': {'type': 'std', 'name': 'int'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param sticker: File identifier of the sticker
        :param position: New sticker position in the set, zero-based
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = SetStickerPositionInSet(
            sticker=sticker,
            position=position,
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
        Use this method to set the thumbnail of a sticker set. Animated thumbnails can be set for animated sticker sets only. Video thumbnails can be set only for video sticker sets only. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'setstickersetthumb', 'name': 'setStickerSetThumb', 'description': 'Use this method to set the thumbnail of a sticker set. Animated thumbnails can be set for animated sticker sets only. Video thumbnails can be set only for video sticker sets only. Returns True on success.', 'html_description': '<p>Use this method to set the thumbnail of a sticker set. Animated thumbnails can be set for animated sticker sets only. Video thumbnails can be set only for video sticker sets only. Returns <em>True</em> on success.</p>', 'rst_description': 'Use this method to set the thumbnail of a sticker set. Animated thumbnails can be set for animated sticker sets only. Video thumbnails can be set only for video sticker sets only. Returns :code:`True` on success.', 'annotations': [{'type': 'String', 'required': True, 'description': 'Sticker set name', 'html_description': '<td>Sticker set name</td>', 'rst_description': 'Sticker set name\n', 'name': 'name', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'Integer', 'required': True, 'description': 'User identifier of the sticker set owner', 'html_description': '<td>User identifier of the sticker set owner</td>', 'rst_description': 'User identifier of the sticker set owner\n', 'name': 'user_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'InputFile or String', 'required': False, 'description': "A PNG image with the thumbnail, must be up to 128 kilobytes in size and have width and height exactly 100px, or a TGS animation with the thumbnail up to 32 kilobytes in size; see https://core.telegram.org/stickers#animated-sticker-requirements for animated sticker technical requirements, or a WEBM video with the thumbnail up to 32 kilobytes in size; see https://core.telegram.org/stickers#video-sticker-requirements for video sticker technical requirements. Pass a file_id as a String to send a file that already exists on the Telegram servers, pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. More information on Sending Files. Animated sticker set thumbnails can't be uploaded via HTTP URL.", 'html_description': '<td>A <strong>PNG</strong> image with the thumbnail, must be up to 128 kilobytes in size and have width and height exactly 100px, or a <strong>TGS</strong> animation with the thumbnail up to 32 kilobytes in size; see <a href="/stickers#animated-sticker-requirements"/><a href="https://core.telegram.org/stickers#animated-sticker-requirements">https://core.telegram.org/stickers#animated-sticker-requirements</a> for animated sticker technical requirements, or a <strong>WEBM</strong> video with the thumbnail up to 32 kilobytes in size; see <a href="/stickers#video-sticker-requirements"/><a href="https://core.telegram.org/stickers#video-sticker-requirements">https://core.telegram.org/stickers#video-sticker-requirements</a> for video sticker technical requirements. Pass a <em>file_id</em> as a String to send a file that already exists on the Telegram servers, pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. <a href="#sending-files">More information on Sending Files &#187;</a>. Animated sticker set thumbnails can\'t be uploaded via HTTP URL.</td>', 'rst_description': "A **PNG** image with the thumbnail, must be up to 128 kilobytes in size and have width and height exactly 100px, or a **TGS** animation with the thumbnail up to 32 kilobytes in size; see `https://core.telegram.org/stickers#animated-sticker-requirements <https://core.telegram.org/stickers#animated-sticker-requirements>`_`https://core.telegram.org/stickers#animated-sticker-requirements <https://core.telegram.org/stickers#animated-sticker-requirements>`_ for animated sticker technical requirements, or a **WEBM** video with the thumbnail up to 32 kilobytes in size; see `https://core.telegram.org/stickers#video-sticker-requirements <https://core.telegram.org/stickers#video-sticker-requirements>`_`https://core.telegram.org/stickers#video-sticker-requirements <https://core.telegram.org/stickers#video-sticker-requirements>`_ for video sticker technical requirements. Pass a *file_id* as a String to send a file that already exists on the Telegram servers, pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`. Animated sticker set thumbnails can't be uploaded via HTTP URL.\n", 'name': 'thumb', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'InputFile'}}, {'type': 'std', 'name': 'str'}]}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param name: Sticker set name
        :param user_id: User identifier of the sticker set owner
        :param thumb: A **PNG** image with the thumbnail, must be up to 128 kilobytes in size and have width and height exactly 100px, or a **TGS** animation with the thumbnail up to 32 kilobytes in size; see `https://core.telegram.org/stickers#animated-sticker-requirements <https://core.telegram.org/stickers#animated-sticker-requirements>`_`https://core.telegram.org/stickers#animated-sticker-requirements <https://core.telegram.org/stickers#animated-sticker-requirements>`_ for animated sticker technical requirements, or a **WEBM** video with the thumbnail up to 32 kilobytes in size; see `https://core.telegram.org/stickers#video-sticker-requirements <https://core.telegram.org/stickers#video-sticker-requirements>`_`https://core.telegram.org/stickers#video-sticker-requirements <https://core.telegram.org/stickers#video-sticker-requirements>`_ for video sticker technical requirements. Pass a *file_id* as a String to send a file that already exists on the Telegram servers, pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`. Animated sticker set thumbnails can't be uploaded via HTTP URL.
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = SetStickerSetThumb(
            name=name,
            user_id=user_id,
            thumb=thumb,
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
        secret_token: Optional[str] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to specify a URL and receive incoming updates via an outgoing webhook. Whenever there is an update for the bot, we will send an HTTPS POST request to the specified URL, containing a JSON-serialized :class:`aiogram.types.update.Update`. In case of an unsuccessful request, we will give up after a reasonable amount of attempts. Returns :code:`True` on success.
        If you'd like to make sure that the webhook was set by you, you can specify secret data in the parameter *secret_token*. If specified, the request will contain a header 'X-Telegram-Bot-Api-Secret-Token' with the secret token as content.

         **Notes**

         **1.** You will not be able to receive updates using :class:`aiogram.methods.get_updates.GetUpdates` for as long as an outgoing webhook is set up.

         **2.** To use a self-signed certificate, you need to upload your `public key certificate <https://core.telegram.org/bots/self-signed>`_ using *certificate* parameter. Please upload as InputFile, sending a String will not work.

         **3.** Ports currently supported *for webhooks*: **443, 80, 88, 8443**.
         If you're having any trouble setting up webhooks, please check out this `amazing guide to webhooks <https://core.telegram.org/bots/webhooks>`_.

        Source: https://core.telegram.org/bots/api#{'anchor': 'setwebhook', 'name': 'setWebhook', 'description': "Use this method to specify a URL and receive incoming updates via an outgoing webhook. Whenever there is an update for the bot, we will send an HTTPS POST request to the specified URL, containing a JSON-serialized Update. In case of an unsuccessful request, we will give up after a reasonable amount of attempts. Returns True on success.\nIf you'd like to make sure that the webhook was set by you, you can specify secret data in the parameter secret_token. If specified, the request will contain a header 'X-Telegram-Bot-Api-Secret-Token' with the secret token as content.\nNotes\n1. You will not be able to receive updates using getUpdates for as long as an outgoing webhook is set up.\n2. To use a self-signed certificate, you need to upload your public key certificate using certificate parameter. Please upload as InputFile, sending a String will not work.\n3. Ports currently supported for webhooks: 443, 80, 88, 8443.\nIf you're having any trouble setting up webhooks, please check out this amazing guide to webhooks.", 'html_description': '<p>Use this method to specify a URL and receive incoming updates via an outgoing webhook. Whenever there is an update for the bot, we will send an HTTPS POST request to the specified URL, containing a JSON-serialized <a href="#update">Update</a>. In case of an unsuccessful request, we will give up after a reasonable amount of attempts. Returns <em>True</em> on success.</p><p>If you\'d like to make sure that the webhook was set by you, you can specify secret data in the parameter <em>secret_token</em>. If specified, the request will contain a header &#8220;X-Telegram-Bot-Api-Secret-Token&#8221; with the secret token as content.</p><blockquote>\n<p><strong>Notes</strong><br/>\n<strong>1.</strong> You will not be able to receive updates using <a href="#getupdates">getUpdates</a> for as long as an outgoing webhook is set up.<br/>\n<strong>2.</strong> To use a self-signed certificate, you need to upload your <a href="/bots/self-signed">public key certificate</a> using <em>certificate</em> parameter. Please upload as InputFile, sending a String will not work.<br/>\n<strong>3.</strong> Ports currently supported <em>for webhooks</em>: <strong>443, 80, 88, 8443</strong>.</p>\n<p>If you\'re having any trouble setting up webhooks, please check out this <a href="/bots/webhooks">amazing guide to webhooks</a>.</p>\n</blockquote>', 'rst_description': "Use this method to specify a URL and receive incoming updates via an outgoing webhook. Whenever there is an update for the bot, we will send an HTTPS POST request to the specified URL, containing a JSON-serialized :class:`aiogram.types.update.Update`. In case of an unsuccessful request, we will give up after a reasonable amount of attempts. Returns :code:`True` on success.\nIf you'd like to make sure that the webhook was set by you, you can specify secret data in the parameter *secret_token*. If specified, the request will contain a header 'X-Telegram-Bot-Api-Secret-Token' with the secret token as content.\n\n **Notes**\n \n **1.** You will not be able to receive updates using :class:`aiogram.methods.get_updates.GetUpdates` for as long as an outgoing webhook is set up.\n \n **2.** To use a self-signed certificate, you need to upload your `public key certificate <https://core.telegram.org/bots/self-signed>`_ using *certificate* parameter. Please upload as InputFile, sending a String will not work.\n \n **3.** Ports currently supported *for webhooks*: **443, 80, 88, 8443**.\n If you're having any trouble setting up webhooks, please check out this `amazing guide to webhooks <https://core.telegram.org/bots/webhooks>`_.", 'annotations': [{'type': 'String', 'required': True, 'description': 'HTTPS URL to send updates to. Use an empty string to remove webhook integration', 'html_description': '<td>HTTPS URL to send updates to. Use an empty string to remove webhook integration</td>', 'rst_description': 'HTTPS URL to send updates to. Use an empty string to remove webhook integration\n', 'name': 'url', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'InputFile', 'required': False, 'description': 'Upload your public key certificate so that the root certificate in use can be checked. See our self-signed guide for details.', 'html_description': '<td>Upload your public key certificate so that the root certificate in use can be checked. See our <a href="/bots/self-signed">self-signed guide</a> for details.</td>', 'rst_description': 'Upload your public key certificate so that the root certificate in use can be checked. See our `self-signed guide <https://core.telegram.org/bots/self-signed>`_ for details.\n', 'name': 'certificate', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'InputFile'}}}, {'type': 'String', 'required': False, 'description': 'The fixed IP address which will be used to send webhook requests instead of the IP address resolved through DNS', 'html_description': '<td>The fixed IP address which will be used to send webhook requests instead of the IP address resolved through DNS</td>', 'rst_description': 'The fixed IP address which will be used to send webhook requests instead of the IP address resolved through DNS\n', 'name': 'ip_address', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'Integer', 'required': False, 'description': "The maximum allowed number of simultaneous HTTPS connections to the webhook for update delivery, 1-100. Defaults to 40. Use lower values to limit the load on your bot's server, and higher values to increase your bot's throughput.", 'html_description': "<td>The maximum allowed number of simultaneous HTTPS connections to the webhook for update delivery, 1-100. Defaults to <em>40</em>. Use lower values to limit the load on your bot's server, and higher values to increase your bot's throughput.</td>", 'rst_description': "The maximum allowed number of simultaneous HTTPS connections to the webhook for update delivery, 1-100. Defaults to *40*. Use lower values to limit the load on your bot's server, and higher values to increase your bot's throughput.\n", 'name': 'max_connections', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Array of String', 'required': False, 'description': "A JSON-serialized list of the update types you want your bot to receive. For example, specify ['message', 'edited_channel_post', 'callback_query'] to only receive updates of these types. See Update for a complete list of available update types. Specify an empty list to receive all update types except chat_member (default). If not specified, the previous setting will be used.\nPlease note that this parameter doesn't affect updates created before the call to the setWebhook, so unwanted updates may be received for a short period of time.", 'html_description': '<td>A JSON-serialized list of the update types you want your bot to receive. For example, specify [&#8220;message&#8221;, &#8220;edited_channel_post&#8221;, &#8220;callback_query&#8221;] to only receive updates of these types. See <a href="#update">Update</a> for a complete list of available update types. Specify an empty list to receive all update types except <em>chat_member</em> (default). If not specified, the previous setting will be used.<br/>\nPlease note that this parameter doesn\'t affect updates created before the call to the setWebhook, so unwanted updates may be received for a short period of time.</td>', 'rst_description': "A JSON-serialized list of the update types you want your bot to receive. For example, specify ['message', 'edited_channel_post', 'callback_query'] to only receive updates of these types. See :class:`aiogram.types.update.Update` for a complete list of available update types. Specify an empty list to receive all update types except *chat_member* (default). If not specified, the previous setting will be used.\n\nPlease note that this parameter doesn't affect updates created before the call to the setWebhook, so unwanted updates may be received for a short period of time.\n", 'name': 'allowed_updates', 'parsed_type': {'type': 'array', 'items': {'type': 'std', 'name': 'str'}}}, {'type': 'Boolean', 'required': False, 'description': 'Pass True to drop all pending updates', 'html_description': '<td>Pass <em>True</em> to drop all pending updates</td>', 'rst_description': 'Pass :code:`True` to drop all pending updates\n', 'name': 'drop_pending_updates', 'parsed_type': {'type': 'std', 'name': 'bool'}}, {'type': 'String', 'required': False, 'description': "A secret token to be sent in a header 'X-Telegram-Bot-Api-Secret-Token' in every webhook request, 1-256 characters. Only characters A-Z, a-z, 0-9, _ and - are allowed. The header is useful to ensure that the request comes from a webhook set by you.", 'html_description': '<td>A secret token to be sent in a header &#8220;X-Telegram-Bot-Api-Secret-Token&#8221; in every webhook request, 1-256 characters. Only characters <code>A-Z</code>, <code>a-z</code>, <code>0-9</code>, <code>_</code> and <code>-</code> are allowed. The header is useful to ensure that the request comes from a webhook set by you.</td>', 'rst_description': "A secret token to be sent in a header 'X-Telegram-Bot-Api-Secret-Token' in every webhook request, 1-256 characters. Only characters :code:`A-Z`, :code:`a-z`, :code:`0-9`, :code:`_` and :code:`-` are allowed. The header is useful to ensure that the request comes from a webhook set by you.\n", 'name': 'secret_token', 'parsed_type': {'type': 'std', 'name': 'str'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param url: HTTPS URL to send updates to. Use an empty string to remove webhook integration
        :param certificate: Upload your public key certificate so that the root certificate in use can be checked. See our `self-signed guide <https://core.telegram.org/bots/self-signed>`_ for details.
        :param ip_address: The fixed IP address which will be used to send webhook requests instead of the IP address resolved through DNS
        :param max_connections: The maximum allowed number of simultaneous HTTPS connections to the webhook for update delivery, 1-100. Defaults to *40*. Use lower values to limit the load on your bot's server, and higher values to increase your bot's throughput.
        :param allowed_updates: A JSON-serialized list of the update types you want your bot to receive. For example, specify ['message', 'edited_channel_post', 'callback_query'] to only receive updates of these types. See :class:`aiogram.types.update.Update` for a complete list of available update types. Specify an empty list to receive all update types except *chat_member* (default). If not specified, the previous setting will be used.
        :param drop_pending_updates: Pass :code:`True` to drop all pending updates
        :param secret_token: A secret token to be sent in a header 'X-Telegram-Bot-Api-Secret-Token' in every webhook request, 1-256 characters. Only characters :code:`A-Z`, :code:`a-z`, :code:`0-9`, :code:`_` and :code:`-` are allowed. The header is useful to ensure that the request comes from a webhook set by you.
        :param request_timeout: Request timeout
        :return: Please upload as InputFile, sending a String will not work.
        """

        call = SetWebhook(
            url=url,
            certificate=certificate,
            ip_address=ip_address,
            max_connections=max_connections,
            allowed_updates=allowed_updates,
            drop_pending_updates=drop_pending_updates,
            secret_token=secret_token,
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
        Use this method to stop updating a live location message before *live_period* expires. On success, if the message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned.

        Source: https://core.telegram.org/bots/api#{'anchor': 'stopmessagelivelocation', 'name': 'stopMessageLiveLocation', 'description': 'Use this method to stop updating a live location message before live_period expires. On success, if the message is not an inline message, the edited Message is returned, otherwise True is returned.', 'html_description': '<p>Use this method to stop updating a live location message before <em>live_period</em> expires. On success, if the message is not an inline message, the edited <a href="#message">Message</a> is returned, otherwise <em>True</em> is returned.</p>', 'rst_description': 'Use this method to stop updating a live location message before *live_period* expires. On success, if the message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned.', 'annotations': [{'type': 'Integer or String', 'required': False, 'description': 'Required if inline_message_id is not specified. Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Required if <em>inline_message_id</em> is not specified. Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': False, 'description': 'Required if inline_message_id is not specified. Identifier of the message with live location to stop', 'html_description': '<td>Required if <em>inline_message_id</em> is not specified. Identifier of the message with live location to stop</td>', 'rst_description': 'Required if *inline_message_id* is not specified. Identifier of the message with live location to stop\n', 'name': 'message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'String', 'required': False, 'description': 'Required if chat_id and message_id are not specified. Identifier of the inline message', 'html_description': '<td>Required if <em>chat_id</em> and <em>message_id</em> are not specified. Identifier of the inline message</td>', 'rst_description': 'Required if *chat_id* and *message_id* are not specified. Identifier of the inline message\n', 'name': 'inline_message_id', 'parsed_type': {'type': 'std', 'name': 'str'}}, {'type': 'InlineKeyboardMarkup', 'required': False, 'description': 'A JSON-serialized object for a new inline keyboard.', 'html_description': '<td>A JSON-serialized object for a new <a href="/bots/features#inline-keyboards">inline keyboard</a>.</td>', 'rst_description': 'A JSON-serialized object for a new `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_.\n', 'name': 'reply_markup', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'InlineKeyboardMarkup'}}}], 'category': 'methods', 'returning': {'type': 'Message or True', 'parsed_type': {'type': 'union', 'items': [{'type': 'entity', 'references': {'category': 'types', 'name': 'Message'}}, {'type': 'std', 'name': 'bool', 'value': True}]}, 'description': 'On success, if the message is not an inline message, the edited Message is returned, otherwise True is returned.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param message_id: Required if *inline_message_id* is not specified. Identifier of the message with live location to stop
        :param inline_message_id: Required if *chat_id* and *message_id* are not specified. Identifier of the inline message
        :param reply_markup: A JSON-serialized object for a new `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_.
        :param request_timeout: Request timeout
        :return: On success, if the message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned.
        """

        call = StopMessageLiveLocation(
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
        Use this method to stop a poll which was sent by the bot. On success, the stopped :class:`aiogram.types.poll.Poll` is returned.

        Source: https://core.telegram.org/bots/api#{'anchor': 'stoppoll', 'name': 'stopPoll', 'description': 'Use this method to stop a poll which was sent by the bot. On success, the stopped Poll is returned.', 'html_description': '<p>Use this method to stop a poll which was sent by the bot. On success, the stopped <a href="#poll">Poll</a> is returned.</p>', 'rst_description': 'Use this method to stop a poll which was sent by the bot. On success, the stopped :class:`aiogram.types.poll.Poll` is returned.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': True, 'description': 'Identifier of the original message with the poll', 'html_description': '<td>Identifier of the original message with the poll</td>', 'rst_description': 'Identifier of the original message with the poll\n', 'name': 'message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'InlineKeyboardMarkup', 'required': False, 'description': 'A JSON-serialized object for a new message inline keyboard.', 'html_description': '<td>A JSON-serialized object for a new message <a href="/bots/features#inline-keyboards">inline keyboard</a>.</td>', 'rst_description': 'A JSON-serialized object for a new message `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_.\n', 'name': 'reply_markup', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'InlineKeyboardMarkup'}}}], 'category': 'methods', 'returning': {'type': 'Poll', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'Poll'}}, 'description': 'On success, the stopped Poll is returned.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param message_id: Identifier of the original message with the poll
        :param reply_markup: A JSON-serialized object for a new message `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_.
        :param request_timeout: Request timeout
        :return: On success, the stopped :class:`aiogram.types.poll.Poll` is returned.
        """

        call = StopPoll(
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=reply_markup,
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

        Source: https://core.telegram.org/bots/api#{'anchor': 'unbanchatmember', 'name': 'unbanChatMember', 'description': "Use this method to unban a previously banned user in a supergroup or channel. The user will not return to the group or channel automatically, but will be able to join via link, etc. The bot must be an administrator for this to work. By default, this method guarantees that after the call the user is not a member of the chat, but will be able to join it. So if the user is a member of the chat they will also be removed from the chat. If you don't want this, use the parameter only_if_banned. Returns True on success.", 'html_description': "<p>Use this method to unban a previously banned user in a supergroup or channel. The user will <strong>not</strong> return to the group or channel automatically, but will be able to join via link, etc. The bot must be an administrator for this to work. By default, this method guarantees that after the call the user is not a member of the chat, but will be able to join it. So if the user is a member of the chat they will also be <strong>removed</strong> from the chat. If you don't want this, use the parameter <em>only_if_banned</em>. Returns <em>True</em> on success.</p>", 'rst_description': "Use this method to unban a previously banned user in a supergroup or channel. The user will **not** return to the group or channel automatically, but will be able to join via link, etc. The bot must be an administrator for this to work. By default, this method guarantees that after the call the user is not a member of the chat, but will be able to join it. So if the user is a member of the chat they will also be **removed** from the chat. If you don't want this, use the parameter *only_if_banned*. Returns :code:`True` on success.", 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target group or username of the target supergroup or channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target group or username of the target supergroup or channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target group or username of the target supergroup or channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': True, 'description': 'Unique identifier of the target user', 'html_description': '<td>Unique identifier of the target user</td>', 'rst_description': 'Unique identifier of the target user\n', 'name': 'user_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'Boolean', 'required': False, 'description': 'Do nothing if the user is not banned', 'html_description': '<td>Do nothing if the user is not banned</td>', 'rst_description': 'Do nothing if the user is not banned\n', 'name': 'only_if_banned', 'parsed_type': {'type': 'std', 'name': 'bool'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'The user will not return to the group or channel automatically, but will be able to join via link, etc. Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target group or username of the target supergroup or channel (in the format :code:`@channelusername`)
        :param user_id: Unique identifier of the target user
        :param only_if_banned: Do nothing if the user is not banned
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = UnbanChatMember(
            chat_id=chat_id,
            user_id=user_id,
            only_if_banned=only_if_banned,
        )
        return await self(call, request_timeout=request_timeout)

    async def unban_chat_sender_chat(
        self,
        chat_id: Union[int, str],
        sender_chat_id: int,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to unban a previously banned channel chat in a supergroup or channel. The bot must be an administrator for this to work and must have the appropriate administrator rights. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'unbanchatsenderchat', 'name': 'unbanChatSenderChat', 'description': 'Use this method to unban a previously banned channel chat in a supergroup or channel. The bot must be an administrator for this to work and must have the appropriate administrator rights. Returns True on success.', 'html_description': '<p>Use this method to unban a previously banned channel chat in a supergroup or channel. The bot must be an administrator for this to work and must have the appropriate administrator rights. Returns <em>True</em> on success.</p>', 'rst_description': 'Use this method to unban a previously banned channel chat in a supergroup or channel. The bot must be an administrator for this to work and must have the appropriate administrator rights. Returns :code:`True` on success.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': True, 'description': 'Unique identifier of the target sender chat', 'html_description': '<td>Unique identifier of the target sender chat</td>', 'rst_description': 'Unique identifier of the target sender chat\n', 'name': 'sender_chat_id', 'parsed_type': {'type': 'std', 'name': 'int'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param sender_chat_id: Unique identifier of the target sender chat
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = UnbanChatSenderChat(
            chat_id=chat_id,
            sender_chat_id=sender_chat_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def unpin_all_chat_messages(
        self,
        chat_id: Union[int, str],
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to clear the list of pinned messages in a chat. If the chat is not a private chat, the bot must be an administrator in the chat for this to work and must have the 'can_pin_messages' administrator right in a supergroup or 'can_edit_messages' administrator right in a channel. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'unpinallchatmessages', 'name': 'unpinAllChatMessages', 'description': "Use this method to clear the list of pinned messages in a chat. If the chat is not a private chat, the bot must be an administrator in the chat for this to work and must have the 'can_pin_messages' administrator right in a supergroup or 'can_edit_messages' administrator right in a channel. Returns True on success.", 'html_description': "<p>Use this method to clear the list of pinned messages in a chat. If the chat is not a private chat, the bot must be an administrator in the chat for this to work and must have the 'can_pin_messages' administrator right in a supergroup or 'can_edit_messages' administrator right in a channel. Returns <em>True</em> on success.</p>", 'rst_description': "Use this method to clear the list of pinned messages in a chat. If the chat is not a private chat, the bot must be an administrator in the chat for this to work and must have the 'can_pin_messages' administrator right in a supergroup or 'can_edit_messages' administrator right in a channel. Returns :code:`True` on success.", 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = UnpinAllChatMessages(
            chat_id=chat_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def unpin_all_forum_topic_messages(
        self,
        chat_id: Union[int, str],
        message_thread_id: int,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to clear the list of pinned messages in a forum topic. The bot must be an administrator in the chat for this to work and must have the *can_pin_messages* administrator right in the supergroup. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'unpinallforumtopicmessages', 'name': 'unpinAllForumTopicMessages', 'description': 'Use this method to clear the list of pinned messages in a forum topic. The bot must be an administrator in the chat for this to work and must have the can_pin_messages administrator right in the supergroup. Returns True on success.', 'html_description': '<p>Use this method to clear the list of pinned messages in a forum topic. The bot must be an administrator in the chat for this to work and must have the <em>can_pin_messages</em> administrator right in the supergroup. Returns <em>True</em> on success.</p>', 'rst_description': 'Use this method to clear the list of pinned messages in a forum topic. The bot must be an administrator in the chat for this to work and must have the *can_pin_messages* administrator right in the supergroup. Returns :code:`True` on success.', 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target supergroup (in the format @supergroupusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target supergroup (in the format <code>@supergroupusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': True, 'description': 'Unique identifier for the target message thread of the forum topic', 'html_description': '<td>Unique identifier for the target message thread of the forum topic</td>', 'rst_description': 'Unique identifier for the target message thread of the forum topic\n', 'name': 'message_thread_id', 'parsed_type': {'type': 'std', 'name': 'int'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)
        :param message_thread_id: Unique identifier for the target message thread of the forum topic
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = UnpinAllForumTopicMessages(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def unpin_chat_message(
        self,
        chat_id: Union[int, str],
        message_id: Optional[int] = None,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to remove a message from the list of pinned messages in a chat. If the chat is not a private chat, the bot must be an administrator in the chat for this to work and must have the 'can_pin_messages' administrator right in a supergroup or 'can_edit_messages' administrator right in a channel. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'unpinchatmessage', 'name': 'unpinChatMessage', 'description': "Use this method to remove a message from the list of pinned messages in a chat. If the chat is not a private chat, the bot must be an administrator in the chat for this to work and must have the 'can_pin_messages' administrator right in a supergroup or 'can_edit_messages' administrator right in a channel. Returns True on success.", 'html_description': "<p>Use this method to remove a message from the list of pinned messages in a chat. If the chat is not a private chat, the bot must be an administrator in the chat for this to work and must have the 'can_pin_messages' administrator right in a supergroup or 'can_edit_messages' administrator right in a channel. Returns <em>True</em> on success.</p>", 'rst_description': "Use this method to remove a message from the list of pinned messages in a chat. If the chat is not a private chat, the bot must be an administrator in the chat for this to work and must have the 'can_pin_messages' administrator right in a supergroup or 'can_edit_messages' administrator right in a channel. Returns :code:`True` on success.", 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target channel (in the format @channelusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target channel (in the format <code>@channelusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'Integer', 'required': False, 'description': 'Identifier of a message to unpin. If not specified, the most recent pinned message (by sending date) will be unpinned.', 'html_description': '<td>Identifier of a message to unpin. If not specified, the most recent pinned message (by sending date) will be unpinned.</td>', 'rst_description': 'Identifier of a message to unpin. If not specified, the most recent pinned message (by sending date) will be unpinned.\n', 'name': 'message_id', 'parsed_type': {'type': 'std', 'name': 'int'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param message_id: Identifier of a message to unpin. If not specified, the most recent pinned message (by sending date) will be unpinned.
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = UnpinChatMessage(
            chat_id=chat_id,
            message_id=message_id,
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

        Source: https://core.telegram.org/bots/api#{'anchor': 'uploadstickerfile', 'name': 'uploadStickerFile', 'description': 'Use this method to upload a .PNG file with a sticker for later use in createNewStickerSet and addStickerToSet methods (can be used multiple times). Returns the uploaded File on success.', 'html_description': '<p>Use this method to upload a .PNG file with a sticker for later use in <em>createNewStickerSet</em> and <em>addStickerToSet</em> methods (can be used multiple times). Returns the uploaded <a href="#file">File</a> on success.</p>', 'rst_description': 'Use this method to upload a .PNG file with a sticker for later use in *createNewStickerSet* and *addStickerToSet* methods (can be used multiple times). Returns the uploaded :class:`aiogram.types.file.File` on success.', 'annotations': [{'type': 'Integer', 'required': True, 'description': 'User identifier of sticker file owner', 'html_description': '<td>User identifier of sticker file owner</td>', 'rst_description': 'User identifier of sticker file owner\n', 'name': 'user_id', 'parsed_type': {'type': 'std', 'name': 'int'}}, {'type': 'InputFile', 'required': True, 'description': 'PNG image with the sticker, must be up to 512 kilobytes in size, dimensions must not exceed 512px, and either width or height must be exactly 512px. More information on Sending Files', 'html_description': '<td><strong>PNG</strong> image with the sticker, must be up to 512 kilobytes in size, dimensions must not exceed 512px, and either width or height must be exactly 512px. <a href="#sending-files">More information on Sending Files &#187;</a></td>', 'rst_description': '**PNG** image with the sticker, must be up to 512 kilobytes in size, dimensions must not exceed 512px, and either width or height must be exactly 512px. :ref:`More information on Sending Files » <sending-files>`\n', 'name': 'png_sticker', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'InputFile'}}}], 'category': 'methods', 'returning': {'type': 'File', 'parsed_type': {'type': 'entity', 'references': {'category': 'types', 'name': 'File'}}, 'description': 'Returns the uploaded File on success.'}, 'bases': ['TelegramMethod']}

        :param user_id: User identifier of sticker file owner
        :param png_sticker: **PNG** image with the sticker, must be up to 512 kilobytes in size, dimensions must not exceed 512px, and either width or height must be exactly 512px. :ref:`More information on Sending Files » <sending-files>`
        :param request_timeout: Request timeout
        :return: Returns the uploaded :class:`aiogram.types.file.File` on success.
        """

        call = UploadStickerFile(
            user_id=user_id,
            png_sticker=png_sticker,
        )
        return await self(call, request_timeout=request_timeout)

    async def close_general_forum_topic(
        self,
        chat_id: Union[int, str],
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to close an open 'General' topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the *can_manage_topics* administrator rights. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'closegeneralforumtopic', 'name': 'closeGeneralForumTopic', 'description': "Use this method to close an open 'General' topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the can_manage_topics administrator rights. Returns True on success.", 'html_description': "<p>Use this method to close an open 'General' topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the <em>can_manage_topics</em> administrator rights. Returns <em>True</em> on success.</p>", 'rst_description': "Use this method to close an open 'General' topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the *can_manage_topics* administrator rights. Returns :code:`True` on success.", 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target supergroup (in the format @supergroupusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target supergroup (in the format <code>@supergroupusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = CloseGeneralForumTopic(
            chat_id=chat_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def edit_general_forum_topic(
        self,
        chat_id: Union[int, str],
        name: str,
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to edit the name of the 'General' topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have *can_manage_topics* administrator rights. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'editgeneralforumtopic', 'name': 'editGeneralForumTopic', 'description': "Use this method to edit the name of the 'General' topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have can_manage_topics administrator rights. Returns True on success.", 'html_description': "<p>Use this method to edit the name of the 'General' topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have <em>can_manage_topics</em> administrator rights. Returns <em>True</em> on success.</p>", 'rst_description': "Use this method to edit the name of the 'General' topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have *can_manage_topics* administrator rights. Returns :code:`True` on success.", 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target supergroup (in the format @supergroupusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target supergroup (in the format <code>@supergroupusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}, {'type': 'String', 'required': True, 'description': 'New topic name, 1-128 characters', 'html_description': '<td>New topic name, 1-128 characters</td>', 'rst_description': 'New topic name, 1-128 characters\n', 'name': 'name', 'parsed_type': {'type': 'std', 'name': 'str'}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)
        :param name: New topic name, 1-128 characters
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = EditGeneralForumTopic(
            chat_id=chat_id,
            name=name,
        )
        return await self(call, request_timeout=request_timeout)

    async def hide_general_forum_topic(
        self,
        chat_id: Union[int, str],
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to hide the 'General' topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the *can_manage_topics* administrator rights. The topic will be automatically closed if it was open. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'hidegeneralforumtopic', 'name': 'hideGeneralForumTopic', 'description': "Use this method to hide the 'General' topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the can_manage_topics administrator rights. The topic will be automatically closed if it was open. Returns True on success.", 'html_description': "<p>Use this method to hide the 'General' topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the <em>can_manage_topics</em> administrator rights. The topic will be automatically closed if it was open. Returns <em>True</em> on success.</p>", 'rst_description': "Use this method to hide the 'General' topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the *can_manage_topics* administrator rights. The topic will be automatically closed if it was open. Returns :code:`True` on success.", 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target supergroup (in the format @supergroupusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target supergroup (in the format <code>@supergroupusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = HideGeneralForumTopic(
            chat_id=chat_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def reopen_general_forum_topic(
        self,
        chat_id: Union[int, str],
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to reopen a closed 'General' topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the *can_manage_topics* administrator rights. The topic will be automatically unhidden if it was hidden. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'reopengeneralforumtopic', 'name': 'reopenGeneralForumTopic', 'description': "Use this method to reopen a closed 'General' topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the can_manage_topics administrator rights. The topic will be automatically unhidden if it was hidden. Returns True on success.", 'html_description': "<p>Use this method to reopen a closed 'General' topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the <em>can_manage_topics</em> administrator rights. The topic will be automatically unhidden if it was hidden. Returns <em>True</em> on success.</p>", 'rst_description': "Use this method to reopen a closed 'General' topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the *can_manage_topics* administrator rights. The topic will be automatically unhidden if it was hidden. Returns :code:`True` on success.", 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target supergroup (in the format @supergroupusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target supergroup (in the format <code>@supergroupusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = ReopenGeneralForumTopic(
            chat_id=chat_id,
        )
        return await self(call, request_timeout=request_timeout)

    async def unhide_general_forum_topic(
        self,
        chat_id: Union[int, str],
        request_timeout: Optional[int] = None,
    ) -> bool:
        """
        Use this method to unhide the 'General' topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the *can_manage_topics* administrator rights. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#{'anchor': 'unhidegeneralforumtopic', 'name': 'unhideGeneralForumTopic', 'description': "Use this method to unhide the 'General' topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the can_manage_topics administrator rights. Returns True on success.", 'html_description': "<p>Use this method to unhide the 'General' topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the <em>can_manage_topics</em> administrator rights. Returns <em>True</em> on success.</p>", 'rst_description': "Use this method to unhide the 'General' topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the *can_manage_topics* administrator rights. Returns :code:`True` on success.", 'annotations': [{'type': 'Integer or String', 'required': True, 'description': 'Unique identifier for the target chat or username of the target supergroup (in the format @supergroupusername)', 'html_description': '<td>Unique identifier for the target chat or username of the target supergroup (in the format <code>@supergroupusername</code>)</td>', 'rst_description': 'Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)\n', 'name': 'chat_id', 'parsed_type': {'type': 'union', 'items': [{'type': 'std', 'name': 'int'}, {'type': 'std', 'name': 'str'}]}}], 'category': 'methods', 'returning': {'type': 'True', 'parsed_type': {'type': 'std', 'name': 'bool', 'value': True}, 'description': 'Returns True on success.'}, 'bases': ['TelegramMethod']}

        :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)
        :param request_timeout: Request timeout
        :return: Returns :code:`True` on success.
        """

        call = UnhideGeneralForumTopic(
            chat_id=chat_id,
        )
        return await self(call, request_timeout=request_timeout)
