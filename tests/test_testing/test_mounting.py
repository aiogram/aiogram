import datetime

import pytest

from aiogram import Bot
from aiogram.test.mounting import bindables, bound_elsewhere, detach, detached_copy, mount
from aiogram.types import (
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ReactionTypeEmoji,
    User,
)

DATE = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
#: Deeper than `copy.deepcopy` survives (~200 levels) and than pydantic-core will
#: serialize, so a copy that manages it cannot be doing either.
DEEP = 1500


def message(**fields):
    return Message(message_id=1, date=DATE, chat=Chat(id=1, type="private"), **fields)


def reply_chain(length):
    """A reply chain `length` messages long — the deepest shape the fake produces."""
    chain = message(text="0")
    for index in range(1, length):
        chain = Message(
            message_id=index + 1,
            date=DATE,
            chat=Chat(id=1, type="private"),
            reply_to_message=chain,
        )
    return chain


def depth_of(chain):
    depth = 0
    while chain is not None:
        depth += 1
        chain = chain.reply_to_message
    return depth


class TestMount:
    def test_it_binds_everything_it_reaches(self, env):
        original = message(from_user=User(id=7, is_bot=False, first_name="A"))

        mount(original, env.bot)

        assert original.bot is env.bot
        assert original.chat.bot is env.bot
        assert original.from_user.bot is env.bot

    def test_binding_a_node_does_not_prune_what_hangs_off_it(self, env):
        """
        The walk decides to prune before the caller gets its hands on the node.

        `mount` binds what it is yielded, so a prune check made afterwards would find every
        object it had just claimed already bound and stop there — leaving a message bound
        and everything inside it, chat and sender and keyboard, unbound.
        """
        original = message(
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Go", callback_data="go")]],
            ),
        )

        mount(original, env.bot)

        assert original.reply_markup.inline_keyboard[0][0].bot is env.bot

    def test_it_reaches_into_a_mapping(self, env):
        """`extra="allow"` parks a future Bot API version's objects in plain dicts."""
        original = message(future_field={"deep": message(text="nested")})

        mount(original, env.bot)

        assert original.future_field["deep"].bot is env.bot

    def test_an_object_with_an_owner_is_left_to_it(self, env):
        other = Bot(token="43:OTHER", session=env.session)
        owned = message()
        owned.as_(other)

        mount(owned, env.bot)

        assert owned.bot is other

    def test_the_walk_stops_at_an_owned_object(self, env):
        other = Bot(token="43:OTHER", session=env.session)
        inner = message(text="inner")
        inner.as_(other)
        outer = message(text="outer", pinned_message=inner)

        mount(outer, env.bot)

        assert outer.bot is env.bot
        # Not env.bot's to claim, and neither is anything it holds.
        assert inner.chat.bot is None


class TestDetach:
    def test_it_unbinds_in_place(self, env):
        original = mount(message(from_user=User(id=7, is_bot=False, first_name="A")), env.bot)

        returned = detach(original)

        assert returned is original
        assert original.bot is None
        assert original.chat.bot is None
        assert original.from_user.bot is None

    def test_it_reaches_past_an_already_unbound_node(self, env):
        """`detach` prunes nothing: an unbound holder may still carry bound objects."""
        inner = mount(message(text="inner"), env.bot)
        outer = message(text="outer", pinned_message=inner)

        detach(outer)

        assert inner.bot is None


class TestDetachedCopy:
    def test_the_copy_shares_nothing_with_the_original(self):
        original = message(from_user=User(id=7, is_bot=False, first_name="A"))

        copied = detached_copy(original)

        assert copied is not original
        assert copied.chat is not original.chat
        assert copied.from_user is not original.from_user
        assert copied.model_dump() == original.model_dump()

    def test_the_original_keeps_its_binding(self, env):
        original = mount(message(), env.bot)

        copied = detached_copy(original)

        assert original.bot is env.bot
        assert original.chat.bot is env.bot
        assert copied.bot is None
        assert copied.chat.bot is None

    def test_the_copy_can_be_born_owned(self, env):
        original = message()

        copied = detached_copy(original, bot=env.bot)

        assert copied.bot is env.bot
        assert copied.chat.bot is env.bot
        assert original.bot is None

    def test_a_shared_object_stays_shared_within_the_copy(self):
        chat = Chat(id=1, type="private")
        first = Message(message_id=1, date=DATE, chat=chat)
        second = Message(message_id=2, date=DATE, chat=chat, reply_to_message=first)

        copied = detached_copy(second)

        assert copied.chat is copied.reply_to_message.chat
        assert copied.chat is not chat

    def test_a_cycle_does_not_hang_the_copy(self):
        looping = message()
        # `frozen=True` forbids assignment, so plant the cycle in the field storage itself.
        looping.__dict__["pinned_message"] = looping

        copied = detached_copy(looping)

        assert copied is not looping
        assert copied.pinned_message is copied

    def test_a_deep_graph_is_copied_without_recursion(self):
        """
        The whole point of building the copy iteratively.

        `copy.deepcopy` gives up around 200 levels and pydantic-core's serializer reports
        the depth as a circular reference — while the mount walk handles any depth, so a
        canned result or a trigger field the fake can mount must also be one it can copy.
        """
        chain = reply_chain(DEEP)

        copied = detached_copy(chain)

        assert depth_of(copied) == DEEP
        assert copied.reply_to_message is not chain.reply_to_message

    def test_a_scalar_is_handed_back_as_it_is(self):
        assert detached_copy(True) is True
        assert detached_copy("text") == "text"
        assert detached_copy(None) is None

    def test_a_list_result_is_copied_item_by_item(self):
        items = [message(text="a"), message(text="b")]

        copied = detached_copy(items)

        assert copied == items
        assert copied is not items
        assert copied[0] is not items[0]

    def test_a_tuple_is_rebuilt_rather_than_filled(self):
        """A tuple cannot be filled after the fact, so it is built from finished children."""
        nested = (message(text="deep"),)
        original = (nested, message(text="shallow"))

        copied = detached_copy(original)

        assert isinstance(copied, tuple)
        assert isinstance(copied[0], tuple)
        assert copied[0][0] is not nested[0]
        assert copied[0][0].text == "deep"

    def test_a_nested_tuple_found_early_is_still_built_first(self):
        """
        Discovery order does not follow nesting: a shared inner tuple can be reached
        through a list before the tuple that holds it is reached at all, and building the
        holder first would fill it with the reservation instead of the copy.
        """
        inner = (message(text="inner"),)
        original = {"through a list": [inner], "through a tuple": (inner,)}

        copied = detached_copy(original)

        assert copied["through a tuple"][0] is copied["through a list"][0]
        assert copied["through a tuple"][0][0].text == "inner"

    def test_a_set_is_rebuilt_as_a_set(self):
        """`bindables` walks any iterable, so the copy has to reach into one too."""
        reaction = ReactionTypeEmoji(emoji="👍")

        copied = detached_copy({reaction})

        assert isinstance(copied, set)
        assert copied.pop() is not reaction

    def test_a_mapping_is_copied_key_by_key(self):
        original = {"outer": {"inner": message(text="nested")}}

        copied = detached_copy(original)

        assert copied["outer"]["inner"] is not original["outer"]["inner"]
        assert copied["outer"]["inner"].text == "nested"

    def test_unknown_fields_are_copied_too(self):
        """`extra="allow"` parks a future Bot API version's objects outside the fields."""
        original = message(future_field={"deep": message(text="from the future")})

        copied = detached_copy(original)

        assert copied.future_field["deep"] is not original.future_field["deep"]
        assert copied.future_field["deep"].text == "from the future"

    def test_a_live_bot_is_never_followed(self, env):
        """
        A binding is not part of the value, so the copy never reaches through one.

        Following it would deep-copy a bot with a session, a world and a dispatcher behind
        it — which is why binding is decided as the copy is made rather than afterwards.
        """
        original = mount(message(), env.bot)

        copied = detached_copy(original, bot=env.bot)

        assert copied.bot is env.bot
        assert copied.bot.session is env.session


class TestBoundElsewhere:
    def test_an_unbound_graph_belongs_to_nobody(self, env):
        assert bound_elsewhere(message(), env.bot) is False

    def test_the_environments_own_objects_are_not_foreign(self, env):
        assert bound_elsewhere(mount(message(), env.bot), env.bot) is False

    def test_an_equal_bot_is_still_a_different_owner(self, env, blueprint, dp):
        """
        Identity, not equality: `Bot.__eq__` compares token hashes.

        Two environments built from one blueprint therefore have equal bots, and only
        comparing them by identity tells whose object this is.
        """
        from aiogram.test import BotTestEnvironment

        other = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            assert other.bot == env.bot
            assert bound_elsewhere(mount(message(), other.bot), env.bot) is True
        finally:
            other.dispose_sync()


class TestBindables:
    def test_a_deep_graph_is_walked_without_recursion(self):
        assert sum(1 for _ in bindables(reply_chain(DEEP))) == DEEP * 2

    @pytest.mark.parametrize("value", [None, "text", 5, 1.5, b"bytes"])
    def test_scalars_yield_nothing(self, value):
        assert list(bindables(value)) == []

    def test_an_owned_node_is_yielded_before_the_walk_stops(self, env):
        inner = mount(message(text="inner"), env.bot)
        outer = message(text="outer", pinned_message=inner)

        yielded = [id(node) for node in bindables(outer, prune_bound=True)]

        assert id(inner) in yielded
        # ...but nothing it holds, which is the pruning.
        assert id(inner.chat) not in yielded
