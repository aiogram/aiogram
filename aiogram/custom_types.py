import datetime
from typing import Annotated

from pydantic import PlainSerializer

# Make datetime compatible with Telegram Bot API (unixtime)
DateTime = Annotated[
    datetime,
    PlainSerializer(
        func=lambda dt: int(dt.timestamp()),
        return_type=int,
        when_used="json-unless-none",
    ),
]

# Make string compatible with custom lazy proxy
# String = Union[str, LazyProxy]
