from pydantic import BaseConfig, BaseModel, Extra

from aiogram.utils.mixins import ContextInstanceMixin


class TelegramObject(ContextInstanceMixin, BaseModel):
    class Config(BaseConfig):
        use_enum_values = True
        orm_mode = True
        extra = Extra.allow
        allow_mutation = False
        allow_population_by_field_name = True
