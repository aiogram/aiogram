import datetime

from aiogram.utils.mixins import ContextInstanceMixin
from pydantic import BaseConfig, BaseModel, Extra


class TelegramObject(ContextInstanceMixin, BaseModel):
    class Config(BaseConfig):
        use_enum_values = True
        orm_mode = True
        extra = Extra.allow
        validate_assignment = True
        allow_population_by_field_name = True
        json_encoders = {datetime.datetime: lambda dt: int(dt.timestamp())}
