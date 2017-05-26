from . import API_URL, log
from .exceptions import ValidationError, TelegramAPIError


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

    result_json = await response.json()

    if not result_json.get('ok'):
        body = await response.text()
        code = result_json.get('error_code')
        description = result_json.get('description')
        raise TelegramAPIError(f"Error code: {code} Description {description}",
                               method_name, response.status, body)
    log.debug(f"Response for '{method_name}': {result_json}")
    return result_json.get('result')


async def request(session, token, method, data=None):
    log.debug(f"Make request: '{method}' with data: {data or {}}")
    url = API_URL.format(token=token, method=method)
    async with session.post(url, json=data) as response:
        return await _check_result(method, response)


class ApiMethods:
    GET_ME = 'getMe'
    GET_UPDATES = 'getUpdates'
    SET_WEBHOOK = 'setWebhook'  # TODO
    DELETE_WEBHOOK = 'deleteWebhook'  # TODO
    GET_WEBHOOK_INFO = 'getWebhookInfo'  # TODO
    SEND_MESSAGE = 'sendMessage'
    FORWARD_MESSAGE = 'forwardMessage'
    SEND_PHOTO = 'sendPhoto'  # TODO
    SEND_AUDIO = 'sendAudio'  # TODO
    SEND_DOCUMENT = 'sendDocument'  # TODO
    SEND_STICKER = 'sendSticker'  # TODO
    SEND_VIDEO = 'sendVideo'  # TODO
    SEND_VOICE = 'sendVoice'  # TODO
    SEND_VIDEO_NOTE = 'sendVideoNote'  # TODO
    SEND_LOCATION = 'sendLocation'  # TODO
    SEND_VENUE = 'sendVenue'  # TODO
    SEND_CONTACT = 'sendContact'  # TODO
    SEND_CHAT_ACTION = 'sendChatAction'  # TODO
    GET_USER_PROFILE_PHOTOS = 'getUserProfilePhotos'  # TODO
    GET_FILE = 'getFile'  # TODO
    KICK_CHAT_MEMBER = 'kickChatMember'  # TODO
    UNBAN_CHAT_MEMBER = 'unbanChatMember'  # TODO
    LEAVE_CHAT = 'leaveChat'  # TODO
    GET_CHAT = 'getChat'
    GET_CHAT_ADMINISTRATORS = 'getChatAdministrators'  # TODO
    GET_CHAT_MEMBERS_COUNT = 'getChatMembersCount'  # TODO
    GET_CHAT_MEMBER = 'getChatMember'  # TODO
    ANSWER_CALLBACK_QUERY = 'answerCallbackQuery'  # TODO
    EDIT_MESSAGE_TEXT = 'editMessageText'  # TODO
    EDIT_MESSAGE_CAPTION = 'editMessageCaption'  # TODO
    EDIT_MESSAGE_REPLY_MARKUP = 'editMessageReplyMarkup'  # TODO
    DELETE_MESSAGE = 'deleteMessage'
