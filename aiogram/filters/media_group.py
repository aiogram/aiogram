from typing import Any, Literal

from aiogram.filters.base import Filter
from aiogram.types import Message

MIN_MEDIA_COUNT = 2
DEFAULT_MAX_MEDIA_COUNT = 10


class MediaGroupFilter(Filter):
    """
    This filter helps to handle media groups.

    Works only with :class:`aiogram.types.message.Message` events which have the :code:`album`
    in the handler context.
    """

    __slots__ = ("min_media_count", "max_media_count")

    def __init__(
        self,
        count: int | None = None,
        min_media_count: int | None = None,
        max_media_count: int | None = None,
    ):
        """
        :param count: expected count of media in the group.
        :param min_media_count: min count of media in the group, inclusively
        :param max_media_count: max count of media in the group, inclusively
        """
        if count is None:
            min_media_count = min_media_count or MIN_MEDIA_COUNT
            max_media_count = max_media_count or DEFAULT_MAX_MEDIA_COUNT
        else:
            if min_media_count is not None or max_media_count is not None:
                raise ValueError(
                    "count and min_media_count or max_media_count can not be used together"
                )
            if count < MIN_MEDIA_COUNT:
                raise ValueError(f"count should be greater or equal to {MIN_MEDIA_COUNT}")
            min_media_count = max_media_count = count
        if min_media_count < MIN_MEDIA_COUNT:
            raise ValueError(f"min_media_count should be greater or equal to {MIN_MEDIA_COUNT}")
        if max_media_count < min_media_count:
            raise ValueError("max_media_count should be greater or equal to min_media_count")
        self.min_media_count = min_media_count
        self.max_media_count = max_media_count

    def __str__(self) -> str:
        return self._signature_to_string(
            min_media_count=self.min_media_count, max_media_count=self.max_media_count
        )

    async def __call__(
        self, message: Message, album: list[Message] = None
    ) -> Literal[False] | dict[str, Any]:
        media_count = len(album or [])
        if not (self.min_media_count <= media_count <= self.max_media_count):
            return False
        return {"media_count": media_count}
