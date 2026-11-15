from typing import Annotated, TypeAlias

from pydantic import Field

from .widget_query_type_data import WidgetQueryTypeData
from .widget_query_type_sent_transaction import WidgetQueryTypeSentTransaction
from .widget_query_type_sign_data import WidgetQueryTypeSignData

WidgetQueryTypeUnion: TypeAlias = Annotated[
    WidgetQueryTypeData | WidgetQueryTypeSignData | WidgetQueryTypeSentTransaction,
    Field(discriminator="type"),
]
