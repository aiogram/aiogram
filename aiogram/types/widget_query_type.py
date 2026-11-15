from .base import TelegramObject


class WidgetQueryType(TelegramObject):
    """
    This object describes the type of a query from a widget. Currently, it can be one of

     - :class:`aiogram.types.widget_query_type_data.WidgetQueryTypeData`
     - :class:`aiogram.types.widget_query_type_sign_data.WidgetQueryTypeSignData`
     - :class:`aiogram.types.widget_query_type_sent_transaction.WidgetQueryTypeSentTransaction`

    Source: https://core.telegram.org/bots/api#widgetquerytype
    """
