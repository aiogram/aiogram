import logging
import os
from dataclasses import dataclass
from http import HTTPStatus

import aiohttp

from .. import types
from ..utils import exceptions, json
from ..utils.helper import Helper, HelperMode, Item

# Main aiogram logger
log = logging.getLogger('aiogram')


@dataclass(frozen=True)
class TelegramAPIServer:
    """
    Base config for API Endpoints
    """

    base: str
    file: str

    def api_url(self, token: str, method: str) -> str:
        """
        Generate URL for API methods

        :param token: Bot token
        :param method: API method name (case insensitive)
        :return: URL
        """
        return self.base.format(token=token, method=method)

    def file_url(self, token: str, path: str) -> str:
        """
        Generate URL for downloading files

        :param token: Bot token
        :param path: file path
        :return: URL
        """
        return self.file.format(token=token, path=path)

    @classmethod
    def from_base(cls, base: str) -> 'TelegramAPIServer':
        base = base.rstrip("/")
        return cls(
            base=f"{base}/bot{{token}}/{{method}}",
            file=f"{base}/file/bot{{token}}/{{path}}",
        )


TELEGRAM_PRODUCTION = TelegramAPIServer.from_base("https://api.telegram.org")


def check_token(token: str) -> bool:
    """
    Validate BOT token

    :param token:
    :return:
    """
    if not isinstance(token, str):
        message = (f"Token is invalid! "
                   f"It must be 'str' type instead of {type(token)} type.")
        raise exceptions.ValidationError(message)

    if any(x.isspace() for x in token):
        message = "Token is invalid! It can't contains spaces."
        raise exceptions.ValidationError(message)

    left, sep, right = token.partition(':')
    if (not sep) or (not left.isdigit()) or (not right):
        raise exceptions.ValidationError('Token is invalid!')

    return True


def check_result(method_name: str, content_type: str, status_code: int, body: str):
    """
    Checks whether `result` is a valid API response.
    A result is considered invalid if:
    - The server returned an HTTP response code other than 200
    - The content of the result is invalid JSON.
    - The method call was unsuccessful (The JSON 'ok' field equals False)

    :param method_name: The name of the method called
    :param status_code: status code
    :param content_type: content type of result
    :param body: result body
    :return: The result parsed to a JSON dictionary
    :raises ApiException: if one of the above listed cases is applicable
    """
    log.debug('Response for %s: [%d] "%r"', method_name, status_code, body)

    if content_type != 'application/json':
        raise exceptions.NetworkError(f"Invalid response with content type {content_type}: \"{body}\"")

    try:
        result_json = json.loads(body)
    except ValueError:
        result_json = {}

    description = result_json.get('description') or body
    parameters = types.ResponseParameters(**result_json.get('parameters', {}) or {})

    if HTTPStatus.OK <= status_code <= HTTPStatus.IM_USED:
        return result_json.get('result')
    elif parameters.retry_after:
        raise exceptions.RetryAfter(parameters.retry_after)
    elif parameters.migrate_to_chat_id:
        raise exceptions.MigrateToChat(parameters.migrate_to_chat_id)
    elif status_code == HTTPStatus.BAD_REQUEST:
        exceptions.BadRequest.detect(description)
    elif status_code == HTTPStatus.NOT_FOUND:
        exceptions.NotFound.detect(description)
    elif status_code == HTTPStatus.CONFLICT:
        exceptions.ConflictError.detect(description)
    elif status_code in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
        exceptions.Unauthorized.detect(description)
    elif status_code == HTTPStatus.REQUEST_ENTITY_TOO_LARGE:
        raise exceptions.NetworkError('File too large for uploading. '
                                      'Check telegram api limits https://core.telegram.org/bots/api#senddocument')
    elif status_code >= HTTPStatus.INTERNAL_SERVER_ERROR:
        if 'restart' in description:
            raise exceptions.RestartingTelegram()
        raise exceptions.TelegramAPIError(description)
    raise exceptions.TelegramAPIError(f"{description} [{status_code}]")


async def make_request(session, server, token, method, data=None, files=None, **kwargs):
    log.debug('Make request: "%s" with data: "%r" and files "%r"', method, data, files)

    url = server.api_url(token=token, method=method)

    req = compose_data(data, files)
    try:
        async with session.post(url, data=req, **kwargs) as response:
            return check_result(method, response.content_type, response.status, await response.text())
    except aiohttp.ClientError as e:
        raise exceptions.NetworkError(f"aiohttp client throws an error: {e.__class__.__name__}: {e}")


def guess_filename(obj):
    """
    Get file name from object

    :param obj:
    :return:
    """
    name = getattr(obj, 'name', None)
    if name and isinstance(name, str) and name[0] != '<' and name[-1] != '>':
        return os.path.basename(name)


def compose_data(params=None, files=None):
    """
    Prepare request data

    :param params:
    :param files:
    :return:
    """
    data = aiohttp.formdata.FormData(quote_fields=False)

    if params:
        for key, value in params.items():
            data.add_field(key, str(value))

    if files:
        for key, f in files.items():
            if isinstance(f, tuple):
                if len(f) == 2:
                    filename, fileobj = f
                else:
                    raise ValueError('Tuple must have exactly 2 elements: filename, fileobj')
            elif isinstance(f, types.InputFile):
                filename, fileobj = f.filename, f.file
            else:
                filename, fileobj = guess_filename(f) or key, f

            data.add_field(key, fileobj, filename=filename)

    return data


class Methods(Helper):
    """
    Helper for Telegram API Methods listed on https://core.telegram.org/bots/api
    """
    mode = HelperMode.lowerCamelCase

    # Getting Updates
    GET_UPDATES = Item()  # getUpdates
    SET_WEBHOOK = Item()  # setWebhook
    DELETE_WEBHOOK = Item()  # deleteWebhook
    GET_WEBHOOK_INFO = Item()  # getWebhookInfo

    # Available methods
    GET_ME = Item()  # getMe
    LOG_OUT = Item()  # logOut
    CLOSE = Item()  # close
    SEND_MESSAGE = Item()  # sendMessage
    FORWARD_MESSAGE = Item()  # forwardMessage
    COPY_MESSAGE = Item()  # copyMessage
    SEND_PHOTO = Item()  # sendPhoto
    SEND_AUDIO = Item()  # sendAudio
    SEND_DOCUMENT = Item()  # sendDocument
    SEND_VIDEO = Item()  # sendVideo
    SEND_ANIMATION = Item()  # sendAnimation
    SEND_VOICE = Item()  # sendVoice
    SEND_VIDEO_NOTE = Item()  # sendVideoNote
    SEND_MEDIA_GROUP = Item()  # sendMediaGroup
    SEND_LOCATION = Item()  # sendLocation
    EDIT_MESSAGE_LIVE_LOCATION = Item()  # editMessageLiveLocation
    STOP_MESSAGE_LIVE_LOCATION = Item()  # stopMessageLiveLocation
    SEND_VENUE = Item()  # sendVenue
    SEND_CONTACT = Item()  # sendContact
    SEND_POLL = Item()  # sendPoll
    SEND_DICE = Item()  # sendDice
    SEND_CHAT_ACTION = Item()  # sendChatAction
    GET_USER_PROFILE_PHOTOS = Item()  # getUserProfilePhotos
    GET_FILE = Item()  # getFile
    KICK_CHAT_MEMBER = Item()  # kickChatMember
    BAN_CHAT_MEMBER = Item()  # banChatMember
    UNBAN_CHAT_MEMBER = Item()  # unbanChatMember
    RESTRICT_CHAT_MEMBER = Item()  # restrictChatMember
    PROMOTE_CHAT_MEMBER = Item()  # promoteChatMember
    SET_CHAT_ADMINISTRATOR_CUSTOM_TITLE = Item()  # setChatAdministratorCustomTitle
    BAN_CHAT_SENDER_CHAT = Item()  # banChatSenderChat
    UNBAN_CHAT_SENDER_CHAT = Item()  # unbanChatSenderChat
    SET_CHAT_PERMISSIONS = Item()  # setChatPermissions
    EXPORT_CHAT_INVITE_LINK = Item()  # exportChatInviteLink
    CREATE_CHAT_INVITE_LINK = Item()  # createChatInviteLink
    EDIT_CHAT_INVITE_LINK = Item()  # editChatInviteLink
    REVOKE_CHAT_INVITE_LINK = Item()  # revokeChatInviteLink
    APPROVE_CHAT_JOIN_REQUEST = Item()  # approveChatJoinRequest
    DECLINE_CHAT_JOIN_REQUEST = Item()  # declineChatJoinRequest
    SET_CHAT_PHOTO = Item()  # setChatPhoto
    DELETE_CHAT_PHOTO = Item()  # deleteChatPhoto
    SET_CHAT_TITLE = Item()  # setChatTitle
    SET_CHAT_DESCRIPTION = Item()  # setChatDescription
    PIN_CHAT_MESSAGE = Item()  # pinChatMessage
    UNPIN_CHAT_MESSAGE = Item()  # unpinChatMessage
    UNPIN_ALL_CHAT_MESSAGES = Item()  # unpinAllChatMessages
    LEAVE_CHAT = Item()  # leaveChat
    GET_CHAT = Item()  # getChat
    GET_CHAT_ADMINISTRATORS = Item()  # getChatAdministrators
    GET_CHAT_MEMBER_COUNT = Item()  # getChatMemberCount
    GET_CHAT_MEMBERS_COUNT = Item()  # getChatMembersCount (renamed to getChatMemberCount)
    GET_CHAT_MEMBER = Item()  # getChatMember
    SET_CHAT_STICKER_SET = Item()  # setChatStickerSet
    DELETE_CHAT_STICKER_SET = Item()  # deleteChatStickerSet
    ANSWER_CALLBACK_QUERY = Item()  # answerCallbackQuery
    SET_MY_COMMANDS = Item()  # setMyCommands
    DELETE_MY_COMMANDS = Item()  # deleteMyCommands
    GET_MY_COMMANDS = Item()  # getMyCommands

    # Updating messages
    EDIT_MESSAGE_TEXT = Item()  # editMessageText
    EDIT_MESSAGE_CAPTION = Item()  # editMessageCaption
    EDIT_MESSAGE_MEDIA = Item()  # editMessageMedia
    EDIT_MESSAGE_REPLY_MARKUP = Item()  # editMessageReplyMarkup
    STOP_POLL = Item()  # stopPoll
    DELETE_MESSAGE = Item()  # deleteMessage

    # Stickers
    SEND_STICKER = Item()  # sendSticker
    GET_STICKER_SET = Item()  # getStickerSet
    UPLOAD_STICKER_FILE = Item()  # uploadStickerFile
    CREATE_NEW_STICKER_SET = Item()  # createNewStickerSet
    ADD_STICKER_TO_SET = Item()  # addStickerToSet
    SET_STICKER_POSITION_IN_SET = Item()  # setStickerPositionInSet
    DELETE_STICKER_FROM_SET = Item()  # deleteStickerFromSet
    SET_STICKER_SET_THUMB = Item()  # setStickerSetThumb

    # Inline mode
    ANSWER_INLINE_QUERY = Item()  # answerInlineQuery

    ANSWER_WEB_APP_QUERY = Item()  # answerWebAppQuery
    SET_CHAT_MENU_BUTTON = Item()  # setChatMenuButton
    GET_CHAT_MENU_BUTTON = Item()  # getChatMenuButton

    SET_MY_DEFAULT_ADMINISTRATOR_RIGHTS = Item()  # setMyDefaultAdministratorRights
    GET_MY_DEFAULT_ADMINISTRATOR_RIGHTS = Item()  # getMyDefaultAdministratorRights

    # Payments
    SEND_INVOICE = Item()  # sendInvoice
    ANSWER_SHIPPING_QUERY = Item()  # answerShippingQuery
    ANSWER_PRE_CHECKOUT_QUERY = Item()  # answerPreCheckoutQuery

    # Telegram Passport
    SET_PASSPORT_DATA_ERRORS = Item()  # setPassportDataErrors

    # Games
    SEND_GAME = Item()  # sendGame
    SET_GAME_SCORE = Item()  # setGameScore
    GET_GAME_HIGH_SCORES = Item()  # getGameHighScores
