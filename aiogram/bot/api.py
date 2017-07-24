import logging
import os

import aiohttp

from ..exceptions import ValidationError, TelegramAPIError
from ..utils import json
from ..utils.helper import Helper, HelperMode, Item

# Main aiogram logger
log = logging.getLogger('aiogram')

# API Url's
API_URL = "https://api.telegram.org/bot{token}/{method}"
FILE_URL = "https://api.telegram.org/file/bot{token}/{path}"


def check_token(token: str) -> bool:
    """
    Validate BOT token

    :param token:
    :return:
    """
    if any(x.isspace() for x in token):
        raise ValidationError('Token is invalid!')

    left, sep, right = token.partition(':')
    if (not sep) or (not left.isdigit()) or (len(left) < 3):
        raise ValidationError('Token is invalid!')

    return True


async def _check_result(method_name, response):
    """
    Checks whether `result` is a valid API response.
    A result is considered invalid if:
        - The server returned an HTTP response code other than 200
        - The content of the result is invalid JSON.
        - The method call was unsuccessful (The JSON 'ok' field equals False)

    :raises ApiException: if one of the above listed cases is applicable
    :param method_name: The name of the method called
    :param response: The returned response of the method request
    :return: The result parsed to a JSON dictionary.
    """
    if response.status != 200:
        body = await response.text()
        raise TelegramAPIError(f"The server returned HTTP {response.status}. Response body:\n[{body}]",
                               method_name, response.status, body)

    result_json = await response.json(loads=json.loads)

    if not result_json.get('ok'):
        body = await response.text()
        code = result_json.get('error_code')
        description = result_json.get('description')
        raise TelegramAPIError(f"Error code: {code} Description {description}",
                               method_name, response.status, body)
    log.debug(f"Response for '{method_name}': {result_json}")
    return result_json.get('result')


def _guess_filename(obj):
    """
    Get file name from object

    :param obj:
    :return:
    """
    name = getattr(obj, 'name', None)
    if name and isinstance(name, str) and name[0] != '<' and name[-1] != '>':
        return os.path.basename(name)


def _compose_data(params=None, files=None):
    """
    Prepare request data

    :param params:
    :param files:
    :return:
    """
    data = aiohttp.formdata.FormData()

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
            else:
                filename, fileobj = _guess_filename(f) or key, f

            data.add_field(key, fileobj, filename=filename)

    return data


async def request(session, token, method, data=None, files=None) -> bool or dict:
    """
    Make request to API

    That make request with Content-Type:
        application/x-www-form-urlencoded - For simple request
        and multipart/form-data - for files uploading

    https://core.telegram.org/bots/api#making-requests

    :param session: :class:`aiohttp.ClientSession`
    :param token: BOT token
    :param method: API method
    :param data: request payload
    :param files: files
    :return: bool or dict
    """
    log.debug(f"Make request: '{method}' with data: {data or {}} and files {files or {}}")
    data = _compose_data(data, files)
    url = Methods.api_url(token=token, method=method)
    async with session.post(url, data=data) as response:
        return await _check_result(method, response)


class Methods(Helper):
    """
    Helper for Telegram API Methods listed on https://core.telegram.org/bots/api

    List is updated to Bot API 3.2
    """
    mode = HelperMode.camelCase

    # Getting Updates
    GET_UPDATES = Item()  # getUpdates
    SET_WEBHOOK = Item()  # setWebhook
    DELETE_WEBHOOK = Item()  # deleteWebhook
    GET_WEBHOOK_INFO = Item()  # getWebhookInfo

    # Available methods
    GET_ME = Item()  # getMe
    SEND_MESSAGE = Item()  # sendMessage
    FORWARD_MESSAGE = Item()  # forwardMessage
    SEND_PHOTO = Item()  # sendPhoto
    SEND_AUDIO = Item()  # sendAudio
    SEND_DOCUMENT = Item()  # sendDocument
    SEND_VIDEO = Item()  # sendVideo
    SEND_VOICE = Item()  # sendVoice
    SEND_VIDEO_NOTE = Item()  # sendVideoNote
    SEND_LOCATION = Item()  # sendLocation
    SEND_VENUE = Item()  # sendVenue
    SEND_CONTACT = Item()  # sendContact
    SEND_CHAT_ACTION = Item()  # sendChatAction
    GET_USER_PROFILE_PHOTOS = Item()  # getUserProfilePhotos
    GET_FILE = Item()  # getFile
    KICK_CHAT_MEMBER = Item()  # kickChatMember
    UNBAN_CHAT_MEMBER = Item()  # unbanChatMember
    RESTRICT_CHAT_MEMBER = Item()  # restrictChatMember
    PROMOTE_CHAT_MEMBER = Item()  # promoteChatMember
    EXPORT_CHAT_INVITE_LINK = Item()  # exportChatInviteLink
    SET_CHAT_PHOTO = Item()  # setChatPhoto
    DELETE_CHAT_PHOTO = Item()  # deleteChatPhoto
    SET_CHAT_TITLE = Item()  # setChatTitle
    SET_CHAT_DESCRIPTION = Item()  # setChatDescription
    PIN_CHAT_MESSAGE = Item()  # pinChatMessage
    UNPIN_CHAT_MESSAGE = Item()  # unpinChatMessage
    LEAVE_CHAT = Item()  # leaveChat
    GET_CHAT = Item()  # getChat
    GET_CHAT_ADMINISTRATORS = Item()  # getChatAdministrators
    GET_CHAT_MEMBERS_COUNT = Item()  # getChatMembersCount
    GET_CHAT_MEMBER = Item()  # getChatMember
    ANSWER_CALLBACK_QUERY = Item()  # answerCallbackQuery

    # Updating messages
    EDIT_MESSAGE_TEXT = Item()  # editMessageText
    EDIT_MESSAGE_CAPTION = Item()  # editMessageCaption
    EDIT_MESSAGE_REPLY_MARKUP = Item()  # editMessageReplyMarkup
    DELETE_MESSAGE = Item()  # deleteMessage

    # Stickers
    SEND_STICKER = Item()  # sendSticker
    GET_STICKER_SET = Item()  # getStickerSet
    UPLOAD_STICKER_FILE = Item()  # uploadStickerFile
    CREATE_NEW_STICKER_SET = Item()  # createNewStickerSet
    ADD_STICKER_TO_SET = Item()  # addStickerToSet
    SET_STICKER_POSITION_IN_SET = Item()  # setStickerPositionInSet
    DELETE_STICKER_FROM_SET = Item()  # deleteStickerFromSet

    # Inline mode
    ANSWER_INLINE_QUERY = Item()  # answerInlineQuery

    # Payments
    SEND_INVOICE = Item()  # sendInvoice
    ANSWER_SHIPPING_QUERY = Item()  # answerShippingQuery
    ANSWER_PRE_CHECKOUT_QUERY = Item()  # answerPreCheckoutQuery

    # Games
    SEND_GAME = Item()  # sendGame
    SET_GAME_SCORE = Item()  # setGameScore
    GET_GAME_HIGH_SCORES = Item()  # getGameHighScores

    @staticmethod
    def api_url(token, method):
        """
        Generate API URL with included token and method name

        :param token:
        :param method:
        :return:
        """
        return API_URL.format(token=token, method=method)

    @staticmethod
    def file_url(token, path):
        """
        Generate File URL with included token and file path

        :param token:
        :param path:
        :return:
        """
        return FILE_URL.format(token=token, path=path)
