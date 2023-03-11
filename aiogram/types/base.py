import datetime
from typing import Any
from unittest.mock import sentinel

from pydantic import BaseModel, Extra

from aiogram.utils.mixins import ContextInstanceMixin


class TelegramObject(ContextInstanceMixin["TelegramObject"], BaseModel):
    class Config:
        use_enum_values = True
        orm_mode = True
        extra = Extra.allow
        validate_assignment = True
        allow_mutation = False
        allow_population_by_field_name = True
        json_encoders = {datetime.datetime: lambda dt: int(dt.timestamp())}


class MutableTelegramObject(TelegramObject):
    class Config:
        allow_mutation = True


# special sentinel object which used in situation when None might be a useful value
UNSET_PARSE_MODE: Any = sentinel.UNSET_PARSE_MODE
UNSET_DISABLE_WEB_PAGE_PREVIEW = sentinel.UNSET_DISABLE_WEB_PAGE_PREVIEW
UNSET_PROTECT_CONTENT = sentinel.UNSET_PROTECT_CONTENT
UNSET_TYPE = type(sentinel.DEFAULT)
