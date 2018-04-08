"""
TelegramAPIError
    ValidationError
    Throttled
    BadRequest
        MessageError
            MessageNotModified
            MessageToForwardNotFound
            MessageToDeleteNotFound
            MessageIdentifierNotSpecified
        ChatNotFound
        InvalidQueryID
        InvalidPeerID
        InvalidHTTPUrlContent
        WrongFileIdentifier
        GroupDeactivated
        BadWebhook
            WebhookRequireHTTPS
            BadWebhookPort
        CantParseUrl
        NotFound
            MethodNotKnown
    ConflictError
        TerminatedByOtherGetUpdates
        CantGetUpdates
    Unauthorized
        BotKicked
        BotBlocked
        UserDeactivated
    NetworkError
    RetryAfter
    MigrateToChat

AIOGramWarning
    TimeoutWarning
"""
import time

_PREFIXES = ['Error: ', '[Error]: ', 'Bad Request: ', 'Conflict: ', 'Not Found: ']


def _clean_message(text):
    for prefix in _PREFIXES:
        if text.startswith(prefix):
            text = text[len(prefix):]
    return (text[0].upper() + text[1:]).strip()


class TelegramAPIError(Exception):
    def __init__(self, message=None):
        super(TelegramAPIError, self).__init__(_clean_message(message))


class _MatchErrorMixin:
    match = ''
    text = None

    @classmethod
    def check(cls, message):
        return cls.match in message

    @classmethod
    def throw(cls):
        raise cls(cls.text or cls.match)


class AIOGramWarning(Warning):
    pass


class TimeoutWarning(AIOGramWarning):
    pass


class FSMStorageWarning(AIOGramWarning):
    pass


class ValidationError(TelegramAPIError):
    pass


class BadRequest(TelegramAPIError):
    pass


class MessageError(BadRequest):
    pass


class MessageNotModified(MessageError, _MatchErrorMixin):
    match = 'message is not modified'


class MessageToForwardNotFound(MessageError, _MatchErrorMixin):
    match = 'message to forward not found'


class MessageToDeleteNotFound(MessageError, _MatchErrorMixin):
    match = 'message to delete not found'


class MessageIdentifierNotSpecified(MessageError, _MatchErrorMixin):
    match = 'message identifier is not specified'


class ChatNotFound(BadRequest, _MatchErrorMixin):
    match = 'chat not found'


class InvalidQueryID(BadRequest, _MatchErrorMixin):
    match = 'QUERY_ID_INVALID'
    text = 'Invalid query ID'


class InvalidPeerID(BadRequest, _MatchErrorMixin):
    match = 'PEER_ID_INVALID'
    text = 'Invalid peer ID'


class InvalidHTTPUrlContent(BadRequest, _MatchErrorMixin):
    match = 'Failed to get HTTP URL content'


class WrongFileIdentifier(BadRequest, _MatchErrorMixin):
    match = 'wrong file identifier/HTTP URL specified'


class GroupDeactivated(BadRequest, _MatchErrorMixin):
    match = 'group is deactivated'


class PhotoAsInputFileRequired(BadRequest, _MatchErrorMixin):
    match = 'Photo should be uploaded as an InputFile'


class BadWebhook(BadRequest):
    pass


class WebhookRequireHTTPS(BadRequest, _MatchErrorMixin):
    match = 'HTTPS url must be provided for webhook'
    text = 'bad webhook: ' + match


class BadWebhookPort(BadRequest, _MatchErrorMixin):
    match = 'Webhook can be set up only on ports 80, 88, 443 or 8443'
    text = 'bad webhook: ' + match


class CantParseUrl(BadRequest, _MatchErrorMixin):
    match = 'can\'t parse URL'


class NotFound(TelegramAPIError):
    pass


class MethodNotKnown(NotFound, _MatchErrorMixin):
    match = 'method not found'


class ConflictError(TelegramAPIError):
    pass


class TerminatedByOtherGetUpdates(ConflictError, _MatchErrorMixin):
    match = 'terminated by other getUpdates request'
    text = 'Terminated by other getUpdates request; ' \
           'Make sure that only one bot instance is running'


class CantGetUpdates(ConflictError, _MatchErrorMixin):
    match = 'can\'t use getUpdates method while webhook is active'


class Unauthorized(TelegramAPIError):
    pass


class BotKicked(Unauthorized, _MatchErrorMixin):
    match = 'Bot was kicked from a chat'


class BotBlocked(Unauthorized, _MatchErrorMixin):
    match = 'bot was blocked by the user'


class UserDeactivated(Unauthorized, _MatchErrorMixin):
    match = 'user is deactivated'


class NetworkError(TelegramAPIError):
    pass


class RetryAfter(TelegramAPIError):
    def __init__(self, retry_after):
        super(RetryAfter, self).__init__(f"Flood control exceeded. Retry in {retry_after} seconds.")
        self.timeout = retry_after


class MigrateToChat(TelegramAPIError):
    def __init__(self, chat_id):
        super(MigrateToChat, self).__init__(f"The group has been migrated to a supergroup. New id: {chat_id}.")
        self.migrate_to_chat_id = chat_id


class Throttled(TelegramAPIError):
    def __init__(self, **kwargs):
        from ..dispatcher.storage import DELTA, EXCEEDED_COUNT, KEY, LAST_CALL, RATE_LIMIT, RESULT
        self.key = kwargs.pop(KEY, '<None>')
        self.called_at = kwargs.pop(LAST_CALL, time.time())
        self.rate = kwargs.pop(RATE_LIMIT, None)
        self.result = kwargs.pop(RESULT, False)
        self.exceeded_count = kwargs.pop(EXCEEDED_COUNT, 0)
        self.delta = kwargs.pop(DELTA, 0)
        self.user = kwargs.pop('user', None)
        self.chat = kwargs.pop('chat', None)

    def __str__(self):
        return f"Rate limit exceeded! (Limit: {self.rate} s, " \
               f"exceeded: {self.exceeded_count}, " \
               f"time delta: {round(self.delta, 3)} s)"
