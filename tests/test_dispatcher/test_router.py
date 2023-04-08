import pytest

from aiogram.dispatcher.event.bases import UNHANDLED, SkipHandler, skip
from aiogram.dispatcher.event.telegram import TelegramEventObserver
from aiogram.dispatcher.router import Router


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

    def test_including_many_routers(self):
        router = Router()
        router1 = Router()
        router2 = Router()

        router.include_routers(router1, router2)

        assert router.sub_routers == [router1, router2]

    def test_including_many_routers_bad_type(self):
        router = Router()
        with pytest.raises(ValueError, match="At least one router must be provided"):
            router.include_routers()

    def test_include_router_by_string_bad_type(self):
        router = Router()
        with pytest.raises(ValueError, match=r"router should be instance of Router"):
            router.include_router(self)

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

    async def test_router_chain_tail(self):
        r1 = Router(name="Router 1")
        r2_1 = Router(name="Router 2-1")
        r2_2 = Router(name="Router 2-2")
        r3 = Router(name="Router 3")

        r1.include_router(r2_1)
        r1.include_router(r2_2)
        r2_1.include_router(r3)

        assert tuple(r1.chain_tail) == (r1, r2_1, r3, r2_2)
        assert tuple(r2_1.chain_tail) == (r2_1, r3)
        assert tuple(r2_2.chain_tail) == (r2_2,)
        assert tuple(r3.chain_tail) == (r3,)

    async def test_router_chain_head(self):
        r1 = Router(name="Router 1")
        r2_1 = Router(name="Router 2-1")
        r2_2 = Router(name="Router 2-2")
        r3 = Router(name="Router 3")

        r1.include_router(r2_1)
        r1.include_router(r2_2)
        r2_1.include_router(r3)

        assert tuple(r1.chain_head) == (r1,)
        assert tuple(r2_1.chain_head) == (r2_1, r1)
        assert tuple(r2_2.chain_head) == (r2_2, r1)
        assert tuple(r3.chain_head) == (r3, r2_1, r1)

    async def test_custom_evenv_nested_router(self):
        r1 = Router()
        r2 = Router()
        r3 = Router()
        r3.observers["custom-event"] = TelegramEventObserver(r3, event_name="custom-event")

        async def handler(evt):
            return evt

        r1.include_router(r2)
        r1.include_router(r3)
        r3.observers["custom-event"].register(handler)

        assert await r1.propagate_event(update_type="custom-event", event=None) is None
        assert await r2.propagate_event(update_type="custom-event", event=None) is UNHANDLED
        assert await r3.propagate_event(update_type="custom-event", event=None) is None
