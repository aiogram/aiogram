import subprocess
import sys

import pytest
from pydantic import BaseModel
from pydantic.version import VERSION as PYDANTIC_VERSION

import aiogram.methods as methods_module
import aiogram.types as types_module
from aiogram.methods import SendMessage
from aiogram.methods.base import Response
from aiogram.types import Message

PYDANTIC_VERSION_INFO = tuple(map(int, PYDANTIC_VERSION.split(".")[:2]))

MESSAGE_DATA = {
    "message_id": 42,
    "date": 1234567890,
    "chat": {"id": -42, "type": "supergroup"},
    "reply_to_message": {
        "message_id": 41,
        "date": 1234567889,
        "chat": {"id": -42, "type": "supergroup"},
    },
}

LAZY_BUILD_SCRIPT = """
import aiogram
from aiogram.methods import SendMessage
from aiogram.types import Message

assert not Message.__pydantic_complete__, "Message schema was built on import"
assert not SendMessage.__pydantic_complete__, "SendMessage schema was built on import"

Message.model_validate(%r)
assert Message.__pydantic_complete__, "Message schema was not built on first use"
""" % (MESSAGE_DATA,)


def _models(module):
    for name in module.__all__:
        entity = getattr(module, name)
        if not (isinstance(entity, type) and issubclass(entity, BaseModel)):
            continue
        # Generic models (e.g. TelegramMethod) are built through their parametrization
        if getattr(entity, "__parameters__", ()):
            continue
        yield name, entity


class TestLazyModelBuild:
    @pytest.mark.parametrize("module", [types_module, methods_module])
    def test_forward_refs_are_resolvable(self, module):
        unresolved = [name for name, entity in _models(module) if entity.model_rebuild() is False]
        assert unresolved == []

    def test_nested_model_is_resolvable_from_foreign_model(self):
        # Models defined outside of aiogram resolve nested types through
        # the namespace exposed in the globals of the type modules.
        class Container(BaseModel):
            message: Message

        container = Container.model_validate({"message": MESSAGE_DATA})

        assert container.message.chat.id == -42
        assert container.message.reply_to_message.message_id == 41

    def test_generic_response_is_resolvable(self):
        response = Response[Message].model_validate({"ok": True, "result": MESSAGE_DATA})

        assert response.result.chat.type == "supergroup"

    def test_method_with_nested_type_is_resolvable(self):
        method = SendMessage.model_validate(
            {
                "chat_id": -42,
                "text": "test",
                "reply_parameters": {"message_id": 41},
            }
        )

        assert method.reply_parameters.message_id == 41

    @pytest.mark.skipif(
        PYDANTIC_VERSION_INFO < (2, 6),
        reason="pydantic<2.6 requires eager model rebuild on import",
    )
    def test_models_are_not_built_on_import(self):
        # Building every model schema on import costs seconds of startup time,
        # so schemas must stay deferred until the model is actually used.
        subprocess.run([sys.executable, "-c", LAZY_BUILD_SCRIPT], check=True)
