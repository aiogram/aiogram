from typing import TYPE_CHECKING, Any, Mapping, TypeVar

if TYPE_CHECKING:
    StorageDataT = TypeVar("StorageDataT", bound=Mapping[str, Any])
else:
    StorageDataT = TypeVar("StorageDataT", bound=Mapping)
