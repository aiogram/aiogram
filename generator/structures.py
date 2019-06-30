from __future__ import annotations

import typing
from dataclasses import dataclass, field

from generator.normalizers import normalize_type, get_returning, normalize_optional


@dataclass
class Annotation:
    name: str
    type: str
    description: str
    required: bool = True

    @property
    def python_name(self):
        if self.name == "from":
            return "from_user"
        return self.name

    @property
    def python_type(self) -> str:
        result = normalize_type(self.type)
        return normalize_optional(result, self.required)

    @property
    def python_field(self):
        result = f"{self.python_name}: {self.python_type}"

        value = "" if self.required else "None"
        if self.name == "from":
            value = f"pydantic.Schema({value or '...'}, alias=\"from\")"

        if value:
            result += f" = {value}"
        return result


@dataclass
class Entity:
    name: str
    anchor: str
    description: str = None
    annotations: typing.List[Annotation] = field(default_factory=list)

    @property
    def is_method(self) -> bool:
        return self.name[0].islower()

    @property
    def is_type(self) -> bool:
        return not self.is_method

    @property
    def python_name(self) -> str:
        return self.name

    def _get_returning(self):
        if self.is_type:
            return self.name, ""

        return get_returning(self.description)

    @property
    def returning(self):
        return self._get_returning()[1]

    @property
    def returning_type(self):
        return self._get_returning()[0]

    @property
    def python_returning_type(self):
        return normalize_type(self.returning_type)


@dataclass
class Group:
    title: str
    anchor: str
    description: str = None
    childs: typing.List[Entity] = field(default_factory=list)

    @property
    def has_methods(self):
        return any(entity.is_method for entity in self.childs)

    @property
    def has_types(self):
        return any(entity.is_method for entity in self.childs)
