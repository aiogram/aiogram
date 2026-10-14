import datetime

import pytest

from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from aiogram.test import Blueprint, BotTestEnvironment, WorldLookupError
from aiogram.test.modeling import LIVE_FOREVER, normalize_until, resolve_date
from aiogram.test.world import BASE_DATE, UNTIL_FOREVER
from aiogram.types import (
    ChatPermissions,
    EphemeralMessageParameters,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    PhotoSize,
)

HOUR = datetime.timedelta(hours=1)
DAY = datetime.timedelta(days=1)
MUTED = ChatPermissions(can_send_messages=False)


@pytest.fixture
def world_blueprint():
    blueprint = Blueprint()
    alice = blueprint.add_user("Alice")
    bob = blueprint.add_user("Bob")
    blueprint.add_private_chat(alice)
    blueprint.add_supergroup(
        "Team",
        members={alice: ChatMemberStatus.MEMBER, bob: ChatMemberStatus.MEMBER},
    )
    blueprint.add_business_connection(alice)
    return blueprint


@pytest.fixture
def env(world_blueprint, dp):
    environment = BotTestEnvironment(
        blueprint=world_blueprint,
        dispatcher=dp,
        clock_start=BASE_DATE,
    )
    try:
        yield environment
    finally:
        environment.dispose_sync()


@pytest.fixture
def alice(world_blueprint):
    return world_blueprint.users[0]


@pytest.fixture
def bob(world_blueprint):
    return world_blueprint.users[1]


@pytest.fixture
def private(env, world_blueprint):
    return env.chat(world_blueprint.chats[0])


@pytest.fixture
def team(env, world_blueprint):
    return env.chat(world_blueprint.chats[1])


@pytest.fixture
def connection(world_blueprint):
    return world_blueprint.business_connections[0]


class TestWhereTheClockStarts:
    async def test_by_default_at_the_real_time(self, world_blueprint, dp):
        before = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
        environment = BotTestEnvironment(blueprint=world_blueprint, dispatcher=dp)
        try:
            after = datetime.datetime.now(datetime.timezone.utc)

            assert before <= environment.now <= after
            assert environment.now.microsecond == 0
        finally:
            await environment.dispose()

    async def test_dates_a_bot_computes_from_the_real_clock_work(self, world_blueprint, dp):
        environment = BotTestEnvironment(blueprint=world_blueprint, dispatcher=dp)
        try:
            team = environment.chat(world_blueprint.chats[1])
            alice = world_blueprint.users[0]
            in_an_hour = datetime.datetime.now(datetime.timezone.utc) + HOUR

            await environment.bot.send_poll(
                chat_id=team.id,
                question="Lunch?",
                options=["Yes", "No"],
                close_date=in_an_hour,
            )
            await environment.bot.restrict_chat_member(
                chat_id=team.id,
                user_id=alice.id,
                permissions=MUTED,
                until_date=in_an_hour,
            )
            await environment.advance_time(HOUR + datetime.timedelta(seconds=1))

            (poll,) = environment.world.polls.values()
            assert poll.is_closed is True
            assert team.member(alice.id).status == ChatMemberStatus.MEMBER
        finally:
            await environment.dispose()

    async def test_a_naive_start_is_read_as_local_time(self, world_blueprint, dp):
        naive = datetime.datetime.fromtimestamp(BASE_DATE.timestamp())
        environment = BotTestEnvironment(
            blueprint=world_blueprint,
            dispatcher=dp,
            clock_start=naive,
        )
        try:
            assert environment.now == BASE_DATE
        finally:
            await environment.dispose()


class TestTheClock:
    async def test_time_does_not_move_on_its_own(self, env, private, alice):
        actor = env.user(alice)
        for text in ("one", "two", "three"):
            await actor.send(text)

        assert {message.date for message in private.messages} == {BASE_DATE}
        assert env.now == BASE_DATE

    async def test_advancing_moves_later_dates(self, env, private, alice):
        actor = env.user(alice)
        await actor.send("before")

        await env.advance_time(HOUR)
        await actor.send("after")
        await env.advance_time(30)
        await actor.send("later")

        before, after, later = (m.date for m in private.messages)
        assert after - before == HOUR
        assert later - after == datetime.timedelta(seconds=30)

    async def test_an_advance_that_feeds_nothing_keeps_the_last_route(self, env, alice):
        async def on_text(message):
            pass

        env.dispatcher.message.register(on_text)
        await env.user(alice).send("hello")

        await env.advance_time(HOUR)

        env.assert_handled_by("on_text")

    async def test_time_cannot_go_backwards(self, env):
        with pytest.raises(ValueError, match="backwards"):
            await env.advance_time(-1)

        assert env.now == BASE_DATE

    async def test_events_run_in_order_each_at_its_moment(self, env):
        seen = []

        def at(label):
            async def action():
                seen.append((label, env.now - BASE_DATE))

            return action

        env.schedule(BASE_DATE + datetime.timedelta(seconds=20), at("late"))
        env.schedule(BASE_DATE + datetime.timedelta(seconds=10), at("first"))
        env.schedule(BASE_DATE + datetime.timedelta(seconds=10), at("second"))
        env.schedule(BASE_DATE + datetime.timedelta(seconds=99), at("not yet"))

        await env.advance_time(30)

        ten = datetime.timedelta(seconds=10)
        assert seen == [("first", ten), ("second", ten), ("late", ten * 2)]
        assert env.now == BASE_DATE + datetime.timedelta(seconds=30)

    async def test_a_naive_moment_is_read_as_local_time(self, env):
        seen = []

        async def action():
            seen.append(env.now)

        moment = BASE_DATE + datetime.timedelta(seconds=10)
        env.schedule(moment.astimezone().replace(tzinfo=None), action)

        await env.advance_time(30)

        assert seen == [moment]

    async def test_an_event_scheduled_during_an_advance_fires_within_it(self, env):
        seen = []

        async def follow_up():
            seen.append(env.now)

        async def first():
            env.schedule(env.now + datetime.timedelta(seconds=5), follow_up)

        env.schedule(BASE_DATE + datetime.timedelta(seconds=5), first)

        await env.advance_time(60)

        assert seen == [BASE_DATE + datetime.timedelta(seconds=10)]

    async def test_a_raising_event_stops_the_clock_at_its_moment(self, env):
        seen = []

        async def boom():
            raise RuntimeError("boom")

        async def later():
            seen.append("later")

        env.schedule(BASE_DATE + datetime.timedelta(seconds=5), boom)
        env.schedule(BASE_DATE + datetime.timedelta(seconds=10), later)

        with pytest.raises(RuntimeError, match="boom"):
            await env.advance_time(60)
        assert env.now == BASE_DATE + datetime.timedelta(seconds=5)

        await env.advance_time(60)
        assert seen == ["later"]

    async def test_an_advance_cannot_overlap_itself(self, env):
        refused = []

        async def reentrant():
            try:
                await env.advance_time(1)
            except RuntimeError as error:
                refused.append(str(error))

        env.schedule(BASE_DATE + datetime.timedelta(seconds=5), reentrant)

        await env.advance_time(10)

        assert refused and "already running" in refused[0]
        assert env.now == BASE_DATE + datetime.timedelta(seconds=10)

    async def test_a_forward_keeps_its_origin_date(self, env, private, team, alice):
        await env.user(alice).send("original")
        original = private.messages[-1]
        await env.advance_time(HOUR)

        await env.bot.forward_message(
            chat_id=team.id,
            from_chat_id=private.id,
            message_id=original.message_id,
        )

        forwarded = team.messages[-1]
        assert forwarded.forward_origin.date == original.date
        assert forwarded.date == original.date + HOUR


class TestDateHelpers:
    def test_resolve_date_reads_every_form(self):
        aware = BASE_DATE + HOUR
        naive = datetime.datetime.fromtimestamp(aware.timestamp())

        assert resolve_date(aware, BASE_DATE) == aware
        assert resolve_date(naive, BASE_DATE) == aware
        assert resolve_date(HOUR, BASE_DATE) == aware
        assert resolve_date(int(aware.timestamp()), BASE_DATE) == aware
        assert resolve_date(None, BASE_DATE) is None

    @pytest.mark.parametrize(
        ("value", "forever"),
        [
            (datetime.timedelta(seconds=10), True),
            (datetime.timedelta(seconds=30), False),
            (datetime.timedelta(days=366), False),
            (datetime.timedelta(days=400), True),
            (0, True),
            (None, True),
        ],
    )
    def test_normalize_until_applies_the_forever_rule(self, value, forever):
        assert (normalize_until(value, BASE_DATE) is None) is forever


class TestRestrictionsExpire:
    async def read(self, env, chat, user):
        return await env.bot.get_chat_member(chat_id=chat.id, user_id=user.id)

    async def test_a_mute_lifts_on_time(self, env, team, alice):
        await env.bot.restrict_chat_member(
            chat_id=team.id,
            user_id=alice.id,
            permissions=MUTED,
            until_date=HOUR,
        )
        assert (await self.read(env, team, alice)).status == ChatMemberStatus.RESTRICTED

        await env.advance_time(HOUR)

        member = await self.read(env, team, alice)
        assert member.status == ChatMemberStatus.MEMBER
        assert member.until_date is None
        assert team.member(alice.id).permissions is None

    async def test_a_naive_end_date_is_read_as_local_time(self, env, team, alice):
        member = team.member(alice.id)
        ends = env.now + datetime.timedelta(hours=1)
        member.set_status(ChatMemberStatus.RESTRICTED)
        member.until_date = ends.astimezone().replace(tzinfo=None)

        assert team.member(alice.id).status == ChatMemberStatus.RESTRICTED

        await env.advance_time(HOUR)

        assert team.member(alice.id).status == ChatMemberStatus.MEMBER

    async def test_the_member_map_reads_the_lifted_mute(self, env, team, alice):
        await env.bot.restrict_chat_member(
            chat_id=team.id,
            user_id=alice.id,
            permissions=MUTED,
            until_date=HOUR,
        )
        held = team.member(alice.id)

        await env.advance_time(HOUR)

        assert team.members[alice.id].status == ChatMemberStatus.MEMBER
        assert held.status == ChatMemberStatus.MEMBER

    async def test_a_mute_on_an_absent_user_ends_as_left(self, env, team, world_blueprint):
        stranger = world_blueprint.users[0]
        await env.user(stranger).in_(team).leave()
        await env.bot.restrict_chat_member(
            chat_id=team.id,
            user_id=stranger.id,
            permissions=MUTED,
            until_date=HOUR,
        )

        await env.advance_time(HOUR)

        assert (await self.read(env, team, stranger)).status == ChatMemberStatus.LEFT

    async def test_a_ban_lifts_on_time(self, env, team, alice):
        await env.bot.ban_chat_member(chat_id=team.id, user_id=alice.id, until_date=DAY)

        await env.advance_time(DAY - datetime.timedelta(seconds=1))
        assert (await self.read(env, team, alice)).status == ChatMemberStatus.KICKED
        await env.advance_time(1)

        assert (await self.read(env, team, alice)).status == ChatMemberStatus.LEFT
        assert await env.bot.get_chat_member_count(chat_id=team.id) == 2

    @pytest.mark.parametrize(
        "until",
        [datetime.timedelta(seconds=10), datetime.timedelta(days=400)],
        ids=["too short", "too long"],
    )
    async def test_out_of_range_means_forever(self, env, team, alice, until):
        await env.bot.restrict_chat_member(
            chat_id=team.id,
            user_id=alice.id,
            permissions=MUTED,
            until_date=until,
        )

        await env.advance_time(datetime.timedelta(days=500))

        member = await self.read(env, team, alice)
        assert member.status == ChatMemberStatus.RESTRICTED
        assert member.until_date == UNTIL_FOREVER

    async def test_a_duration_counts_from_now(self, env, team, alice):
        await env.advance_time(DAY)

        await env.bot.restrict_chat_member(
            chat_id=team.id,
            user_id=alice.id,
            permissions=MUTED,
            until_date=HOUR,
        )

        assert team.member(alice.id).until_date == BASE_DATE + DAY + HOUR

    async def test_an_invite_link_date_is_never_forever(self, env, team):
        link = await env.bot.create_chat_invite_link(
            chat_id=team.id,
            expire_date=datetime.timedelta(days=400),
        )

        assert link.expire_date == BASE_DATE + datetime.timedelta(days=400)


class TestScheduledPolls:
    async def send(self, env, chat, **schedule):
        return await env.bot.send_poll(
            chat_id=chat.id,
            question="Tabs or spaces?",
            options=["Tabs", "Spaces"],
            is_anonymous=False,
            **schedule,
        )

    async def test_a_poll_closes_when_its_period_ends(self, env, team):
        updates = []
        env.dispatcher.poll.register(updates.append)
        sent = await self.send(env, team, open_period=60)

        await env.advance_time(59)
        assert updates == []
        await env.advance_time(1)

        (update,) = updates
        assert update.is_closed is True
        assert env.world.polls[sent.poll.id].is_closed is True
        assert team.find_message(sent.message_id).poll.is_closed is True

    async def test_voting_works_before_and_is_refused_after(self, env, team, alice):
        sent = await self.send(env, team, open_period=60)
        actor = env.user(alice).in_(team)

        await actor.vote(sent.poll.id, [0])
        await env.advance_time(60)

        with pytest.raises(WorldLookupError, match="closed"):
            await actor.vote(sent.poll.id, [1])

    async def test_a_stopped_poll_does_not_close_twice(self, env, team):
        updates = []
        env.dispatcher.poll.register(updates.append)
        sent = await self.send(env, team, open_period=60)
        await env.bot.stop_poll(chat_id=team.id, message_id=sent.message_id)

        await env.advance_time(60)

        assert updates == []

    async def test_a_stale_close_keeps_the_last_route(self, env, team, alice):
        async def on_text(message):
            pass

        env.dispatcher.message.register(on_text)
        sent = await self.send(env, team, open_period=60)
        await env.bot.stop_poll(chat_id=team.id, message_id=sent.message_id)
        await env.user(alice).in_(team).send("hello")

        await env.advance_time(60)

        env.assert_handled_by("on_text")

    async def test_a_deleted_poll_message_does_not_close(self, env, team):
        updates = []
        env.dispatcher.poll.register(updates.append)
        sent = await self.send(env, team, open_period=60)
        await env.bot.delete_message(chat_id=team.id, message_id=sent.message_id)

        await env.advance_time(60)

        assert updates == []
        # The poll itself still closes on schedule, so no vote counts after it.
        assert env.world.polls[sent.poll.id].is_closed is True

    async def test_a_close_date_works_and_is_reported(self, env, team):
        sent = await self.send(env, team, close_date=BASE_DATE + datetime.timedelta(minutes=5))

        assert sent.poll.close_date == BASE_DATE + datetime.timedelta(minutes=5)
        await env.advance_time(datetime.timedelta(minutes=5))
        assert env.world.polls[sent.poll.id].is_closed is True

    async def test_an_open_period_is_reported(self, env, team):
        sent = await self.send(env, team, open_period=60)

        assert sent.poll.open_period == 60
        assert sent.poll.close_date == BASE_DATE + datetime.timedelta(seconds=60)

    @pytest.mark.parametrize(
        "schedule",
        [
            {"close_date": BASE_DATE + datetime.timedelta(seconds=2)},
            {"open_period": 3},
            {"open_period": 2628001},
            {"open_period": 60, "close_date": BASE_DATE + HOUR},
        ],
        ids=["close date too soon", "period too short", "period too long", "both"],
    )
    async def test_an_invalid_schedule_is_rejected(self, env, team, schedule):
        with pytest.raises(TelegramBadRequest):
            await self.send(env, team, **schedule)

        assert env.world.polls == {}
        assert [m for m in team.messages if m.poll is not None] == []


class TestLiveLocations:
    async def send(self, env, chat, live_period=600):
        return await env.bot.send_location(
            chat_id=chat.id,
            latitude=1.0,
            longitude=2.0,
            live_period=live_period,
        )

    async def edit(self, env, chat, sent, **kwargs):
        return await env.bot.edit_message_live_location(
            chat_id=chat.id,
            message_id=sent.message_id,
            latitude=3.0,
            longitude=4.0,
            **kwargs,
        )

    async def test_editing_within_the_period(self, env, private):
        sent = await self.send(env, private)
        await env.advance_time(300)

        edited = await self.edit(env, private, sent)

        assert edited.location.latitude == 3.0

    async def test_editing_after_the_period_fails(self, env, private):
        sent = await self.send(env, private)
        await env.advance_time(600)

        with pytest.raises(TelegramBadRequest, match="can't be edited"):
            await self.edit(env, private, sent)

        assert private.find_message(sent.message_id).location.latitude == 1.0

    async def test_editing_a_stopped_location_fails(self, env, private):
        sent = await self.send(env, private)
        await env.bot.stop_message_live_location(chat_id=private.id, message_id=sent.message_id)

        with pytest.raises(TelegramBadRequest, match="can't be edited"):
            await self.edit(env, private, sent)

    async def test_editing_a_static_location_fails(self, env, private):
        sent = await self.send(env, private, live_period=None)

        with pytest.raises(TelegramBadRequest, match="can't be edited"):
            await self.edit(env, private, sent)

    async def test_stopping_an_expired_or_stopped_location_fails(self, env, private):
        expired = await self.send(env, private)
        stopped = await self.send(env, private, live_period=LIVE_FOREVER)
        await env.bot.stop_message_live_location(chat_id=private.id, message_id=stopped.message_id)
        await env.advance_time(600)

        for sent in (expired, stopped):
            with pytest.raises(TelegramBadRequest, match="can't be edited"):
                await env.bot.stop_message_live_location(
                    chat_id=private.id,
                    message_id=sent.message_id,
                )

    async def test_a_forever_location_never_expires(self, env, private):
        sent = await self.send(env, private, live_period=LIVE_FOREVER)
        await env.advance_time(datetime.timedelta(days=365))

        edited = await self.edit(env, private, sent)

        assert edited.location.live_period == LIVE_FOREVER

    async def test_extending_by_more_than_a_day_is_refused_forever_is_not(self, env, private):
        sent = await self.send(env, private, live_period=3600)

        with pytest.raises(TelegramBadRequest, match="more than a day"):
            await self.edit(env, private, sent, live_period=3600 + 2 * 86400)
        extended = await self.edit(env, private, sent, live_period=3600 + 86400)
        assert extended.location.live_period == 3600 + 86400
        forever = await self.edit(env, private, sent, live_period=LIVE_FOREVER)
        assert forever.location.live_period == LIVE_FOREVER

    async def test_ending_beyond_ninety_days_is_refused(self, env, private):
        sent = await self.send(env, private, live_period=LIVE_FOREVER)

        with pytest.raises(TelegramBadRequest, match="90 days"):
            await self.edit(env, private, sent, live_period=100 * 86400)


class TestMessageAgeLimits:
    async def test_a_fresh_message_can_be_deleted(self, env, private):
        sent = await env.bot.send_message(chat_id=private.id, text="x")
        await env.advance_time(HOUR)

        assert await env.bot.delete_message(chat_id=private.id, message_id=sent.message_id)

    async def test_a_two_day_old_message_cannot_be_deleted(self, env, private):
        sent = await env.bot.send_message(chat_id=private.id, text="x")
        await env.advance_time(datetime.timedelta(hours=48))

        with pytest.raises(TelegramBadRequest, match="can't be deleted"):
            await env.bot.delete_message(chat_id=private.id, message_id=sent.message_id)

        assert private.find_message(sent.message_id) is not None

    async def test_a_fresh_dice_in_a_private_chat_cannot_be_deleted(self, env, private):
        sent = await env.bot.send_dice(chat_id=private.id)

        with pytest.raises(TelegramBadRequest, match="can't be deleted"):
            await env.bot.delete_message(chat_id=private.id, message_id=sent.message_id)
        await env.advance_time(datetime.timedelta(hours=24))
        with pytest.raises(TelegramBadRequest, match="can't be deleted"):
            await env.bot.delete_message(chat_id=private.id, message_id=sent.message_id)
        await env.advance_time(1)

        assert await env.bot.delete_message(chat_id=private.id, message_id=sent.message_id)

    async def test_a_naive_date_is_measured_against_the_clock(self, env, team, alice):
        naive = (BASE_DATE - datetime.timedelta(hours=72)).astimezone().replace(tzinfo=None)
        await env.user(alice).in_(team).send("old", fields={"date": naive})
        sent = team.messages[-1]

        with pytest.raises(TelegramBadRequest, match="can't be deleted"):
            await env.bot.delete_message(chat_id=team.id, message_id=sent.message_id)

    async def test_a_dice_in_a_group_can_be_deleted_at_once(self, env, team):
        sent = await env.bot.send_dice(chat_id=team.id)

        assert await env.bot.delete_message(chat_id=team.id, message_id=sent.message_id)

    async def test_batch_deletion_skips_messages_too_old(self, env, private):
        old = await env.bot.send_message(chat_id=private.id, text="old")
        await env.advance_time(datetime.timedelta(hours=48))
        fresh = await env.bot.send_message(chat_id=private.id, text="fresh")

        assert await env.bot.delete_messages(
            chat_id=private.id,
            message_ids=[old.message_id, fresh.message_id],
        )

        assert private.find_message(old.message_id) is not None
        assert private.find_message(fresh.message_id) is None


class TestBusinessEditWindow:
    async def owner_message(
        self,
        env,
        alice,
        private,
        connection,
        keyboard=False,
        captioned=False,
    ):
        fields = {}
        if keyboard:
            fields["reply_markup"] = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="K", callback_data="k")]],
            )
        text = "mine"
        if captioned:
            # A caption edit needs media to sit on.
            text = None
            fields["photo"] = [PhotoSize(file_id="p", file_unique_id="p", width=1, height=1)]
            fields["caption"] = "mine"
        await env.user(alice).in_(private, business=connection).send(text, fields=fields)
        return private.messages[-1]

    @pytest.mark.parametrize(
        ("edit", "captioned"),
        [
            (lambda bot, target: bot.edit_message_text(text="new", **target), False),
            (lambda bot, target: bot.edit_message_caption(caption="new", **target), True),
            (
                lambda bot, target: bot.edit_message_media(
                    media=InputMediaPhoto(media="id"),
                    **target,
                ),
                False,
            ),
            (lambda bot, target: bot.edit_message_reply_markup(**target), False),
        ],
        ids=["text", "caption", "media", "markup"],
    )
    async def test_an_old_owner_message_cannot_be_edited(
        self,
        env,
        alice,
        private,
        connection,
        edit,
        captioned,
    ):
        message = await self.owner_message(env, alice, private, connection, captioned=captioned)
        target = {
            "business_connection_id": connection.id,
            "chat_id": private.id,
            "message_id": message.message_id,
        }
        await env.advance_time(datetime.timedelta(hours=48))
        await edit(env.bot, target)
        await env.advance_time(1)

        with pytest.raises(TelegramBadRequest, match="can't be edited"):
            await edit(env.bot, target)

    async def test_a_message_with_a_keyboard_stays_editable(
        self,
        env,
        alice,
        private,
        connection,
    ):
        message = await self.owner_message(env, alice, private, connection, keyboard=True)
        await env.advance_time(datetime.timedelta(days=3))

        await env.bot.edit_message_text(
            business_connection_id=connection.id,
            chat_id=private.id,
            message_id=message.message_id,
            text="new",
        )

    async def test_a_bot_sent_business_message_stays_editable(self, env, private, connection):
        sent = await env.bot.send_message(
            business_connection_id=connection.id,
            chat_id=private.id,
            text="from the bot",
        )
        await env.advance_time(datetime.timedelta(days=3))

        await env.bot.edit_message_text(
            business_connection_id=connection.id,
            chat_id=private.id,
            message_id=sent.message_id,
            text="new",
        )


class TestAnswerWindows:
    async def test_a_prompt_pre_checkout_answer_succeeds(self, env, alice):
        queries = []
        env.dispatcher.pre_checkout_query.register(queries.append)
        await env.user(alice).pre_checkout_query()

        assert await env.bot.answer_pre_checkout_query(
            pre_checkout_query_id=queries[0].id,
            ok=True,
        )

    async def test_a_late_pre_checkout_answer_fails(self, env, alice):
        queries = []
        env.dispatcher.pre_checkout_query.register(queries.append)
        await env.user(alice).pre_checkout_query()
        await env.advance_time(11)

        with pytest.raises(TelegramBadRequest, match="query is too old"):
            await env.bot.answer_pre_checkout_query(
                pre_checkout_query_id=queries[0].id,
                ok=True,
            )

    async def test_a_callback_query_does_not_expire(self, env, private, alice):
        queries = []
        env.dispatcher.callback_query.register(queries.append)
        await env.bot.send_message(
            chat_id=private.id,
            text="x",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Go", callback_data="go")]],
            ),
        )
        await env.user(alice).click("go")
        await env.advance_time(HOUR)

        assert await env.bot.answer_callback_query(callback_query_id=queries[0].id)

    async def ephemeral_command(self, env, team, alice):
        await env.user(alice).in_(team).send("/secret", ephemeral=True)
        (command,) = team.ephemeral_commands(alice)
        return command

    async def reply(self, env, team, alice, command):
        return await env.bot.send_message(
            chat_id=team.id,
            text="only you",
            reply_parameters={"ephemeral_message_id": command.ephemeral_message_id},
            ephemeral_message_parameters=EphemeralMessageParameters(receiver_user_id=alice.id),
        )

    async def test_a_prompt_ephemeral_reply_succeeds(self, env, team, alice):
        command = await self.ephemeral_command(env, team, alice)
        await env.advance_time(15)

        reply = await self.reply(env, team, alice, command)

        assert team.ephemeral_messages(alice) == [reply]

    async def test_a_late_ephemeral_reply_fails(self, env, team, alice):
        command = await self.ephemeral_command(env, team, alice)
        await env.advance_time(16)

        with pytest.raises(TelegramBadRequest, match="15 seconds"):
            await self.reply(env, team, alice, command)

        assert team.ephemeral_messages(alice) == []
