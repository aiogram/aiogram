"""
Types and methods build their schema on first use, not at ``import aiogram``.

Each check runs in a fresh interpreter: this test process imports :mod:`aiogram.test`,
which builds every schema up front, so nothing here would still be unbuilt.
"""

import subprocess
import sys
import textwrap


def run_fresh(code: str) -> str:
    result = subprocess.run(
        [sys.executable, "-c", textwrap.dedent(code)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_import_builds_no_schema():
    out = run_fresh(
        """
        from aiogram import methods, types

        for module in (types, methods):
            for name in module.__all__:
                obj = getattr(module, name)
                # the abstract TelegramMethod is built as the origin of TelegramMethod[...]
                if hasattr(obj, "model_rebuild") and name not in {"Request", "Response", "TelegramMethod"}:
                    if obj.__pydantic_complete__:
                        print(name)
        """
    )
    assert out == ""


def test_every_type_and_method_builds_on_first_use():
    out = run_fresh(
        """
        from aiogram import methods, types

        def first_use(model):
            model.__pydantic_validator__.validate_python  # raises if not fully defined

        names = 0
        for module in (types, methods):
            for name in module.__all__:
                obj = getattr(module, name)
                if hasattr(obj, "model_rebuild"):
                    first_use(obj)
                    assert obj.__pydantic_complete__, name
                    names += 1
        print(names)
        """
    )
    assert int(out) > 600  # every model of both packages, about 430 types and 200 methods


def test_never_built_type_nested_in_other_contexts():
    run_fresh(
        """
        from pydantic import BaseModel, TypeAdapter

        from aiogram.types import CallbackQuery, Chat, Message

        chat = {"id": 1, "type": "private"}
        message = {"message_id": 1, "date": 1, "chat": chat, "reply_to_message": {
            "message_id": 2, "date": 1, "chat": chat,
        }}

        class Box(BaseModel):
            message: Message

        assert Box.model_validate({"message": message}).message.reply_to_message.chat.id == 1
        assert TypeAdapter(list[Chat]).validate_python([chat])[0].id == 1

        class MyQuery(CallbackQuery):
            pass

        query = {"id": "1", "chat_instance": "1", "from": {
            "id": 1, "is_bot": False, "first_name": "a",
        }, "message": message}
        assert MyQuery.model_validate(query).message.chat.id == 1
        """
    )


def test_concurrent_first_use():
    run_fresh(
        """
        import threading

        from aiogram.types import Update

        data = {"update_id": 1, "message": {
            "message_id": 1, "date": 1, "chat": {"id": 1, "type": "private"}, "text": "hi",
        }}
        barrier = threading.Barrier(8)
        results, errors = [], []

        def validate():
            barrier.wait()
            try:
                results.append(Update.model_validate(data))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=validate) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert not errors, errors
        assert len(results) == 8
        assert all(result == results[0] for result in results)
        """
    )
