from __future__ import annotations

from typing import TypeAlias

from .input_paid_media_photo import InputPaidMediaPhoto
from .input_paid_media_video import InputPaidMediaVideo

InputPaidMediaUnion: TypeAlias = InputPaidMediaPhoto | InputPaidMediaVideo
