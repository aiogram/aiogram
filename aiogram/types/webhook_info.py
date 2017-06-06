import datetime

from .base import Deserializable


class WebhookInfo(Deserializable):
    """
    Contains information about the current status of a webhook.
    
    https://core.telegram.org/bots/api#webhookinfo
    """
    def __init__(self, url, has_custom_certificate, pending_update_count, last_error_date, last_error_message,
                 max_connections, allowed_updates):
        self.url: str = url
        self.has_custom_certificate: bool = has_custom_certificate
        self.pending_update_count: int = pending_update_count
        self.last_error_date: int = last_error_date
        self.last_error_message: str = last_error_message
        self.max_connections: int = max_connections
        self.allowed_updates: [str] = allowed_updates

    @classmethod
    def _parse_date(cls, unix_time):
        return datetime.datetime.fromtimestamp(unix_time)

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        url = raw_data.get('url')
        has_custom_certificate = raw_data.get('has_custom_certificate')
        pending_update_count = raw_data.get('pending_update_count')
        last_error_date = cls._parse_date(raw_data.get('last_error_date'))
        last_error_message = raw_data.get('last_error_message')
        max_connections = raw_data.get('max_connections')
        allowed_updates = raw_data.get('allowed_updates')

        return WebhookInfo(url, has_custom_certificate, pending_update_count, last_error_date, last_error_message,
                           max_connections, allowed_updates)
