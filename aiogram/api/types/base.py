import datetime

from pydantic import BaseModel, Extra

from aiogram.utils.mixins import ContextInstanceMixin


class TelegramObject(ContextInstanceMixin, BaseModel):
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
