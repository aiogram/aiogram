from typing import TYPE_CHECKING, Any, Generic, TypeVar

from aiogram.filters.command.base import CommandStart

if TYPE_CHECKING:
    from magic_filter import MagicFilter

    from aiogram.filters.command.data.base import DeeplinkData

T = TypeVar("T", bound="DeeplinkData")


class DeeplinkCommand(CommandStart, Generic[T]):
    def __init__(
        self,
        data: type[T] | None = None,
        ignore_case: bool = False,
        ignore_mention: bool = False,
        magic: MagicFilter | None = None,
    ) -> None:
        if data is not None and data.__prefix__ is None:
            raise ValueError(f"{data.__name__} has no prefix. Set prefix= on the class.")
        super().__init__(
            deep_link=True,
            deep_link_encoded=False,
            ignore_case=ignore_case,
            ignore_mention=ignore_mention,
            magic=magic,
        )
        self._data = data

    def __str__(self) -> str:
        return self._signature_to_string(
            self._data,
            ignore_case=self.ignore_case,
            ignore_mention=self.ignore_mention,
            magic=self.magic,
        )

    def _has_data(self) -> bool:
        return self._data is not None

    def _parse_args(self, args: str) -> Any:
        return self._data.unpack(args)  # type: ignore[union-attr]
