from . import types
from .utils import json


class ValidationError(Exception):
    pass


class TelegramAPIError(Exception):
    def __init__(self, message, method, status, body):
        super(TelegramAPIError, self).__init__(
            f"A request to the Telegram API was unsuccessful.\n{message}")
        self.method = method
        self.status = status
        self.body = body

    def json(self):
        if not self.body:
            return None
        try:
            data = json.dumps(self.body)
        except Exception:
            data = None
        return data

    @property
    def parameters(self):
        data = self.json()
        if data and 'parameters' in data:
            return types.ResponseParameters.deserialize(data['parameters'])
