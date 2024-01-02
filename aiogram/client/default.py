from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, Optional, TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from aiogram.types import LinkPreviewOptions


# @dataclass ??
class Default:
    # Is not a dataclass because of JSON serialization.

    __slots__ = ("_name",)

    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def __str__(self) -> str:
        return f"Default({self._name!r})"

    def __repr__(self) -> str:
        return f"<{self}>"


_dataclass_properties: Dict[str, Any] = {}
if sys.version_info >= (3, 10):
    # Speedup attribute access for dataclasses in Python 3.10+
    _dataclass_properties.update({"slots": True, "kw_only": True})


@dataclass(**_dataclass_properties)
class DefaultBotProperties:
    """
    Default bot properties.
    """

    parse_mode: Optional[str] = None
    disable_notification: Optional[bool] = None
    protect_content: Optional[bool] = None
    allow_sending_without_reply: Optional[bool] = None

    link_preview: Optional[LinkPreviewOptions] = None
    link_preview_is_disabled: Optional[bool] = None
    link_preview_prefer_small_media: Optional[bool] = None
    link_preview_prefer_large_media: Optional[bool] = None
    link_preview_show_above_text: Optional[bool] = None

    def __post_init__(self) -> None:
        if any(
            (
                self.link_preview_is_disabled,
                self.link_preview_prefer_small_media,
                self.link_preview_prefer_large_media,
                self.link_preview_show_above_text,
            )
        ):
            from ..types import LinkPreviewOptions

            self.link_preview = LinkPreviewOptions(
                is_disabled=self.link_preview_is_disabled,
                prefer_small_media=self.link_preview_prefer_small_media,
                prefer_large_media=self.link_preview_prefer_large_media,
                show_above_text=self.link_preview_show_above_text,
            )

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item, None)
