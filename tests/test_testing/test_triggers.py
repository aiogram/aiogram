import pytest

from aiogram import Dispatcher
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import AnswerPreCheckoutQuery, AnswerShippingQuery
from aiogram.test import Blueprint, BotTestEnvironment
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Update

#: How to drive each update variant: the actor to use, and what to call on it.
#: The guard below *invokes* these, so a mapping that names the wrong trigger fails.
TRIGGERS = {
    "message": ("plain", lambda actor: actor.send("hi")),
    "edited_message": ("plain", lambda actor: actor.edit(actor.chat.messages[-1], "edited")),
    "channel_post": ("channel", lambda actor: actor.send("headline")),
    "edited_channel_post": (
        "channel",
        lambda actor: actor.edit(actor.chat.messages[-1], "corrected"),
    ),
    "business_connection": ("business", lambda actor: actor.enable_business_connection()),
    "business_message": ("business", lambda actor: actor.send("hi")),
    "edited_business_message": (
        "business",
        lambda actor: actor.edit(actor.chat.messages[-1], "edited"),
    ),
    "deleted_business_messages": ("business", lambda actor: actor.delete_business_messages([1])),
    "guest_message": ("plain", lambda actor: actor.guest_message("let me in")),
    "inline_query": ("plain", lambda actor: actor.inline_query("search")),
    "chosen_inline_result": ("plain", lambda actor: actor.chosen_inline_result("result-1")),
    "callback_query": ("plain", lambda actor: actor.click("go")),
    "shipping_query": ("plain", lambda actor: actor.shipping_query()),
    "pre_checkout_query": ("plain", lambda actor: actor.pre_checkout_query()),
    "purchased_paid_media": ("plain", lambda actor: actor.purchase_paid_media()),
    "my_chat_member": ("plain", lambda actor: actor.add_bot()),
    "chat_member": ("plain", lambda actor: actor.join()),
    "chat_join_request": ("plain", lambda actor: actor.request_join()),
    "chat_boost": ("plain", lambda actor: actor.boost()),
    "removed_chat_boost": ("plain", lambda actor: actor.remove_boost()),
    "managed_bot": ("plain", lambda actor: actor.manage_bot()),
    "subscription": ("plain", lambda actor: actor.update_subscription()),
    "poll": ("plain", lambda actor: actor.poll_update(_only_poll(actor))),
    "poll_answer": ("plain", lambda actor: actor.vote(_only_poll(actor), [0])),
    "message_reaction": ("plain", lambda actor: actor.react(actor.chat.messages[-1], "👍")),
    "message_reaction_count": (
        "plain",
        lambda actor: actor.reaction_count(actor.chat.messages[-1]),
    ),
}


def _only_poll(actor):
    """The id of the single poll in the actor's environment."""
    (poll_id,) = actor.environment.world.polls
    return poll_id


def update_variants():
    return sorted(name for name in Update.model_fields if name not in {"update_id", "Source"})


class TestEveryUpdateKindIsReachable:
    """The guard that keeps this change true as the Bot API grows — design decision D1."""

    @pytest.fixture
    def trigger_env(self, dp):
        blueprint = Blueprint()
        user = blueprint.add_user("Ann")
        private = blueprint.add_private_chat(user)
        channel = blueprint.add_channel("News")
        connection = blueprint.add_business_connection(user)
        environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            base = environment.user(user)
            yield (
                environment,
                {
                    "plain": base.in_(private),
                    "channel": base.in_(channel),
                    "business": base.in_(private, business=connection),
                },
            )
        finally:
            environment.dispose_sync()

    @pytest.mark.parametrize("variant", update_variants())
    async def test_a_trigger_produces_this_update(self, trigger_env, variant):
        assert variant in TRIGGERS, f"no actor trigger produces the {variant!r} update"

        env, actors = trigger_env
        captured = []

        @env.dispatcher.update.outer_middleware()
        async def capture(handler, event, data):
            captured.append(event)
            return await handler(event, data)

        binding, call = TRIGGERS[variant]
        actor = actors[binding]
        # A few triggers need something to act on first.
        if variant in {"edited_message", "edited_channel_post", "edited_business_message"}:
            await actor.send("original")
        if variant in {"message_reaction", "message_reaction_count"}:
            await actor.send("react to me")
        if variant in {"poll", "poll_answer"}:
            await env.bot.send_poll(
                chat_id=actor.chat.id,
                question="Tabs or spaces?",
                options=["Tabs", "Spaces"],
                is_anonymous=variant == "poll",
            )
        if variant == "callback_query":
            await env.bot.send_message(
                chat_id=actor.chat.id,
                text="hi",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="Go", callback_data="go")]],
                ),
            )

        await call(actor)

        assert getattr(captured[-1], variant) is not None, (
            f"{TRIGGERS[variant]} did not produce a {variant!r} update"
        )

    def test_no_variant_is_exempt(self):
        """Every variant is driven for real — there is no exemption set left."""
        assert set(TRIGGERS) == set(update_variants())


class TestQueryRegistry:
    async def test_answering_the_current_query_succeeds(self, env, private, alice):
        markup = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Go", callback_data="go")]],
        )
        await env.bot.send_message(chat_id=private.id, text="hi", reply_markup=markup)
        seen = []
        env.dispatcher.callback_query.register(lambda query: seen.append(query.id))

        await alice.click("go")

        assert await env.bot.answer_callback_query(callback_query_id=seen[0]) is True

    async def test_answering_a_fabricated_id_fails(self, env):
        with pytest.raises(TelegramBadRequest, match="query is too old"):
            await env.bot.answer_callback_query(callback_query_id="never-issued")

    async def test_answering_twice_fails(self, env, private, alice):
        markup = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Go", callback_data="go")]],
        )
        await env.bot.send_message(chat_id=private.id, text="hi", reply_markup=markup)
        seen = []
        env.dispatcher.callback_query.register(lambda query: seen.append(query.id))
        await alice.click("go")
        await env.bot.answer_callback_query(callback_query_id=seen[0])

        with pytest.raises(TelegramBadRequest, match="query is too old"):
            await env.bot.answer_callback_query(callback_query_id=seen[0])

    async def test_answering_an_inline_query(self, env, alice):
        seen = []
        env.dispatcher.inline_query.register(lambda query: seen.append(query.id))

        await alice.inline_query("search")

        assert await env.bot.answer_inline_query(inline_query_id=seen[0], results=[]) is True

    async def test_a_query_id_of_the_wrong_kind_is_not_accepted(self, env, alice):
        """An inline query id must not satisfy a callback query answer."""
        seen = []
        env.dispatcher.inline_query.register(lambda query: seen.append(query.id))
        await alice.inline_query("search")

        with pytest.raises(TelegramBadRequest, match="query is too old"):
            await env.bot.answer_callback_query(callback_query_id=seen[0])

    async def test_outstanding_queries_do_not_leak_between_environments(self, blueprint):
        first = BotTestEnvironment(blueprint=blueprint, dispatcher=Dispatcher())
        second = BotTestEnvironment(blueprint=blueprint, dispatcher=Dispatcher())
        try:
            alice = first.user(blueprint.users[0])
            seen = []
            first.dispatcher.inline_query.register(lambda query: seen.append(query.id))
            await alice.inline_query("search")

            with pytest.raises(TelegramBadRequest, match="query is too old"):
                await second.bot.answer_inline_query(inline_query_id=seen[0], results=[])
        finally:
            first.dispose_sync()
            second.dispose_sync()


class TestJoinRequests:
    @pytest.fixture
    def outsider_env(self, dp):
        """A group and a user who is deliberately *not* a member of it."""
        blueprint = Blueprint()
        outsider = blueprint.add_user("Outsider")
        blueprint.add_supergroup("Club")
        environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            yield environment, environment.user(outsider), environment.chat(blueprint.chats[0])
        finally:
            environment.dispose_sync()

    async def test_a_request_reaches_its_handler(self, outsider_env):
        env, outsider, club = outsider_env
        seen = []
        env.dispatcher.chat_join_request.register(lambda event: seen.append(event.from_user.id))

        await outsider.in_(club).request_join()

        assert seen == [outsider.user.id]
        assert outsider.user.id in club.join_requests

    async def test_approving_adds_the_member(self, outsider_env):
        env, outsider, club = outsider_env
        assert not club.member(outsider.user.id).is_present
        await outsider.in_(club).request_join()

        await env.bot.approve_chat_join_request(chat_id=club.id, user_id=outsider.user.id)

        assert club.member(outsider.user.id).is_present
        assert outsider.user.id not in club.join_requests

    async def test_declining_leaves_the_user_out(self, outsider_env):
        env, outsider, club = outsider_env
        await outsider.in_(club).request_join()

        await env.bot.decline_chat_join_request(chat_id=club.id, user_id=outsider.user.id)

        assert outsider.user.id not in club.join_requests
        assert not club.member(outsider.user.id).is_present

    @pytest.mark.parametrize(
        "method_name",
        ["approve_chat_join_request", "decline_chat_join_request"],
    )
    async def test_acting_on_a_request_that_does_not_exist_fails(self, outsider_env, method_name):
        env, outsider, club = outsider_env

        with pytest.raises(TelegramBadRequest, match="no join request is pending"):
            await getattr(env.bot, method_name)(chat_id=club.id, user_id=outsider.user.id)


class TestChannelPosts:
    @pytest.fixture
    def channel_env(self, dp):
        blueprint = Blueprint()
        blueprint.add_user("Author")
        blueprint.add_channel("News")
        environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            yield environment, blueprint
        finally:
            environment.dispose_sync()

    async def test_a_post_routes_as_a_channel_post(self, channel_env):
        env, blueprint = channel_env
        posts, messages = [], []
        env.dispatcher.channel_post.register(lambda message: posts.append(message.text))
        env.dispatcher.message.register(lambda message: messages.append(message.text))
        author = env.user(blueprint.users[0]).in_(blueprint.chats[0])

        await author.send("headline")

        assert posts == ["headline"]
        assert messages == []

    async def test_a_channel_post_is_attributed_to_the_channel(self, channel_env):
        env, blueprint = channel_env
        channel = env.chat(blueprint.chats[0])
        author = env.user(blueprint.users[0]).in_(channel)

        await author.send("headline")

        stored = channel.messages[-1]
        assert stored.from_user is None
        assert stored.sender_chat.id == channel.id
        assert stored.author_signature == "Author"

    async def test_editing_a_post_routes_as_an_edited_channel_post(self, channel_env):
        env, blueprint = channel_env
        channel = env.chat(blueprint.chats[0])
        author = env.user(blueprint.users[0]).in_(channel)
        await author.send("headline")
        edits = []
        env.dispatcher.edited_channel_post.register(lambda message: edits.append(message.text))

        await author.edit(channel.messages[-1], "corrected")

        assert edits == ["corrected"]


class TestPaymentFlow:
    async def test_a_full_payment_reaches_every_handler(self, env, alice):
        """The whole flow, each step answered with the id its own handler received."""
        seen = []

        async def on_shipping(query):
            seen.append(("shipping", query.invoice_payload))
            await env.bot.answer_shipping_query(
                shipping_query_id=query.id,
                ok=True,
                shipping_options=[],
            )

        async def on_pre_checkout(query):
            seen.append(("pre_checkout", query.invoice_payload))
            await env.bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=True)

        env.dispatcher.shipping_query.register(on_shipping)
        env.dispatcher.pre_checkout_query.register(on_pre_checkout)
        env.dispatcher.message.register(
            lambda message: seen.append(("paid", message.successful_payment.invoice_payload)),
        )

        await alice.shipping_query("order-1")
        await alice.pre_checkout_query("order-1")
        await alice.pay("order-1")

        assert seen == [
            ("shipping", "order-1"),
            ("pre_checkout", "order-1"),
            ("paid", "order-1"),
        ]
        assert env.world.pending_queries == {}

    async def test_a_payment_message_lands_in_the_chat(self, env, private, alice):
        await alice.pay("order-1")

        assert private.messages[-1].successful_payment.invoice_payload == "order-1"

    async def test_digital_goods_skip_the_shipping_step(self, env, alice):
        seen = []
        env.dispatcher.pre_checkout_query.register(lambda query: seen.append(query.id))

        await alice.pre_checkout_query("order-1")

        assert await env.bot.answer_pre_checkout_query(
            pre_checkout_query_id=seen[0],
            ok=True,
        )

    async def test_failing_a_pre_checkout_clears_the_query(self, env, alice):
        seen = []
        env.dispatcher.pre_checkout_query.register(lambda query: seen.append(query.id))
        await alice.pre_checkout_query("order-1")

        await env.bot.answer_pre_checkout_query(
            pre_checkout_query_id=seen[0],
            ok=False,
            error_message="Out of stock",
        )

        with pytest.raises(TelegramBadRequest, match="query is too old"):
            await env.bot.answer_pre_checkout_query(pre_checkout_query_id=seen[0], ok=True)

    @pytest.mark.parametrize(
        ("method_type", "argument"),
        [
            (AnswerShippingQuery, "shipping_query_id"),
            (AnswerPreCheckoutQuery, "pre_checkout_query_id"),
        ],
        ids=lambda item: getattr(item, "__name__", item),
    )
    async def test_answering_an_unregistered_query_fails(self, env, method_type, argument):
        with pytest.raises(TelegramBadRequest, match="query is too old"):
            await env.bot(method_type(**{argument: "never-issued", "ok": True}))


class TestRemainingUpdateKinds:
    async def test_chosen_inline_result(self, env, alice):
        seen = []
        env.dispatcher.chosen_inline_result.register(lambda event: seen.append(event.result_id))

        await alice.chosen_inline_result("result-1", "search")

        assert seen == ["result-1"]

    async def test_purchased_paid_media(self, env, alice):
        seen = []
        env.dispatcher.purchased_paid_media.register(
            lambda event: seen.append(event.paid_media_payload),
        )

        await alice.purchase_paid_media("media-1")

        assert seen == ["media-1"]

    async def test_chat_boosts(self, env, team, alice):
        added, removed = [], []
        env.dispatcher.chat_boost.register(lambda event: added.append(event.chat.id))
        env.dispatcher.removed_chat_boost.register(lambda event: removed.append(event.chat.id))
        actor = alice.in_(team)

        await actor.boost()
        await actor.remove_boost()

        assert added == [team.id]
        assert removed == [team.id]

    async def test_guest_message(self, env, private, alice):
        seen = []
        env.dispatcher.guest_message.register(lambda message: seen.append(message.text))

        await alice.guest_message("let me in")

        assert seen == ["let me in"]
        assert private.messages[-1].text == "let me in"

    async def test_managed_bot(self, env, alice):
        seen = []
        env.dispatcher.managed_bot.register(lambda event: seen.append(event.user.id))

        await alice.manage_bot()

        assert seen == [alice.user.id]

    async def test_subscription(self, env, alice):
        seen = []
        env.dispatcher.subscription.register(lambda event: seen.append(event.invoice_payload))

        await alice.update_subscription("sub-1")

        assert seen == ["sub-1"]

    async def test_event_from_user_resolves_on_the_new_triggers(self, env, alice):
        seen = []

        async def handler(event, event_from_user):
            seen.append(event_from_user.id)

        env.dispatcher.chosen_inline_result.register(handler)
        await alice.chosen_inline_result("result-1")

        assert seen == [alice.user.id]


class TestBotMembership:
    async def test_the_bots_own_membership_is_my_chat_member(self, env, team, alice):
        """A bot registering only `my_chat_member` must not see other members' changes."""
        mine, others = [], []
        env.dispatcher.my_chat_member.register(
            lambda event: mine.append(event.new_chat_member.status),
        )
        env.dispatcher.chat_member.register(
            lambda event: others.append(event.new_chat_member.status),
        )
        actor = alice.in_(team)

        await actor.add_bot()
        await actor.remove_bot()
        await actor.join()

        assert mine == ["member", "left"]
        assert others == ["member"]

    async def test_removing_the_bot_updates_the_membership_state(self, env, team, alice):
        actor = alice.in_(team)
        await actor.add_bot()

        await actor.remove_bot()

        assert not team.member(env.world.bot_user.id).is_present

    async def test_a_membership_change_keeps_what_the_membership_carries(self, env, team, alice):
        """A join or a leave changes the status, not the rights that came with it."""
        seen = []
        env.dispatcher.chat_member.register(seen.append)
        actor = alice.in_(team)
        await env.bot.promote_chat_member(
            chat_id=team.id,
            user_id=alice.user.id,
            can_delete_messages=True,
        )

        await actor.leave()

        event = seen[-1]
        assert event.old_chat_member.can_delete_messages is True
        assert event.old_chat_member.can_manage_chat is False
        assert event.new_chat_member.status == "left"


class TestCallerSuppliedObjects:
    """
    What a test hands a trigger stays the test's own.

    An update is mounted to the bot on the way in, and everything nested in it with it, so
    a trigger that embedded the caller's object would bind a shared constant to a bot for
    the rest of the session — and it would no longer compare equal to the copy the world
    keeps, since the binding counts towards equality.
    """

    async def test_a_field_object_is_copied_before_it_is_stored(self, env, private, alice):
        markup = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Go", callback_data="go")]],
        )

        await alice.send("menu", fields={"reply_markup": markup})

        stored = private.messages[-1].reply_markup
        assert stored is not markup
        assert stored.inline_keyboard[0][0].callback_data == "go"
        # The stored copy is bound to the bot, like everything the world holds; the
        # test's own object is left alone.
        assert stored.bot is env.bot
        assert markup.bot is None

    async def test_an_edit_copies_its_fields_too(self, env, private, alice):
        markup = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Go", callback_data="go")]],
        )
        await alice.send("menu")

        await alice.edit(private.messages[-1], "menu", fields={"reply_markup": markup})

        stored = private.messages[-1].reply_markup
        assert stored.inline_keyboard[0][0].callback_data == "go"
        assert stored is not markup
        assert markup.bot is None
