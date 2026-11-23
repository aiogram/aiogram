"""Utilities: keyboards, formatting, entity unparsing, CallbackData filters, deserialization."""

from __future__ import annotations

from typing import Any

from benchmarks.harness import REGISTRY, Ctx


def _keyboard(input_id: str) -> None:
    @REGISTRY.case(input_id)
    def setup(ctx: Ctx) -> Any:
        """Build the pinned markup button by button with ``add`` + ``adjust`` + ``as_markup``."""
        expected = ctx.json(input_id)
        adapter = ctx.adapter
        buttons, width = adapter.keyboard_buttons(expected)
        assert adapter.keyboard_dump(adapter.build_keyboard(buttons, width)) == expected
        build = adapter.build_keyboard
        return lambda: build(buttons, width)


_keyboard("keyboard.inline.30")
_keyboard("keyboard.inline.100")


@REGISTRY.case("formatting.nested")
def formatting_nested(ctx: Ctx) -> Any:
    """``Text.from_entities(...).as_html()``."""
    text, items = ctx.adapter.entities(ctx.json("formatting.nested"))
    render = ctx.adapter.formatting_html
    return lambda: render(text, items)


@REGISTRY.case("entities.unparse")
def entities_unparse(ctx: Ctx) -> Any:
    """``html_decoration.unparse(text, entities)``."""
    text, items = ctx.adapter.entities(ctx.json("entities.unparse"))
    unparse = ctx.adapter.unparse_html
    return lambda: unparse(text, items)


@REGISTRY.case("callback_data.filter.miss")
def callback_data_miss(ctx: Ctx) -> Any:
    """Run the filters in order until one matches, as the router would; only the last does."""
    spec = ctx.toml("callback_data.filter.miss")
    filters = ctx.adapter.callback_filters(spec)
    query = ctx.adapter.callback_query(spec["data"])

    async def first_match() -> Any:
        for flt in filters:
            if result := await flt(query):
                return result
        return None

    matched = ctx.run(first_match())
    assert matched and matched["callback_data"].__prefix__ == spec["classes"][-1]["prefix"]
    return first_match


@REGISTRY.case("utils.deserialize", uses=["request.sendMessage.defaults"])
def utils_deserialize(ctx: Ctx) -> Any:
    spec = ctx.toml("request.sendMessage.defaults")
    method = ctx.adapter.build_method(spec, ctx.file)
    defaults = spec.get("defaults", {})
    deserialize = ctx.adapter.deserialize
    return lambda: deserialize(method, defaults)
