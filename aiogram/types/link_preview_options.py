from typing import TYPE_CHECKING, Any, Optional, Union

from pydantic import field_serializer, field_validator

from ..client.default import Default
from .base import TelegramObject


class LinkPreviewOptions(TelegramObject):
    """
    Describes the options used for link preview generation.

    Source: https://core.telegram.org/bots/api#linkpreviewoptions
    """

    is_disabled: Optional[Union[bool, Default]] = Default("link_preview_is_disabled")
    """*Optional*. :code:`True`, if the link preview is disabled"""
    url: Optional[str] = None
    """*Optional*. URL to use for the link preview. If empty, then the first URL found in the message text will be used"""
    prefer_small_media: Optional[Union[bool, Default]] = Default("link_preview_prefer_small_media")
    """*Optional*. :code:`True`, if the media in the link preview is supposed to be shrunk; ignored if the URL isn't explicitly specified or media size change isn't supported for the preview"""
    prefer_large_media: Optional[Union[bool, Default]] = Default("link_preview_prefer_large_media")
    """*Optional*. :code:`True`, if the media in the link preview is supposed to be enlarged; ignored if the URL isn't explicitly specified or media size change isn't supported for the preview"""
    show_above_text: Optional[Union[bool, Default]] = Default("link_preview_show_above_text")
    """*Optional*. :code:`True`, if the link preview must be shown above the message text; otherwise, the link preview will be shown below the message text"""

    @field_serializer(
        "is_disabled",
        "prefer_small_media",
        "prefer_large_media",
        "show_above_text",
        when_used="json",
    )
    def serialize_fields(self, value: Union[bool, Default]) -> str:
        if isinstance(value, bool):
            return str(value)
        else:
            return value.name

    @classmethod
    @field_validator(
        "is_disabled",
        "prefer_small_media",
        "prefer_large_media",
        "show_above_text",
        mode="before",
    )
    def deserialize_fields(cls, value: str) -> Union[bool, Default]:
        if value == "True":
            return True
        elif value == "False":
            return False
        else:
            return Default(value)

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            is_disabled: Optional[Union[bool, Default]] = Default("link_preview_is_disabled"),
            url: Optional[str] = None,
            prefer_small_media: Optional[Union[bool, Default]] = Default(
                "link_preview_prefer_small_media"
            ),
            prefer_large_media: Optional[Union[bool, Default]] = Default(
                "link_preview_prefer_large_media"
            ),
            show_above_text: Optional[Union[bool, Default]] = Default(
                "link_preview_show_above_text"
            ),
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                is_disabled=is_disabled,
                url=url,
                prefer_small_media=prefer_small_media,
                prefer_large_media=prefer_large_media,
                show_above_text=show_above_text,
                **__pydantic_kwargs,
            )
