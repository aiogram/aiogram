from datetime import datetime, timedelta
from typing import Union

from pydantic import PlainSerializer
from typing_extensions import Annotated

# Make datetime compatible with Telegram Bot API (unixtime)


def _serialize_datetime(dt: Union[datetime, timedelta, int]) -> int:
    if isinstance(dt, int):
        return dt
    if isinstance(dt, timedelta):
        dt = datetime.now() + dt
    return int(dt.timestamp())


DateTime = Annotated[
    Union[datetime, timedelta, int],
    PlainSerializer(
        func=_serialize_datetime,
        return_type=int,
    ),
]
