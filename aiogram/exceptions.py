def _clean_message(text):
    return text. \
        lstrip('Error: '). \
        lstrip('[Error]: '). \
        lstrip('Bad Request: ')


class TelegramAPIError(Exception):
    def __init__(self, message):
        super(TelegramAPIError, self).__init__(_clean_message(message))


class ValidationError(TelegramAPIError):
    pass


class BadRequest(TelegramAPIError):
    pass


class Unauthorized(TelegramAPIError):
    pass


class NetworkError(TelegramAPIError):
    pass


class RetryAfter(TelegramAPIError):
    def __init__(self, retry_after):
        super(RetryAfter, self).__init__(f"Flood control exceeded. Retry in {retry_after} seconds")
        self.timeout = retry_after


class MigrateToChat(TelegramAPIError):
    def __init__(self, chat_id):
        super(MigrateToChat, self).__init__(f"The group has been migrated to a supergroup. New id: {chat_id}")
        self.migrate_to_chat_id = chat_id
