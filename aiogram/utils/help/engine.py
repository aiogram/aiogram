from abc import ABC, abstractmethod
from collections import Generator
from typing import Dict, List

from aiogram.utils.help.record import CommandRecord


class BaseHelpBackend(ABC):
    @abstractmethod
    def add(self, record: CommandRecord) -> None:
        pass

    @abstractmethod
    def search(self, value: str) -> CommandRecord:
        pass

    @abstractmethod
    def all(self) -> Generator[CommandRecord, None, None]:
        pass

    def __getitem__(self, item: str) -> CommandRecord:
        return self.search(item)

    def __iter__(self) -> Generator[CommandRecord, None, None]:
        return self.all()


class MappingBackend(BaseHelpBackend):
    def __init__(self, search_empty_prefix: bool = True) -> None:
        self._records: List[CommandRecord] = []
        self._mapping: Dict[str, CommandRecord] = {}
        self.search_empty_prefix = search_empty_prefix

    def search(self, value: str) -> CommandRecord:
        return self._mapping[value]

    def add(self, record: CommandRecord) -> None:
        new_records = {}
        for key in record.as_keys(with_empty_prefix=self.search_empty_prefix):
            if key in self._mapping:
                raise ValueError(f"Key '{key}' is already indexed")
            new_records[key] = record
        self._mapping.update(new_records)
        self._records.append(record)
        self._records.sort(key=lambda rec: (rec.priority, rec.commands[0]))

    def all(self) -> Generator[CommandRecord, None, None]:
        yield from self._records
