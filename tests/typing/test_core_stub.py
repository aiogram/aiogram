from typing import assert_type

from aiogram import _core

assert_type(_core.__version__, str)
assert_type(_core.build_info()["profile"], str)
assert_type(_core.ModelSchema(object()).to_flat(object()), list[str])
