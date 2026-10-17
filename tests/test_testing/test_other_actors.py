"""Actors that are another bot, or an anonymous administrator."""

import pytest

from aiogram import F
from aiogram.enums import ChatMemberStatus
from aiogram.fsm.state import State
from aiogram.test import (
    Blueprint,
    BotTestEnvironment,
    Withheld,
    WorldLookupError,
    administrator_rights,
)
from aiogram.types import ChatMemberUpdated, Message

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

    async def test_a_service_message_carries_the_same_sender(self, build, seen):
        world = build()
        admin = world["admin"].in_(world["chat"], anonymous=True)

        await admin.close_topic(world["topic"])
        await admin.hide_general_topic()

        for message in seen:
            assert message.from_user.username == "GroupAnonymousBot"
            assert message.sender_chat.id == world["chat"].id
            assert message.author_signature == "Host"
        assert seen[0].forum_topic_closed is not None
        assert seen[1].general_forum_topic_hidden is not None

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

    async def test_a_topic_opened_anonymously_is_the_groups(self, build, seen):
        world = build()
        member = world["chat"].member(world["admin"].user.id)
        member.rights = administrator_rights(is_anonymous=True, can_manage_topics=False)
        admin = world["admin"].in_(world["chat"], anonymous=True)

        topic = await admin.create_topic("Mafia")

        assert topic.creator_id == world["chat"].id
        root = topic.root_message
        assert (root.sender_chat.id, root.author_signature) == (world["chat"].id, "Host")
        # Its creator closes it without the right.
        await admin.close_topic(topic)
        assert topic.is_closed
        # The same user, posting as themselves, is not its creator.
        with pytest.raises(WorldLookupError, match="can_manage_topics"):
            await world["admin"].in_(world["chat"]).reopen_topic(topic)

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
