import typing

from . import base
from . import fields
from .message_entity import MessageEntity


class InputMessageContent(base.TelegramObject):
    """
    This object represents the content of a message to be sent as a result of an inline query.

    Telegram clients currently support the following 4 types

    https://core.telegram.org/bots/api#inputmessagecontent
    """
    pass


class InputContactMessageContent(InputMessageContent):
    """
    Represents the content of a contact message to be sent as the result of an inline query.

    Note: This will only work in Telegram versions released after 9 April, 2016.
    Older clients will ignore them.

    https://core.telegram.org/bots/api#inputcontactmessagecontent
    """
    phone_number: base.String = fields.Field()
    first_name: base.String = fields.Field()
    last_name: base.String = fields.Field()
    vcard: base.String = fields.Field()

    def __init__(self, phone_number: base.String,
                 first_name: typing.Optional[base.String] = None,
                 last_name: typing.Optional[base.String] = None):
        super(InputContactMessageContent, self).__init__(phone_number=phone_number, first_name=first_name,
                                                         last_name=last_name)


class InputLocationMessageContent(InputMessageContent):
    """
    Represents the content of a location message to be sent as the result of an inline query.

    https://core.telegram.org/bots/api#inputlocationmessagecontent
    """
    latitude: base.Float = fields.Field()
    longitude: base.Float = fields.Field()
    horizontal_accuracy: typing.Optional[base.Float] = fields.Field()
    live_period: typing.Optional[base.Integer] = fields.Field()
    heading: typing.Optional[base.Integer] = fields.Field()
    proximity_alert_radius: typing.Optional[base.Integer] = fields.Field()

    def __init__(self,
                 latitude: base.Float,
                 longitude: base.Float,
                 horizontal_accuracy: typing.Optional[base.Float] = None,
                 live_period: typing.Optional[base.Integer] = None,
                 heading: typing.Optional[base.Integer] = None,
                 proximity_alert_radius: typing.Optional[base.Integer] = None,
                 ):
        super().__init__(
            latitude=latitude,
            longitude=longitude,
            horizontal_accuracy=horizontal_accuracy,
            live_period=live_period,
            heading=heading,
            proximity_alert_radius=proximity_alert_radius,
        )


class InputTextMessageContent(InputMessageContent):
    """
    Represents the content of a text message to be sent as the result of an inline query.

    https://core.telegram.org/bots/api#inputtextmessagecontent
    """
    message_text: base.String = fields.Field()
    parse_mode: base.String = fields.Field()
    disable_web_page_preview: base.Boolean = fields.Field()

    def safe_get_parse_mode(self):
        try:
            return self.bot.parse_mode
        except RuntimeError:
            pass

    def __init__(
            self,
            message_text: typing.Optional[base.String] = None,
            parse_mode: typing.Optional[base.String] = None,
            caption_entities: typing.Optional[typing.List[MessageEntity]] = None,
            disable_web_page_preview: typing.Optional[base.Boolean] = None,
    ):
        if parse_mode is None:
            parse_mode = self.safe_get_parse_mode()

        super().__init__(
            message_text=message_text, parse_mode=parse_mode,
            caption_entities=caption_entities,
            disable_web_page_preview=disable_web_page_preview,
        )


class InputVenueMessageContent(InputMessageContent):
    """
    Represents the content of a venue message to be sent as the result of an inline query.

    Note: This will only work in Telegram versions released after 9 April, 2016.
    Older clients will ignore them.

    https://core.telegram.org/bots/api#inputvenuemessagecontent
    """
    latitude: base.Float = fields.Field()
    longitude: base.Float = fields.Field()
    title: base.String = fields.Field()
    address: base.String = fields.Field()
    foursquare_id: base.String = fields.Field()
    foursquare_type: base.String = fields.Field()
    google_place_id: base.String = fields.Field()
    google_place_type: base.String = fields.Field()

    def __init__(
            self,
            latitude: typing.Optional[base.Float] = None,
            longitude: typing.Optional[base.Float] = None,
            title: typing.Optional[base.String] = None,
            address: typing.Optional[base.String] = None,
            foursquare_id: typing.Optional[base.String] = None,
            foursquare_type: typing.Optional[base.String] = None,
            google_place_id: typing.Optional[base.String] = None,
            google_place_type: typing.Optional[base.String] = None,
    ):
        super().__init__(
            latitude=latitude, longitude=longitude, title=title,
            address=address, foursquare_id=foursquare_id,
            foursquare_type=foursquare_type, google_place_id=google_place_id,
            google_place_type=google_place_type,
        )
