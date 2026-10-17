"""Actors that are another bot, or an anonymous administrator."""

import pytest

from aiogram import F
from aiogram.enums import ChatMemberStatus
from aiogram.fsm.state import State
from aiogram.methods import GetMe
from aiogram.test import (
    Blueprint,
    BotTestEnvironment,
    CommunityState,
    Withheld,
    WorldLookupError,
    administrator_rights,
)
from aiogram.test.world import PollState
from aiogram.types import (
    CallbackQuery,
    ChatMemberUpdated,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

ANONYMOUS = administrator_rights(is_anonymous=True)
PLAYING = State("playing")


@pytest.fixture
def seen(dp):
    messages: list[Message] = []

    @dp.message()
    async def collect(message: Message) -> None:
        messages.append(message)

    return messages


@pytest.fixture
def build(dp):
    """Build a forum with a human, another bot and an admin."""
    environments = []

    def make(
        *,
        ours=False,
        theirs=False,
        privacy=True,
        bot_status=ChatMemberStatus.MEMBER,
        bot_rights=None,
        service=True,
    ):
        blueprint = Blueprint(bot_to_bot_mode=ours, bot_group_privacy=privacy)
        alice = blueprint.add_user("Alice")
        other = blueprint.add_user(
            "Other", username="other_bot", is_bot=True, bot_to_bot_mode=theirs
        )
        admin = blueprint.add_user("Admin")
        owner = blueprint.add_user("Owner")
        chat = blueprint.add_supergroup(
            "Forum",
            members={alice: ChatMemberStatus.MEMBER, owner: ChatMemberStatus.CREATOR},
            bot_status=bot_status,
            is_forum=True,
        )
        blueprint.set_member(chat, other, rights=administrator_rights())
        blueprint.set_member(chat, admin, rights=ANONYMOUS, custom_title="Host")
        if bot_rights is not None:
            blueprint.set_member(chat, blueprint.bot, rights=bot_rights)
        topic = blueprint.add_topic(chat, "Game")
        channel = blueprint.add_channel("News", members={other: ChatMemberStatus.ADMINISTRATOR})
        environment = BotTestEnvironment(
            blueprint=blueprint,
            dispatcher=dp,
            deliver_service_messages_from_bots=service,
        )
        environments.append(environment)
        return {
            "env": environment,
            "chat": environment.chat(chat),
            "topic": environment.chat(chat).topic(topic.message_thread_id),
            "alice": environment.user(alice).in_(chat),
            "other": environment.user(other).in_(chat),
            "other_spec": other,
            "admin": environment.user(admin),
            "owner": environment.user(owner),
            "channel": environment.chat(channel),
            "chat_spec": chat,
        }

    yield make
    for environment in environments:
        environment.dispose_sync()


class TestDeclaringAnotherBot:
    def test_a_bot_is_declared_with_its_mode(self):
        blueprint = Blueprint(bot_to_bot_mode=True, bot_group_privacy=False)
        other = blueprint.add_user("Other", is_bot=True, bot_to_bot_mode=True)

        world = blueprint.build()

        assert world.user(other.id).is_bot is True
        assert world.user(other.id).bot_to_bot_mode is True
        assert world.bot_user.bot_to_bot_mode is True
        assert world.bot_group_privacy is False

    def test_the_defaults_are_telegrams(self):
        world = Blueprint().build()

        assert world.bot_user.bot_to_bot_mode is False
        assert world.bot_group_privacy is True

    @pytest.mark.parametrize("privacy", [True, False])
    async def test_get_me_reports_group_privacy(self, dp, privacy):
        env = BotTestEnvironment(
            blueprint=Blueprint(bot_group_privacy=privacy),
            dispatcher=dp,
        )
        try:
            me = await env.bot.get_me()
            assert me.can_read_all_group_messages is (not privacy)
            assert (await env.bot.me()).can_read_all_group_messages is (not privacy)
        finally:
            env.dispose_sync()

    @pytest.mark.parametrize("privacy", [True, False])
    async def test_a_change_of_group_privacy_reaches_the_cached_bot(self, dp, privacy):
        env = BotTestEnvironment(
            blueprint=Blueprint(bot_group_privacy=privacy),
            dispatcher=dp,
        )
        try:
            env.world.bot_group_privacy = not privacy

            assert (await env.bot.get_me()).can_read_all_group_messages is privacy
            assert (await env.bot.me()).can_read_all_group_messages is privacy
            assert env.calls.count(GetMe) == 1
        finally:
            env.dispose_sync()

    def test_a_world_without_a_bot_has_nothing_to_refresh(self):
        world = Blueprint().build()

        world.bot_group_privacy = False

        assert world.bot_me().can_read_all_group_messages is True

    def test_a_person_has_no_bot_to_bot_mode(self):
        with pytest.raises(ValueError, match="Only a bot"):
            Blueprint().add_user("Alice", bot_to_bot_mode=True)

    def test_a_running_world_adds_one_too(self, build):
        world = build()
        actor = world["env"].add_user("Late", is_bot=True, bot_to_bot_mode=True)

        assert (actor.user.is_bot, actor.user.bot_to_bot_mode) == (True, True)


class TestAnotherBotsMessages:
    async def test_without_the_mode_it_is_stored_but_not_delivered(self, build, seen):
        world = build()

        result = await world["other"].send("hello")

        stored = world["chat"].messages[-1]
        assert stored.text == "hello"
        assert stored.from_user.is_bot is True
        assert stored.from_user.id == world["other_spec"].id
        assert isinstance(result, Withheld)
        assert result.update.message is stored
        assert "Bot-to-Bot" in result.reason
        assert seen == []
        assert world["env"].routes == []

    @pytest.mark.parametrize(("ours", "theirs"), [(True, False), (False, True)])
    async def test_a_command_naming_the_bot_gets_through_with_either_side(
        self, build, seen, ours, theirs
    ):
        world = build(ours=ours, theirs=theirs)

        await world["other"].send("/start@Test_Bot now")

        assert [message.text for message in seen] == ["/start@Test_Bot now"]

    async def test_a_command_in_a_caption_counts(self, build, seen):
        world = build(theirs=True)

        await world["other"].send(fields={"caption": "/start@test_bot"})

        assert len(seen) == 1

    async def test_a_command_for_another_bot_does_not(self, build, seen):
        world = build(theirs=True)

        result = await world["other"].send("/start@someone_bot")

        assert isinstance(result, Withheld)

    async def test_a_reply_to_the_bot_gets_through(self, build, seen):
        world = build(theirs=True)
        env, chat = world["env"], world["chat"]
        sent = await env.bot.send_message(chat_id=chat.id, text="question")

        await world["other"].reply(sent.message_id, "answer")

        assert [message.text for message in seen] == ["answer"]

    async def test_a_reply_to_someone_else_does_not(self, build, seen):
        world = build(theirs=True)
        await world["alice"].send("hi")
        seen.clear()

        result = await world["other"].reply(world["chat"].messages[-1], "hi Alice")

        assert isinstance(result, Withheld)
        assert seen == []

    async def test_the_topics_root_is_no_reply_to_the_bot(self, build, seen):
        world = build(theirs=True)
        in_topic = world["env"].user(world["other_spec"]).in_(world["chat"], topic=world["topic"])

        result = await in_topic.send("in the game")

        # The declared root is announced as the bot's.
        assert world["chat"].messages[-1].reply_to_message.from_user.is_bot
        assert isinstance(result, Withheld)

    async def test_without_the_mode_on_either_side_nothing_counts(self, build, seen):
        world = build(bot_status=ChatMemberStatus.ADMINISTRATOR)

        result = await world["other"].send("/start@test_bot")

        assert isinstance(result, Withheld)

    @pytest.mark.parametrize(
        ("status", "privacy"),
        [(ChatMemberStatus.ADMINISTRATOR, True), (ChatMemberStatus.MEMBER, False)],
    )
    async def test_with_the_bots_mode_an_admin_or_open_bot_reads_all(
        self, build, seen, status, privacy
    ):
        world = build(ours=True, bot_status=status, privacy=privacy)

        await world["other"].send("plain")

        assert [message.text for message in seen] == ["plain"]

    async def test_with_the_bots_mode_a_private_member_reads_only_mentions(self, build, seen):
        world = build(ours=True)

        result = await world["other"].send("plain")

        assert isinstance(result, Withheld)

    async def test_the_other_bots_mode_alone_reads_no_plain_message(self, build, seen):
        world = build(theirs=True, bot_status=ChatMemberStatus.ADMINISTRATOR)

        result = await world["other"].send("plain")

        assert isinstance(result, Withheld)

    async def test_an_edit_follows_the_same_rule(self, build, seen):
        world = build()
        await world["other"].send("v1")

        result = await world["other"].edit(world["chat"].messages[-1], "v2")

        assert world["chat"].messages[-1].text == "v2"
        assert isinstance(result, Withheld)
        assert result.update.edited_message is not None

    async def test_a_channel_post_is_the_channels(self, build, dp):
        world = build()
        posts = []

        @dp.channel_post()
        async def collect(post: Message) -> None:
            posts.append(post)

        await world["env"].user(world["other_spec"]).in_(world["channel"]).send("news")

        assert [post.text for post in posts] == ["news"]
        assert posts[0].from_user is None

    async def test_a_human_is_never_held_back(self, build, seen):
        world = build()

        await world["alice"].send("plain")

        assert len(seen) == 1


class TestAnotherBotInABusinessChat:
    @pytest.fixture
    def business(self, dp):
        def make(*, theirs):
            blueprint = Blueprint()
            owner = blueprint.add_user("Owner")
            other = blueprint.add_user("Other", is_bot=True, bot_to_bot_mode=theirs)
            blueprint.add_private_chat(other)
            connection = blueprint.add_business_connection(owner)
            env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
            return env, env.user(other).in_(other.id, business=connection)

        return make

    async def test_the_senders_mode_alone_lets_it_in(self, business, dp):
        env, other = business(theirs=True)
        seen = []

        @dp.business_message()
        async def collect(message: Message) -> None:
            seen.append(message)

        try:
            await other.send("hi")
        finally:
            env.dispose_sync()

        assert seen[0].from_user.is_bot is True

    async def test_without_it_the_message_is_refused(self, business):
        env, other = business(theirs=False)
        try:
            with pytest.raises(WorldLookupError, match="business chat"):
                await other.send("hi")
        finally:
            env.dispose_sync()


class TestAnotherBotInPrivate:
    async def test_it_takes_the_mode_on_both_sides(self, build):
        world = build(ours=True)
        other = world["env"].user(world["other_spec"])

        with pytest.raises(WorldLookupError, match="both turn on Bot-to-Bot"):
            await other.send("hi")

    async def test_with_both_it_is_delivered(self, build, seen):
        world = build(ours=True, theirs=True)

        await world["env"].user(world["other_spec"]).send("hi")

        assert [message.text for message in seen] == ["hi"]
        assert seen[0].from_user.is_bot is True


class TestAnotherBotsServiceMessages:
    async def test_closing_a_topic_is_delivered_by_default(self, build, seen):
        world = build()

        await world["other"].close_topic(world["topic"])

        assert world["topic"].is_closed
        closed = seen[-1]
        assert closed.forum_topic_closed is not None
        assert closed.from_user.id == world["other_spec"].id
        assert closed.from_user.is_bot is True

    async def test_the_environment_can_withhold_it(self, build, seen):
        world = build(service=False)

        result = await world["other"].close_topic(world["topic"])

        assert world["topic"].is_closed
        assert world["chat"].messages[-1].forum_topic_closed is not None
        assert isinstance(result, Withheld)
        assert "deliver_service_messages_from_bots=False" in result.reason
        assert seen == []

    async def test_a_withheld_topic_is_still_created(self, build, seen):
        world = build(service=False)

        topic = await world["other"].create_topic("Bots")

        assert topic.root_message.from_user.id == world["other_spec"].id
        assert topic.creator_id == world["other_spec"].id
        assert seen == []

    async def test_its_regular_messages_still_follow_the_mode(self, build, seen):
        world = build(theirs=True, service=False)

        await world["other"].send("/start@test_bot")

        assert len(seen) == 1

    async def test_it_needs_the_right_as_a_user_does(self, build):
        world = build()
        env, chat = world["env"], world["chat"]
        chat.member(world["other_spec"].id).rights = administrator_rights(
            can_manage_topics=False,
        )

        with pytest.raises(WorldLookupError, match="can_manage_topics"):
            await world["other"].close_topic(world["topic"])
        assert not world["topic"].is_closed
        assert env.routes == []


class TestAnonymousAdministrator:
    async def test_a_message_is_the_groups(self, build, seen):
        world = build()
        admin = world["admin"].in_(world["chat"], anonymous=True)

        await admin.send("Night falls")

        message = seen[0]
        assert message.from_user.id == 1087968824
        assert message.from_user.username == "GroupAnonymousBot"
        assert message.from_user.first_name == "Group"
        assert message.from_user.is_bot is True
        assert message.sender_chat.id == world["chat"].id
        assert message.author_signature == "Host"

    async def test_without_a_title_it_is_unsigned(self, build, seen):
        world = build()
        world["chat"].member(world["admin"].user.id).custom_title = None
        admin = world["admin"].in_(world["chat"], anonymous=True)

        await admin.send("hi")

        assert seen[0].author_signature is None

    async def test_a_service_message_carries_the_sender_but_no_signature(self, build, seen):
        world = build()
        admin = world["admin"].in_(world["chat"], anonymous=True)

        await admin.close_topic(world["topic"])
        await admin.hide_general_topic()
        await admin.promote(world["alice"].user)
        world["env"].world.communities[5000] = CommunityState(id=5000, name="Club")
        await admin.add_chat_to_community(5000)
        await admin.create_topic("Mafia")

        assert len(seen) == 4
        for message in seen:
            assert message.from_user.username == "GroupAnonymousBot"
            assert message.sender_chat.id == world["chat"].id
            assert message.author_signature is None
        assert seen[0].forum_topic_closed is not None
        assert seen[1].general_forum_topic_hidden is not None
        assert seen[2].community_chat_added is not None
        assert seen[3].forum_topic_created is not None

    async def test_an_explicit_signature_wins(self, build, seen):
        world = build()
        admin = world["admin"].in_(world["chat"], anonymous=True)

        await admin.send("hi", fields={"author_signature": "Narrator"})

        assert seen[0].author_signature == "Narrator"

    async def test_the_owner_can_be_anonymous_too(self, build, seen):
        world = build()
        owner = world["chat"].member(world["owner"].user.id)
        owner.rights = ANONYMOUS

        await world["owner"].in_(world["chat"], anonymous=True).send("hi")

        assert seen[0].sender_chat.id == world["chat"].id

    async def test_the_rights_are_still_the_users(self, build):
        world = build()
        member = world["chat"].member(world["admin"].user.id)
        member.rights = administrator_rights(is_anonymous=True, can_manage_topics=False)
        admin = world["admin"].in_(world["chat"], anonymous=True)

        with pytest.raises(WorldLookupError, match="can_manage_topics"):
            await admin.close_topic(world["topic"])

    async def test_a_topic_opened_anonymously_is_the_admins(self, build, seen):
        world = build()
        chat = world["chat"]
        for user in (world["admin"].user, world["owner"].user):
            chat.member(user.id).rights = administrator_rights(
                is_anonymous=True, can_manage_topics=False
            )
        chat.member(world["owner"].user.id).status = ChatMemberStatus.ADMINISTRATOR
        admin = world["admin"].in_(chat, anonymous=True)

        topic = await admin.create_topic("Mafia")

        assert topic.creator_id == world["admin"].user.id
        assert topic.root_message.sender_chat.id == chat.id
        # Its creator manages it without the right, bound either way.
        await admin.close_topic(topic)
        await world["admin"].in_(chat).reopen_topic(topic)
        assert not topic.is_closed
        # Another anonymous administrator is not its creator.
        with pytest.raises(WorldLookupError, match="can_manage_topics"):
            await world["owner"].in_(chat, anonymous=True).close_topic(topic)

    async def test_the_bot_to_bot_rule_does_not_apply(self, build, seen):
        world = build()

        await world["admin"].in_(world["chat"], anonymous=True).send("plain")

        assert len(seen) == 1

    async def test_its_fsm_key_is_the_anonymous_bots(self, build, dp):
        world = build()
        admin = world["admin"].in_(world["chat"], anonymous=True)

        @dp.message(F.text == "/play")
        async def play(message: Message, state) -> None:
            await state.set_state(PLAYING)

        await admin.send("/play")

        assert await admin.state().get_state() == PLAYING.state

    async def test_a_promotion_is_from_the_anonymous_bot(self, build, dp):
        world = build()
        updates = []

        @dp.chat_member()
        async def collect(update: ChatMemberUpdated) -> None:
            updates.append(update)

        admin = world["admin"].in_(world["chat"], anonymous=True)
        await admin.promote(world["alice"].user, can_pin_messages=True)

        assert updates[0].from_user.username == "GroupAnonymousBot"

    @pytest.mark.parametrize("trigger", ["join", "leave", "request_join"])
    async def test_joining_or_leaving_is_the_users_own(self, build, trigger):
        world = build()
        admin = world["admin"].in_(world["chat"], anonymous=True)

        with pytest.raises(WorldLookupError, match="anonymous administrator cannot"):
            await getattr(admin, trigger)()

    async def test_it_edits_what_it_posted_as_the_group(self, build, seen):
        world = build()
        admin = world["admin"].in_(world["chat"], anonymous=True)
        await admin.send("v1")

        await admin.edit(world["chat"].messages[-1], "v2")

        assert world["chat"].messages[-1].text == "v2"

    async def test_it_edits_no_one_elses(self, build):
        world = build()
        await world["alice"].send("mine")
        admin = world["admin"].in_(world["chat"], anonymous=True)

        with pytest.raises(WorldLookupError, match="can edit only their own"):
            await admin.edit(world["chat"].messages[-1], "theirs")


class TestBindingAnonymously:
    def test_a_basic_group_has_no_anonymous_administrators(self, dp):
        blueprint = Blueprint()
        admin = blueprint.add_user("Admin")
        group = blueprint.add_group("Group", members={admin: ChatMemberStatus.ADMINISTRATOR})
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            with pytest.raises(WorldLookupError, match="Only a supergroup"):
                env.user(admin).in_(group, anonymous=True)
        finally:
            env.dispose_sync()

    @pytest.mark.parametrize("who", ["alice", "plain admin"])
    def test_only_an_anonymous_administrator_binds(self, build, who):
        world = build()
        if who == "plain admin":
            world["chat"].member(world["admin"].user.id).rights = administrator_rights()
            actor = world["admin"]
        else:
            actor = world["env"].user(world["alice"].user.id)

        with pytest.raises(WorldLookupError, match="is_anonymous=True"):
            actor.in_(world["chat"], anonymous=True)

    async def test_losing_anonymity_later_fails_the_trigger(self, build):
        world = build()
        admin = world["admin"].in_(world["chat"], anonymous=True)
        world["chat"].member(world["admin"].user.id).rights = administrator_rights()

        with pytest.raises(WorldLookupError, match="not an anonymous administrator"):
            await admin.send("hi")


class TestWhatABotCannotDo:
    @pytest.mark.parametrize(
        ("trigger", "args", "action"),
        [
            ("click", ("go",), "press buttons"),
            ("inline_query", ("q",), "use inline mode"),
            ("chosen_inline_result", ("r1",), "use inline mode"),
            ("vote", ("p1", [0]), "vote in polls"),
            ("pay", (), "pay"),
            ("pre_checkout_query", (), "confirm a checkout"),
            ("shipping_query", (), "ask for shipping"),
            ("purchase_paid_media", (), "buy paid media"),
            ("boost", (), "boost a chat"),
            ("remove_boost", (), "withdraw a boost"),
            ("update_subscription", (), "subscribe to the bot"),
            ("follow_deep_link", ("https://t.me/x?start=a",), "follow deep links"),
        ],
    )
    async def test_it_is_refused(self, build, seen, trigger, args, action):
        world = build()

        with pytest.raises(WorldLookupError, match=f"cannot {action}: only a person"):
            await getattr(world["other"], trigger)(*args)
        assert seen == []

    async def test_a_service_message_it_builds_follows_the_switch(self, build, seen):
        world = build()

        await world["other"].send(fields={"new_chat_title": "Renamed"})

        assert seen[0].new_chat_title == "Renamed"

    async def test_the_switch_withholds_one_it_builds_too(self, build, seen):
        world = build(theirs=True, service=False)

        result = await world["other"].send(fields={"new_chat_title": "Renamed"})

        assert "deliver_service_messages_from_bots=False" in result.reason
        assert seen == []


class TestWithheldByTelegram:
    async def test_it_leaves_an_empty_route_scope(self, build, seen):
        world = build()
        env = world["env"]
        await world["alice"].send("handled")
        assert env.last_route is not None

        await world["other"].send("plain")

        assert env.routes == []
        assert env.last_route is None
        with pytest.raises(AssertionError):
            env.assert_handled_by("collect")
        env.assert_updates_handled()

    async def test_its_repr_is_short(self, build):
        world = build()

        result = await world["other"].send("plain")

        text = repr(result)
        assert text.startswith(f"Withheld(update_id={result.update.update_id}, ")
        assert "kind='message'" in text
        assert "reason=" in text
        assert "Message(" not in text


class TestAnonymousBeyondMessages:
    async def test_a_reaction_names_the_chat_and_no_user(self, build, dp):
        world = build()
        await world["alice"].send("vote me")
        reactions = []

        @dp.message_reaction()
        async def collect(update) -> None:
            reactions.append(update)

        admin = world["admin"].in_(world["chat"], anonymous=True)
        message_id = world["chat"].messages[-1].message_id
        await admin.react(message_id, "👍")

        assert reactions[0].user is None
        assert reactions[0].actor_chat.id == world["chat"].id
        assert world["chat"].id in world["chat"].reactions_for(message_id)

    async def test_a_vote_names_the_chat_and_no_user(self, build, dp):
        world = build()
        env, chat = world["env"], world["chat"]
        poll = await env.bot.send_poll(
            chat_id=chat.id, question="Who?", options=["A", "B"], is_anonymous=False
        )
        answers = []

        @dp.poll_answer()
        async def collect(answer) -> None:
            answers.append(answer)

        admin = world["admin"].in_(chat, anonymous=True)
        await admin.vote(poll.poll.id, [1])

        assert answers[0].user is None
        assert answers[0].voter_chat.id == chat.id
        assert env.world.poll(poll.poll.id).votes == {chat.id: [1]}

    async def test_a_click_is_the_users_own_and_so_is_its_key(self, build, dp):
        world = build()
        env, chat = world["env"], world["chat"]
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Play", callback_data="play")]],
        )
        await env.bot.send_message(chat_id=chat.id, text="Ready?", reply_markup=keyboard)
        pressed = []

        @dp.callback_query(F.data == "play")
        async def play(query: CallbackQuery, state) -> None:
            pressed.append(query.from_user.id)
            await state.set_state(PLAYING)

        anonymous = world["admin"].in_(chat, anonymous=True)
        await anonymous.click("play")

        assert pressed == [world["admin"].user.id]
        assert await anonymous.state().get_state() is None
        assert await env.state(world["admin"].user.id, chat).get_state() == PLAYING.state
        assert await world["admin"].in_(chat).state().get_state() == PLAYING.state

    async def test_a_promotion_rechecks_the_binding(self, build):
        world = build()
        chat, alice = world["chat"], world["alice"]
        admin = world["admin"].in_(chat, anonymous=True)
        chat.member(world["admin"].user.id).rights = administrator_rights()

        with pytest.raises(WorldLookupError, match="not an anonymous administrator"):
            await admin.promote(alice.user, can_pin_messages=True)
        assert chat.member(alice.user.id).status == ChatMemberStatus.MEMBER


class TestOneCheckPerTrigger:
    @staticmethod
    def self_managing(world):
        """An anonymous administrator who may promote, and its actor."""
        chat, admin = world["chat"], world["admin"]
        rights = administrator_rights(is_anonymous=True, can_promote_members=True)
        chat.member(admin.user.id).rights = rights
        return chat, admin, admin.in_(chat, anonymous=True)

    async def test_demoting_itself_changes_the_world_and_announces_it(self, build, dp):
        world = build()
        chat, admin, anonymous = self.self_managing(world)
        updates = []

        @dp.chat_member()
        async def collect(update: ChatMemberUpdated) -> None:
            updates.append(update)

        await anonymous.demote(admin.user.id)

        assert chat.member(admin.user.id).status == ChatMemberStatus.MEMBER
        assert [update.new_chat_member.status for update in updates] == ["member"]
        world["env"].assert_updates_handled()
        with pytest.raises(WorldLookupError, match="not an anonymous administrator"):
            await anonymous.send("again")

    async def test_promoting_itself_out_of_anonymity_announces_it(self, build, dp):
        world = build()
        chat, admin, anonymous = self.self_managing(world)
        updates = []

        @dp.chat_member()
        async def collect(update: ChatMemberUpdated) -> None:
            updates.append(update)

        await anonymous.promote(admin.user.id, can_promote_members=True)

        assert chat.member(admin.user.id).rights.is_anonymous is False
        assert len(updates) == 1

    async def test_a_send_checks_the_binding_once(self, build, monkeypatch):
        world = build()
        admin = world["admin"].in_(world["chat"], anonymous=True)
        checks = []
        original = type(admin)._require_anonymous

        def counted(self, chat):
            checks.append(chat.id)
            return original(self, chat)

        monkeypatch.setattr(type(admin), "_require_anonymous", counted)

        await admin.send("hi")

        assert checks == [world["chat"].id]

    async def test_a_refused_trigger_changes_nothing(self, build):
        world = build()
        chat, alice = world["chat"], world["alice"]
        admin = world["admin"].in_(chat, anonymous=True)
        chat.member(world["admin"].user.id).rights = administrator_rights()
        before = list(chat.messages)

        with pytest.raises(WorldLookupError, match="not an anonymous administrator"):
            await admin.send("hi")
        with pytest.raises(WorldLookupError, match="not an anonymous administrator"):
            await admin.promote(alice.user, can_pin_messages=True)

        assert chat.messages == before
        assert chat.member(alice.user.id).status == ChatMemberStatus.MEMBER


class TestAWithheldUpdateIsBound:
    async def test_what_it_carries_answers_the_bot(self, build, dp):
        world = build()
        env, chat = world["env"], world["chat"]
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Buy", callback_data="buy")]],
        )
        await env.bot.send_message(chat_id=chat.id, text="Shop", reply_markup=keyboard)

        withheld = await world["alice"].click("buy", deliver=False)

        assert isinstance(withheld, Withheld)
        assert withheld.update.callback_query.bot is env.bot
        assert await withheld.update.callback_query.answer("ok") is True

    async def test_it_snapshots_the_running_tasks(self, build):
        world = build()
        env = world["env"]
        assert env._protection_extended is False

        await world["alice"].send("unseen", deliver=False)

        assert env._protection_extended is True

    async def test_a_withheld_message_from_another_bot_is_bound(self, build):
        world = build()

        withheld = await world["other"].send("plain")

        assert withheld.update.message.bot is world["env"].bot


class TestAnAnonymousVoteIsInItsOwnChat:
    async def test_a_poll_of_another_chat_is_refused(self, build):
        world = build()
        env, chat = world["env"], world["chat"]
        env.enforce_bot_rights = False
        poll = await env.bot.send_poll(
            chat_id=world["channel"].id, question="Who?", options=["A", "B"], is_anonymous=False
        )
        admin = world["admin"].in_(chat, anonymous=True)

        with pytest.raises(WorldLookupError, match=f"belongs to chat {world['channel'].id}"):
            await admin.vote(poll.poll.id, [0])
        assert env.world.poll(poll.poll.id).votes == {}

    async def test_a_poll_of_no_known_chat_is_not_held_against_it(self, build):
        world = build()
        env, chat = world["env"], world["chat"]
        env.world.polls["loose"] = PollState(
            id="loose", question="Who?", options=["A", "B"], is_anonymous=False
        )
        admin = world["admin"].in_(chat, anonymous=True)

        await admin.vote("loose", [0])

        assert env.world.poll("loose").votes == {chat.id: [0]}

    async def test_a_person_still_votes_in_any_chat(self, build):
        world = build()
        env = world["env"]
        env.enforce_bot_rights = False
        poll = await env.bot.send_poll(
            chat_id=world["channel"].id, question="Who?", options=["A", "B"], is_anonymous=False
        )

        await world["alice"].vote(poll.poll.id, [1])

        assert env.world.poll(poll.poll.id).votes == {world["alice"].user.id: [1]}

    async def test_a_copied_poll_belongs_to_the_chat_it_was_copied_to(self, build):
        world = build()
        env, chat, channel = world["env"], world["chat"], world["channel"]
        env.enforce_bot_rights = False
        poll = await env.bot.send_poll(
            chat_id=channel.id, question="Who?", options=["A", "B"], is_anonymous=False
        )

        copied = await env.bot.copy_message(
            chat_id=chat.id, from_chat_id=channel.id, message_id=poll.message_id
        )
        sent = chat.find_message(copied.message_id)

        assert env.world.poll(sent.poll.id).chat_id == chat.id
        assert env.world.poll(poll.poll.id).chat_id == channel.id
