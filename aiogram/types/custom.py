import sys
from datetime import datetime

from pydantic import PlainSerializer
from typing_extensions import Annotated

if sys.platform == "win32":  # pragma: no cover

    def _datetime_serializer(value: datetime) -> int:
        # https://github.com/aiogram/aiogram/issues/349
        # https://github.com/aiogram/aiogram/pull/880
        return round((value - datetime(1970, 1, 1)).total_seconds())

else:  # pragma: no cover

    def _datetime_serializer(value: datetime) -> int:
        return round(value.timestamp())


# Make datetime compatible with Telegram Bot API (unixtime)
DateTime = Annotated[
    datetime,
    PlainSerializer(
        func=_datetime_serializer,
        return_type=int,
        when_used="unless-none",
    ),
]
