from __future__ import annotations

from typing import Annotated, TypeAlias

from pydantic import Field

from .paid_media_live_photo import PaidMediaLivePhoto
from .paid_media_photo import PaidMediaPhoto
from .paid_media_preview import PaidMediaPreview
from .paid_media_video import PaidMediaVideo

PaidMediaUnion: TypeAlias = Annotated[
    PaidMediaLivePhoto | PaidMediaPhoto | PaidMediaPreview | PaidMediaVideo,
    Field(discriminator="type"),
]
