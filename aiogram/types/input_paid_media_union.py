from __future__ import annotations

from typing import Annotated, TypeAlias

from pydantic import Field

from .input_paid_media_live_photo import InputPaidMediaLivePhoto
from .input_paid_media_photo import InputPaidMediaPhoto
from .input_paid_media_video import InputPaidMediaVideo

InputPaidMediaUnion: TypeAlias = Annotated[
    InputPaidMediaLivePhoto | InputPaidMediaPhoto | InputPaidMediaVideo,
    Field(discriminator="type"),
]
