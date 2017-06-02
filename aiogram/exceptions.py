class ValidationError(Exception):
    pass


class TelegramAPIError(Exception):
    def __init__(self, message, method, status, body):
        super(TelegramAPIError, self).__init__(
            f"A request to the Telegram API was unsuccessful.\n{message}")
        self.method = method
        self.status = status
        self.body = body
