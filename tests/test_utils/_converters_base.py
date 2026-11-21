"""Fixture for the converter-core contract suite: a base model whose field type is a nested class.

``_converters_sub`` subclasses it from another module; the inherited field must resolve in
this module's namespace and this class body (F-08 plan-10, "resolution per field and per base").
"""

from __future__ import annotations

import enum
from datetime import date

from aiogram.utils._converters import ModelBase


class Base(ModelBase):
    class Kind(enum.Enum):
        A = "a"

    kind: Kind
    day: date = date(2024, 1, 2)
