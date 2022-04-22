import typing

from . import base
from . import fields


class WebhookInfo(base.TelegramObject):
    """
    Contains information about the current status of a webhook.

    https://core.telegram.org/bots/api#webhookinfo
    """
    url: base.String = fields.Field()
    has_custom_certificate: base.Boolean = fields.Field()
    pending_update_count: base.Integer = fields.Field()
    ip_address: base.String = fields.Field()
    last_error_date: base.Integer = fields.Field()
    last_error_message: base.String = fields.Field()
    max_connections: base.Integer = fields.Field()
    allowed_updates: typing.List[base.String] = fields.ListField()
    last_synchronization_error_date: base.Integer = fields.DateTimeField()
