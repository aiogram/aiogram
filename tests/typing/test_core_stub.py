from typing import assert_type

from aiogram import _core

assert_type(_core.__version__, str)
assert_type(_core.build_info()["profile"], str)
assert_type(_core.Kind.sequence(_core.Kind.int_(), list).label, str)
assert_type(_core.JsonCodec(_core.Kind.int_()).dump_json(1), bytes)
