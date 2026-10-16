"""
``env.all_routes`` and ``env.assert_updates_handled()``: where
every update of a test went, not only the last trigger's.
"""

import subprocess
import sys
import textwrap
from types import SimpleNamespace

import pytest

from aiogram import F
from aiogram.types import Update


@pytest.fixture
def game(dp):
    @dp.message(F.text == "/start")
    async def on_start(message):
        return "started"

    @dp.message(F.text == "/crash")
    async def on_crash(message):
        msg = "no such player"
        raise KeyError(msg)

    return dp


class TestRouteHistory:
    async def test_every_trigger_is_kept_in_order(self, env, game, alice):
        await alice.send("/start")
        await alice.send("hello")
        await alice.send("/start")

        history = env.all_routes
        assert [record.handled for record in history] == [True, False, True]
        assert env.routes == [history[-1]]

    async def test_a_trigger_keeps_its_updates_together(self, env, game, alice):
        await alice.send("first")
        with env.trigger():
            await alice.send("/start")
            await alice.send("second")

        assert [record.handled for record in env.all_routes] == [False, True, False]

    async def test_an_update_fed_to_the_dispatcher_directly_is_kept(self, env, game, alice):
        await alice.send("/start")
        update = Update(update_id=99, message=env.chat(alice.user.id).messages[-1])

        await env.dispatcher.feed_update(env.bot, update)

        assert [record.update_id for record in env.all_routes][-1] == 99

    def test_it_is_empty_before_anything_is_fed(self, env):
        assert env.all_routes == []


class TestAssertUpdatesHandled:
    async def test_a_handled_test_passes(self, env, game, alice):
        await alice.send("/start")

        env.assert_updates_handled()

    def test_a_test_that_fed_nothing_passes(self, env):
        env.assert_updates_handled()

    async def test_an_unhandled_update_fails_it(self, env, game, alice):
        await alice.send("/start")
        await alice.send("hello")
        await alice.send("/start")

        with pytest.raises(AssertionError) as failure:
            env.assert_updates_handled()

        message = str(failure.value)
        assert message.startswith("1 update(s) fed to this environment went unhandled")
        assert "(message) was NOT handled" in message
        assert "assert_unhandled()" in message

    async def test_an_update_whose_error_was_swallowed_fails_it(self, env, game, alice):
        @game.errors()
        async def swallow(event):
            return True

        await alice.send("/crash")

        with pytest.raises(AssertionError, match="raised:  KeyError"):
            env.assert_updates_handled()

    async def test_a_trigger_with_one_handled_update_passes(self, env, game, alice):
        """A join's service message nobody claims: the join was handled."""
        with env.trigger():
            await alice.send("/start")
            await alice.send("service")

        env.assert_updates_handled()

    async def test_a_raise_beside_a_handled_update_still_fails(self, env, game, alice):
        with env.trigger():
            await alice.send("/start")
            with pytest.raises(KeyError):
                await alice.send("/crash")

        with pytest.raises(AssertionError, match="1 update"):
            env.assert_updates_handled()


class TestExpectUnhandled:
    async def test_an_ignored_update_is_accounted_for(self, env, game, alice):
        await alice.send("hello")

        [record] = env.assert_unhandled()

        assert record.handled is False
        env.assert_updates_handled()

    async def test_an_expected_failure_is_returned_for_checking(self, env, game, alice):
        with pytest.raises(KeyError):
            await alice.send("/crash")

        [record] = env.assert_unhandled()

        assert isinstance(record.exception, KeyError)
        env.assert_updates_handled()

    async def test_only_the_last_trigger_is_accounted_for(self, env, game, alice):
        await alice.send("hello")
        await alice.send("again")
        env.assert_unhandled()

        with pytest.raises(AssertionError, match="1 update"):
            env.assert_updates_handled()

    async def test_a_handled_trigger_is_not_expected_to_be_unhandled(self, env, game, alice):
        await alice.send("/start")

        with pytest.raises(AssertionError, match="were handled") as failure:
            env.assert_unhandled()

        assert "on_start" in str(failure.value)

    def test_nothing_routed_is_an_error(self, env):
        with pytest.raises(AssertionError, match="no update has been routed"):
            env.assert_unhandled()

    async def test_inside_a_trigger_it_accounts_for_that_trigger(self, env, game, alice):
        with env.trigger():
            await alice.send("hello")
            env.assert_unhandled()
            await alice.send("again")

        env.assert_updates_handled()


def _item(environment, *, check):
    funcargs = {"bot_env": environment, "bot_env_assert_updates_handled": check}
    return SimpleNamespace(funcargs=funcargs)


class TestPluginCheck:
    def test_it_is_off_by_default(self):
        from aiogram.test import plugin

        assert plugin.bot_env_assert_updates_handled.__wrapped__() is False

    async def test_a_passing_test_is_checked(self, env, game, alice):
        from aiogram.test import plugin

        await alice.send("hello")
        hook = plugin.pytest_runtest_call(_item(env, check=True))
        next(hook)

        with pytest.raises(AssertionError, match="went unhandled"):
            hook.send("result")

    async def test_nothing_is_checked_unless_asked(self, env, game, alice):
        from aiogram.test import plugin

        await alice.send("hello")
        hook = plugin.pytest_runtest_call(_item(env, check=False))
        next(hook)

        with pytest.raises(StopIteration) as stop:
            hook.send("result")
        assert stop.value.value == "result"

    def test_a_failed_test_is_not_checked(self, env):
        from aiogram.test import plugin

        hook = plugin.pytest_runtest_call(_item(env, check=True))
        next(hook)

        with pytest.raises(RuntimeError, match="the test's own"):
            hook.throw(RuntimeError("the test's own"))

    def test_an_item_without_fixtures_is_left_alone(self):
        from aiogram.test import plugin

        hook = plugin.pytest_runtest_call(SimpleNamespace())
        next(hook)

        with pytest.raises(StopIteration):
            hook.send(None)

    def test_the_plugin_fails_a_passing_test_that_left_an_update(self, tmp_path):
        test_file = tmp_path / "test_generated.py"
        test_file.write_text(
            textwrap.dedent(
                """
                import pytest


                @pytest.fixture
                def bot_env_assert_updates_handled():
                    return True


                async def test_forgot_one(bot_env, bot_user):
                    await bot_user.send("hello")


                async def test_meant_it(bot_env, bot_user):
                    await bot_user.send("hello")
                    bot_env.assert_unhandled()
                """,
            ),
        )

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                str(test_file),
                "-q",
                "-p",
                "no:cacheprovider",
                "-o",
                "asyncio_mode=auto",
            ],
            capture_output=True,
            text=True,
            cwd=tmp_path,
            check=False,
        )

        output = result.stdout + result.stderr
        assert result.returncode == 1, output
        assert "1 failed, 1 passed" in output
        assert "test_forgot_one" in output
        assert "went unhandled or raised" in output
