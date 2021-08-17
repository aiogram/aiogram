import pytest

from aiogram.dispatcher.event.bases import UNHANDLED, SkipHandler, skip
from aiogram.dispatcher.router import Router
from aiogram.utils.warnings import CodeHasNoEffect

pytestmark = pytest.mark.asyncio
importable_router = Router()


class TestRouter:
    def test_including_routers(self):
        router1 = Router()
        router2 = Router()
        router3 = Router()
        assert router1.parent_router is None
        assert router2.parent_router is None
        assert router3.parent_router is None

        with pytest.raises(RuntimeError, match="Self-referencing routers is not allowed"):
            router1.include_router(router1)

        router1.include_router(router2)

        with pytest.raises(RuntimeError, match="Router is already attached"):
            router1.include_router(router2)

        router2.include_router(router3)

        with pytest.raises(RuntimeError, match="Circular referencing of Router is not allowed"):
            router3.include_router(router1)

        assert router1.parent_router is None
        assert router1.sub_routers == [router2]
        assert router2.parent_router is router1
        assert router2.sub_routers == [router3]
        assert router3.parent_router is router2
        assert router3.sub_routers == []

    def test_include_router_code_has_no_effect(self):
        router1 = Router()
        router2 = Router(use_builtin_filters=False)

        assert router1.use_builtin_filters
        assert not router2.use_builtin_filters
        with pytest.warns(CodeHasNoEffect):
            assert router1.include_router(router2)

    def test_include_router_by_string(self):
        router = Router()
        router.include_router("tests.test_dispatcher.test_router:importable_router")

    def test_include_router_by_string_bad_type(self):
        router = Router()
        with pytest.raises(ValueError, match=r"router should be instance of Router"):
            router.include_router("tests.test_dispatcher.test_router:TestRouter")

    def test_set_parent_router_bad_type(self):
        router = Router()
        with pytest.raises(ValueError, match=r"router should be instance of Router"):
            router.parent_router = object()

    def test_observers_config(self):
        router = Router()

        assert router.observers["message"] == router.message
        assert router.observers["edited_message"] == router.edited_message
        assert router.observers["channel_post"] == router.channel_post
        assert router.observers["edited_channel_post"] == router.edited_channel_post
        assert router.observers["inline_query"] == router.inline_query
        assert router.observers["chosen_inline_result"] == router.chosen_inline_result
        assert router.observers["callback_query"] == router.callback_query
        assert router.observers["shipping_query"] == router.shipping_query
        assert router.observers["pre_checkout_query"] == router.pre_checkout_query
        assert router.observers["poll"] == router.poll

    async def test_emit_startup(self):
        router1 = Router()
        router2 = Router()
        router1.include_router(router2)

        results = []

        @router1.startup()
        async def startup1():
            results.append(1)

        @router2.startup()
        async def startup2():
            results.append(2)

        await router2.emit_startup()
        assert results == [2]

        await router1.emit_startup()
        assert results == [2, 1, 2]

    async def test_emit_shutdown(self):
        router1 = Router()
        router2 = Router()
        router1.include_router(router2)

        results = []

        @router1.shutdown()
        async def shutdown1():
            results.append(1)

        @router2.shutdown()
        async def shutdown2():
            results.append(2)

        await router2.emit_shutdown()
        assert results == [2]

        await router1.emit_shutdown()
        assert results == [2, 1, 2]

    def test_skip(self):
        with pytest.raises(SkipHandler):
            skip()
        with pytest.raises(SkipHandler, match="KABOOM"):
            skip("KABOOM")

    async def test_global_filter_in_nested_router(self):
        r1 = Router()
        r2 = Router()

        async def handler(evt):
            return evt

        r1.include_router(r2)
        r1.message.filter(lambda evt: False)
        r2.message.register(handler)

        assert await r1.propagate_event(update_type="message", event=None) is UNHANDLED
