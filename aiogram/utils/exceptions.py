import time

_PREFIXES = ['Error: ', '[Error]: ', 'Bad Request: ', 'Conflict: ']


def _clean_message(text):
    for prefix in _PREFIXES:
        if text.startswith(prefix):
            text = text[len(prefix):]
    return (text[0].upper() + text[1:]).strip()


class TelegramAPIError(Exception):
    def __init__(self, message):
        super(TelegramAPIError, self).__init__(_clean_message(message))


class AIOGramWarning(Warning):
    pass


class TimeoutWarning(AIOGramWarning):
    pass


class ValidationError(TelegramAPIError):
    pass


class BadRequest(TelegramAPIError):
    pass


class ConflictError(TelegramAPIError):
    pass


class Unauthorized(TelegramAPIError):
    pass


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


class Throttled(Exception):
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
