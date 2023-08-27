from datetime import datetime

from pydantic import PlainSerializer
from typing_extensions import Annotated

# Make datetime compatible with Telegram Bot API (unixtime)
DateTime = Annotated[
    datetime,
    PlainSerializer(
        func=lambda dt: int(dt.timestamp()),
        return_type=int,
        when_used="json-unless-none",
    ),
]
