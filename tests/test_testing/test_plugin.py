import subprocess
import sys
import textwrap

import pytest

from aiogram import Dispatcher
from aiogram.methods import SendMessage
from aiogram.test import Blueprint
from aiogram.test.plugin import pytest_assertrepr_compare
from aiogram.test.world import ChatState


def call_fixture(fixture, *args, **kwargs):
    """Fixtures cannot be called directly; reach the function they wrap."""
    return fixture.__wrapped__(*args, **kwargs)


class TestFixtures:
    def test_blueprint_default(self):
        from aiogram.test import plugin

        blueprint = call_fixture(plugin.bot_blueprint)

        assert isinstance(blueprint, Blueprint)
        assert blueprint.users

    def test_dispatcher_default(self):
        from aiogram.test import plugin

        assert isinstance(call_fixture(plugin.bot_dispatcher), Dispatcher)

    def test_environment_is_disposed_after_the_test(self):
        from aiogram.test import plugin

        blueprint = call_fixture(plugin.bot_blueprint)
        dispatcher = call_fixture(plugin.bot_dispatcher)
        original_storage = dispatcher.fsm.storage

        generator = call_fixture(plugin.bot_env, blueprint, dispatcher)
        environment = next(generator)
        assert dispatcher.fsm.storage is not original_storage
        with pytest.raises(StopIteration):
            next(generator)

        assert environment.session.closed is True
        assert dispatcher.fsm.storage is original_storage

    def test_environment_is_disposed_when_the_test_fails(self):
        from aiogram.test import plugin

        blueprint = call_fixture(plugin.bot_blueprint)
        dispatcher = call_fixture(plugin.bot_dispatcher)
        original_storage = dispatcher.fsm.storage

        generator = call_fixture(plugin.bot_env, blueprint, dispatcher)
        environment = next(generator)
        with pytest.raises(RuntimeError, match="boom"):
            generator.throw(RuntimeError("boom"))

        assert environment.session.closed is True
        assert dispatcher.fsm.storage is original_storage

    def test_chat_and_user_accessors(self, env):
        from aiogram.test import plugin

        chat = call_fixture(plugin.bot_chat, env)
        actor = call_fixture(plugin.bot_user, env)

        assert chat.id == env.blueprint.chats[0].id
        assert actor.chat.id == env.blueprint.chats[0].id

    def test_user_accessor_without_chats(self):
        from aiogram.test import plugin

        blueprint = Blueprint()
        blueprint.add_user("Lonely")
        dispatcher = Dispatcher()
        generator = call_fixture(plugin.bot_env, blueprint, dispatcher)
        environment = next(generator)
        try:
            actor = call_fixture(plugin.bot_user, environment)
            assert actor.user.first_name == "Lonely"
        finally:
            environment.dispose_sync()


class TestAssertionReporting:
    def test_chat_state_is_described(self, env, private):
        private.add_message(_message(private))

        lines = pytest_assertrepr_compare("==", private, ChatState(id=0))

        assert any("contains 1 message" in line for line in lines)
        assert any("hello" in line for line in lines)

    def test_method_calls_are_diffed(self):
        left = SendMessage(chat_id=1, text="a")
        right = SendMessage(chat_id=1, text="b")

        lines = pytest_assertrepr_compare("==", left, right)

        assert any("text: 'a' != 'b'" in line for line in lines)

    def test_different_method_types(self):
        from aiogram.methods import DeleteMessage

        lines = pytest_assertrepr_compare(
            "==",
            SendMessage(chat_id=1, text="a"),
            DeleteMessage(chat_id=1, message_id=1),
        )

        assert "SendMessage != DeleteMessage" in lines[0]

    async def test_objects_differing_only_in_their_binding_are_explained(self, env, private):
        """
        Pydantic compares private attributes, and ``_bot`` is one; the repr hides it.

        So a mounted object and an identical unmounted one print the same and compare
        unequal — a failure that reads as if pytest had lost its mind.
        """
        returned = await env.bot.send_message(chat_id=private.id, text="hi")
        twin = returned.model_copy().as_(None)

        lines = pytest_assertrepr_compare("==", returned, twin)

        assert any("differ only in the bot they are bound to" in line for line in lines)
        assert any("mounted to bot id=42" in line and "not mounted" in line for line in lines)
        assert any("model_dump()" in line for line in lines)

    async def test_objects_that_really_differ_are_left_alone(self, env, private):
        returned = await env.bot.send_message(chat_id=private.id, text="hi")
        other = returned.model_copy(update={"text": "different"})

        assert pytest_assertrepr_compare("==", returned, other) is None

    def test_other_comparisons_are_left_alone(self):
        from aiogram.types import Chat, User

        assert pytest_assertrepr_compare("==", 1, 2) is None
        assert pytest_assertrepr_compare("<", ChatState(id=1), ChatState(id=2)) is None
        # Same payload is not enough: these are different types.
        assert (
            pytest_assertrepr_compare(
                "==",
                Chat(id=1, type="private"),
                User(id=1, is_bot=False, first_name="A"),
            )
            is None
        )


def _message(chat: ChatState):
    from aiogram.test.world import BASE_DATE
    from aiogram.types import Message

    return Message(
        message_id=chat.allocate_message_id(),
        date=BASE_DATE,
        chat=chat.as_chat(),
        text="hello",
    )


class TestImportGraph:
    """``import aiogram`` must work in production, where pytest is not installed."""

    def test_pytest_is_not_pulled_in_by_the_package(self):
        program = (
            "import sys, aiogram.test; "
            "assert 'pytest' not in sys.modules, 'pytest was imported'; "
            "assert 'aiogram.test.plugin' not in sys.modules, 'plugin was imported'"
        )

        result = subprocess.run(
            [sys.executable, "-c", program],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, result.stdout + result.stderr


class TestPluginDiscovery:
    """The plugin must reach a project through the entry point, with no conftest."""

    def test_fixtures_resolve_in_a_clean_project(self, tmp_path):
        test_file = tmp_path / "test_generated.py"
        test_file.write_text(
            textwrap.dedent(
                """
                def test_fixtures_are_available(bot_env, bot_chat, bot_user):
                    assert bot_env.bot.id
                    assert bot_chat.id
                    assert bot_user.user.id
                """,
            ),
        )

        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_file), "-q", "-p", "no:cacheprovider"],
            capture_output=True,
            text=True,
            cwd=tmp_path,
            check=False,
        )

        assert result.returncode == 0, result.stdout + result.stderr
