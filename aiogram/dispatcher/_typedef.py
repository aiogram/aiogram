from typing import TYPE_CHECKING, Any, Mapping, TypeVar

if TYPE_CHECKING:  # pragma: no cover
    StorageDataT = TypeVar("StorageDataT", bound=Mapping[Any, Any])
else:
    StorageDataT = TypeVar("StorageDataT", bound=Mapping)
