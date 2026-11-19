import pytest

from aiogram import F
from aiogram.enums import ChatMemberStatus, MessageEntityType
from aiogram.test import Blueprint, BotTestEnvironment
from aiogram.test.markup import bot_command_entities
from aiogram.types import Message, MessageEntity

LONG_COMMAND = "a" * 64
LONG_USERNAME = "b" * 32


def spans(text):
    return [(entity.offset, entity.length) for entity in bot_command_entities(text)]


class TestWhereACommandIs:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("/start", [(0, 6)]),
            ("/start@my_bot", [(0, 13)]),
            ("/start@abc", [(0, 10)]),
            ("/start@bot-name", [(0, 10)]),
            ("hello /start", [(6, 6)]),
            ("hello\n/start", [(6, 6)]),
            ("hello\t/start now", [(6, 6)]),
            ("/a /b", [(0, 2), (3, 2)]),
            ("/a@bot_1 text /b_2", [(0, 8), (14, 4)]),
            ("(/start)", [(1, 6)]),
            ('"/start"', [(1, 6)]),
            ("go: /start.", [(4, 6)]),
            ("/start?arg", [(0, 6)]),
            ("/Start_1", [(0, 8)]),
            ("/" + LONG_COMMAND, [(0, 65)]),
            ("/start@" + LONG_USERNAME, [(0, 39)]),
            # An emoji takes two UTF-16 units, and does not hold
            # a command back.
            ("😀 /start", [(3, 6)]),
            ("😀/start", [(2, 6)]),
            ("é /start 😀 /go", [(2, 6), (12, 3)]),
        ],
    )
    def test_commands_are_found(self, text, expected):
        assert spans(text) == expected

    @pytest.mark.parametrize(
        "text",
        [
            "",
            "/",
            "hello",
            "a/start",
            "1/start",
            "_/start",
            "é/start",
            "//start",
            "<b>/start",
            "</start",
            ">/start",
            "/start>",
            "/start<",
            "/start/more",
            "/start_é",
            "/startй",
            "/привет",
            "/ start",
            "/@bot",
            "/start@",
            "/start@ab",
            "/start@" + "b" * 33,
            "/" + "a" * 65,
            "http://example.com/start",
        ],
    )
    def test_everything_else_is_not(self, text):
        assert spans(text) == []

    def test_a_broken_name_drops_the_command_before_it_only(self):
        assert spans("/a@ab /b") == [(6, 2)]

    def test_nothing_is_found_in_none(self):
        assert bot_command_entities(None) == []

    def test_the_entities_are_bot_commands(self):
        entity = bot_command_entities("/start")[0]

        assert entity.type == MessageEntityType.BOT_COMMAND
        assert entity.url is None and entity.user is None


@pytest.fixture
def world(dp):
    blueprint = Blueprint()
    alice = blueprint.add_user("Alice")
    team = blueprint.add_supergroup("Team", members={alice: ChatMemberStatus.MEMBER})
    news = blueprint.add_channel("News", members={alice: ChatMemberStatus.ADMINISTRATOR})
    blueprint.add_private_chat(alice)
    blueprint.add_business_connection(alice)
    env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
    try:
        yield env, env.user(alice), team, news
    finally:
        env.dispose_sync()


@pytest.fixture
def seen(dp):
    messages: list[Message] = []

    @dp.message()
    @dp.channel_post()
    @dp.edited_message()
    @dp.business_message()
    async def collect(message: Message) -> None:
        messages.append(message)

    return messages


class TestWhatAnActorSends:
    async def test_a_command_carries_its_entity(self, world, seen):
        _env, alice, _team, _news = world

        await alice.send("/start")

        assert [(e.type, e.offset, e.length) for e in seen[0].entities] == [
            (MessageEntityType.BOT_COMMAND, 0, 6),
        ]
        assert alice.chat.messages[-1].entities[0].type == MessageEntityType.BOT_COMMAND

    async def test_a_router_keying_on_entities_matches(self, world, dp):
        _env, alice, _team, _news = world
        hits = []

        @dp.message(F.entities[0].type == MessageEntityType.BOT_COMMAND)
        async def on_command(message: Message) -> None:
            hits.append(message.text)

        await alice.send("/help me")
        await alice.send("plain text")

        assert hits == ["/help me"]

    async def test_a_text_without_one_has_none(self, world, seen):
        _env, alice, _team, _news = world

        await alice.send("hello")

        assert seen[0].entities is None

    async def test_explicit_entities_are_never_overridden(self, world, seen):
        _env, alice, _team, _news = world
        bold = MessageEntity(type=MessageEntityType.BOLD, offset=0, length=3)

        await alice.send("/go", fields={"entities": [bold]})
        await alice.send("/go", fields={"entities": []})

        assert [e.type for e in seen[0].entities] == [MessageEntityType.BOLD]
        assert seen[1].entities == []

    async def test_a_caption_gets_them_too(self, world, seen):
        _env, alice, _team, _news = world

        await alice.send(fields={"caption": "see /start"})
        await alice.send(
            fields={"caption": "/start", "caption_entities": []},
        )

        assert [(e.offset, e.length) for e in seen[0].caption_entities] == [(4, 6)]
        assert seen[0].entities is None
        assert seen[1].caption_entities == []

    async def test_a_text_given_in_the_fields_is_read(self, world, seen):
        _env, alice, _team, _news = world

        await alice.send(fields={"text": "/start"})

        assert seen[0].entities[0].length == 6

    async def test_a_group_a_channel_and_a_business_chat_too(self, world, seen):
        env, alice, team, news = world

        await alice.in_(team).send("/start@bot")
        await alice.in_(news).send("/post")
        connection = next(iter(env.world.business_connections))
        await alice.in_(env.chat(alice.user.id), business=connection).send("/biz")

        assert [m.entities[0].length for m in seen] == [10, 5, 4]

    async def test_a_reply_and_an_ephemeral_command_get_them(self, world, seen):
        _env, alice, team, _news = world
        member = alice.in_(team)

        await member.send("question")
        await member.reply(member.chat.messages[-1], "/answer")
        await member.send("/mine", ephemeral=True)

        assert seen[1].entities[0].length == 7
        assert seen[2].entities[0].length == 5

    async def test_the_bots_own_messages_are_untouched(self, world):
        env, _alice, team, _news = world
        env.world.chat(team.id).member(
            env.world.bot_user.id
        ).status = ChatMemberStatus.ADMINISTRATOR

        sent = await env.bot.send_message(chat_id=team.id, text="/start")

        assert sent.entities is None


class TestEdits:
    async def test_the_new_text_is_marked_afresh(self, world, seen):
        _env, alice, _team, _news = world
        await alice.send("/old")
        sent = alice.chat.messages[-1]

        await alice.edit(sent, "now /new")

        assert [(e.offset, e.length) for e in seen[-1].entities] == [(4, 4)]

    async def test_text_without_a_command_clears_the_old_entity(self, world, seen):
        _env, alice, _team, _news = world
        await alice.send("/old")
        sent = alice.chat.messages[-1]

        await alice.edit(sent, "plain")

        assert seen[-1].entities is None

    async def test_explicit_entities_win_in_an_edit(self, world, seen):
        _env, alice, _team, _news = world
        await alice.send("/old")
        sent = alice.chat.messages[-1]

        await alice.edit(sent, "/new", fields={"entities": []})

        assert seen[-1].entities == []

    async def test_an_edit_that_leaves_the_text_leaves_the_entities(self, world, seen):
        _env, alice, _team, _news = world
        await alice.send("/old")
        sent = alice.chat.messages[-1]

        await alice.edit(sent, fields={"caption": "x"})

        assert [e.length for e in seen[-1].entities] == [4]


def test_offsets_run_on_across_a_long_text():
    """Each command is measured from the last, in UTF-16 units."""
    text = " ".join(["😀 /go"] * 200)

    found = spans(text)

    assert len(found) == 200
    assert found[0] == (3, 3)
    assert found[-1] == (199 * 7 + 3, 3)
