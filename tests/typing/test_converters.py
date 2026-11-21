# dataclass_transform on ModelBase (PEP 681): what type checkers infer for a model (F-08).
import dataclasses
from typing import assert_type

from aiogram.utils._converters import ModelBase, fields_set, flat_schema, json_schema
from aiogram.utils.converters import field


class Form(ModelBase, rename="camel", frozen=True, slots=True):
    item_id: int
    tags: list[str] = field(default_factory=list)
    note: str = field(default="", key="n")
    page: int = dataclasses.field(default=1, kw_only=False)


form = Form(item_id=1)
assert_type(form.item_id, int)
assert_type(form.tags, list[str])
assert_type(fields_set(form), frozenset[str])
assert_type(json_schema(Form).load({}), Form)
assert_type(json_schema(Form).dump_json(form), bytes)
assert_type(flat_schema(Form).dump(form), list[str])

Form(item_id="x")  # type: ignore[arg-type]
Form()  # type: ignore[call-arg]
form.item_id = 2  # type: ignore[misc]
Form(item_id=1, nope=1)  # type: ignore[call-arg]
