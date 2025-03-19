from __future__ import annotations

from typing import Union

from .paid_media_photo import PaidMediaPhoto
from .paid_media_preview import PaidMediaPreview
from .paid_media_video import PaidMediaVideo

PaidMediaUnion = Union[PaidMediaPreview, PaidMediaPhoto, PaidMediaVideo]
