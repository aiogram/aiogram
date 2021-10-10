from typing import Any

from magic_filter import AttrDict, MagicFilter

from aiogram.dispatcher.filters import BaseFilter
from aiogram.types import TelegramObject


class MagicData(BaseFilter):
    magic_data: MagicFilter

    class Config:
        arbitrary_types_allowed = True

    async def __call__(self, event: TelegramObject, *args: Any, **kwargs: Any) -> bool:
        return bool(
            self.magic_data.resolve(
                AttrDict({"event": event, **{k: v for k, v in enumerate(args)}, **kwargs})
            )
        )
