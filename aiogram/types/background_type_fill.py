from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Union

from .background_type import BackgroundType

if TYPE_CHECKING:
    from .background_fill_freeform_gradient import BackgroundFillFreeformGradient
    from .background_fill_gradient import BackgroundFillGradient
    from .background_fill_solid import BackgroundFillSolid


class BackgroundTypeFill(BackgroundType):
    """
    The background is automatically filled based on the selected colors.

    Source: https://core.telegram.org/bots/api#backgroundtypefill
    """

    type: Literal["fill"] = "fill"
    """Type of the background, always 'fill'"""
    fill: Union[BackgroundFillSolid, BackgroundFillGradient, BackgroundFillFreeformGradient]
    """The background fill"""
    dark_theme_dimming: int
    """Dimming of the background in dark themes, as a percentage; 0-100"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal["fill"] = "fill",
            fill: Union[
                BackgroundFillSolid, BackgroundFillGradient, BackgroundFillFreeformGradient
            ],
            dark_theme_dimming: int,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                type=type, fill=fill, dark_theme_dimming=dark_theme_dimming, **__pydantic_kwargs
            )
