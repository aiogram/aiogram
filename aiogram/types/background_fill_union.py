from __future__ import annotations

from typing import Union

from .background_fill_freeform_gradient import BackgroundFillFreeformGradient
from .background_fill_gradient import BackgroundFillGradient
from .background_fill_solid import BackgroundFillSolid

BackgroundFillUnion = Union[
    BackgroundFillSolid, BackgroundFillGradient, BackgroundFillFreeformGradient
]
