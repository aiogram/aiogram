from __future__ import annotations

import datetime
import typing

from pydantic import BaseModel, Extra

from aiogram.utils.mixins import ContextInstanceMixin

if typing.TYPE_CHECKING:
    from ..client.bot import Bot  # pragma: no cover


class TelegramObject(ContextInstanceMixin["TelegramObject"], BaseModel):
    class Config:
        use_enum_values = True
        orm_mode = True
        extra = Extra.allow
        validate_assignment = True
        allow_mutation = False
        allow_population_by_field_name = True
        json_encoders = {datetime.datetime: lambda dt: int(dt.timestamp())}

    @property
    def bot(self) -> Bot:
        from ..client.bot import Bot

        bot = Bot.get_current()
        if bot is None:
            raise RuntimeError(
                "Can't get bot instance from context. "
                "You can fix it with setting current instance: "
                "'Bot.set_current(bot_instance)'"
            )
        return bot


class MutableTelegramObject(TelegramObject):
    class Config:
        allow_mutation = True
