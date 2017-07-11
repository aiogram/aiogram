import logging
import os

import aiohttp

from ..exceptions import ValidationError, TelegramAPIError
from ..utils import json

log = logging.getLogger('aiogram')

API_URL = "https://api.telegram.org/bot{token}/{method}"
FILE_URL = "https://api.telegram.org/file/bot{token}/{path}"


def check_token(token):
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
    name = getattr(obj, 'name', None)
    if name and isinstance(name, str) and name[0] != '<' and name[-1] != '>':
        return os.path.basename(name)


def _compose_data(params, files=None):
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


async def request(session, token, method, data=None, files=None):
    log.debug(f"Make request: '{method}' with data: {data or {}} and files {files or {}}")
    data = _compose_data(data, files)
    url = Methods.api_url(token=token, method=method)
    async with session.post(url, data=data) as response:
        return await _check_result(method, response)


class Methods:
    GET_ME = 'getMe'
    GET_UPDATES = 'getUpdates'
    SET_WEBHOOK = 'setWebhook'
    DELETE_WEBHOOK = 'deleteWebhook'
    GET_WEBHOOK_INFO = 'getWebhookInfo'
    SEND_MESSAGE = 'sendMessage'
    FORWARD_MESSAGE = 'forwardMessage'
    SEND_PHOTO = 'sendPhoto'
    SEND_AUDIO = 'sendAudio'
    SEND_DOCUMENT = 'sendDocument'
    SEND_STICKER = 'sendSticker'
    SEND_VIDEO = 'sendVideo'
    SEND_VOICE = 'sendVoice'
    SEND_VIDEO_NOTE = 'sendVideoNote'
    SEND_LOCATION = 'sendLocation'
    SEND_VENUE = 'sendVenue'
    SEND_CONTACT = 'sendContact'
    SEND_CHAT_ACTION = 'sendChatAction'
    GET_USER_PROFILE_PHOTOS = 'getUserProfilePhotos'
    GET_FILE = 'getFile'
    KICK_CHAT_MEMBER = 'kickChatMember'
    UNBAN_CHAT_MEMBER = 'unbanChatMember'
    LEAVE_CHAT = 'leaveChat'
    GET_CHAT = 'getChat'
    GET_CHAT_ADMINISTRATORS = 'getChatAdministrators'
    GET_CHAT_MEMBERS_COUNT = 'getChatMembersCount'
    GET_CHAT_MEMBER = 'getChatMember'
    RESTRICT_CHAT_MEMBER = 'restrictChatMember'
    PROMOTE_CHAT_MEMBER = 'promoteChatMember'
    EXPORT_CHAT_INVITE_LINK = 'exportChatInviteLink'
    SET_CHAT_PHOTO = 'setChatPhoto'
    DELETE_CHAT_PHOTO = 'deleteChatPhoto'
    SET_CHAT_TITLE = 'setChatTitle'
    SET_CHAT_DESCRIPTION = 'setChatDescription'
    PIN_CHAT_MESSAGE = 'pinChatMessage'
    UNPIN_CHAT_MESSAGE = 'unpinChatMessage'
    ANSWER_CALLBACK_QUERY = 'answerCallbackQuery'
    ANSWER_INLINE_QUERY = 'answerInlineQuery'
    EDIT_MESSAGE_TEXT = 'editMessageText'
    EDIT_MESSAGE_CAPTION = 'editMessageCaption'
    EDIT_MESSAGE_REPLY_MARKUP = 'editMessageReplyMarkup'
    DELETE_MESSAGE = 'deleteMessage'
    SEND_INVOICE = 'sendInvoice'
    ANSWER_SHIPPING_QUERY = 'answerShippingQuery'
    ANSWER_PRE_CHECKOUT_QUERY = 'answerPreCheckoutQuery'
    SEND_GAME = 'sendGame'
    SET_GAME_SCORE = 'setGameScore'
    GET_GAME_HIGH_SCORES = 'getGameHighScores'

    @staticmethod
    def api_url(token, method):
        return API_URL.format(token=token, method=method)

    @staticmethod
    def file_url(token, path):
        return FILE_URL.format(token=token, path=path)
