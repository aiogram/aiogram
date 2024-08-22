import warnings
from typing import Optional

from pydantic import BaseModel, ConfigDict

from aiogram.enums import ParseMode
from aiogram.types import LinkPreviewOptions


class DefaultBotProperties(BaseModel):
    """
    Default bot properties.
    """

    model_config = ConfigDict(
        frozen=True,
    )

    parse_mode: Optional[ParseMode] = None
    """Default parse mode for messages."""
    disable_notification: Optional[bool] = None
    """Sends the message silently. Users will receive a notification with no sound."""
    protect_content: Optional[bool] = None
    """Protects content from copying."""
    allow_sending_without_reply: Optional[bool] = None
    """Allows to send messages without reply."""
    link_preview_options: Optional[LinkPreviewOptions] = None
    """Link preview settings."""

    @property
    def is_empty(self) -> bool:
        return all(
            getattr(self, field_name) == field_info.default
            for field_name, field_info in self.model_fields.items()
        )

    def __init__(
        self,
        *,
        parse_mode: Optional[ParseMode] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        allow_sending_without_reply: Optional[bool] = None,
        link_preview: Optional[LinkPreviewOptions] = None,
        link_preview_options: Optional[LinkPreviewOptions] = None,
        link_preview_is_disabled: Optional[bool] = None,
        link_preview_prefer_small_media: Optional[bool] = None,
        link_preview_prefer_large_media: Optional[bool] = None,
        link_preview_show_above_text: Optional[bool] = None,
    ):
        has_any_link_preview_option = any(
            (
                link_preview_is_disabled,
                link_preview_prefer_small_media,
                link_preview_prefer_large_media,
                link_preview_show_above_text,
            )
        )
        if has_any_link_preview_option:
            warnings.warn(
                "Passing `link_preview_is_disabled`, `link_preview_prefer_small_media`, "
                "`link_preview_prefer_large_media`, and `link_preview_show_above_text` "
                "to DefaultBotProperties initializer is deprecated. "
                "These arguments will be removed in 3.7.0 version\n"
                "Use `link_preview` instead.",
                category=DeprecationWarning,
                stacklevel=2,
            )
        if link_preview:
            warnings.warn(
                "Passing `link_preview` to DefaultBotProperties initializer is deprecated. "
                "This argument will be removed in 3.7.0 version\n"
                "Use `link_preview_options` instead.",
                category=DeprecationWarning,
                stacklevel=2,
            )
        super().__init__(
            parse_mode=parse_mode,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_sending_without_reply=allow_sending_without_reply,
            link_preview_options=link_preview_options or link_preview,
        )
