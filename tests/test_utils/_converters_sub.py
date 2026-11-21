"""Fixture for the converter-core contract suite: a subclass of ``_converters_base.Base``.

Neither ``Kind`` nor ``date`` is defined here: the inherited fields resolve in the base's module.
"""

from __future__ import annotations

from tests.test_utils._converters_base import Base


class Sub(Base):
    extra: Extra | None = None


class Extra(Base):
    note: str = ""
