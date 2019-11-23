from abc import ABC, abstractmethod
from typing import Any, Dict, Union

from pydantic import BaseModel


class BaseFilter(ABC, BaseModel):
    @abstractmethod
    async def __call__(self, *args, **kwargs) -> Union[bool, Dict[str, Any]]:
        pass

    def __await__(self):
        return self.__call__
