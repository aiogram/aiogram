from typing import assert_type

from aiogram import _core
from aiogram._core.conv import JsonCodec, Kind

assert_type(_core.__version__, str)
assert_type(_core.build_info()["profile"], str)
assert_type(_core.conv.Kind.int_(), Kind)
assert_type(Kind.sequence(Kind.int_(), list).label, str)
assert_type(JsonCodec(Kind.int_()).dump_json(1), bytes)
