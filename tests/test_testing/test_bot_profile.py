from typing import get_args

import pytest

from aiogram import Dispatcher
from aiogram.test import Blueprint, BotTestEnvironment, WorldLookupError
from aiogram.test.world import scope_key
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllGroupChats,
    BotCommandScopeChat,
    BotCommandScopeChatMember,
    BotCommandScopeDefault,
    BotCommandScopeUnion,
    ChatAdministratorRights,
    MenuButtonCommands,
    MenuButtonDefault,
    WebAppInfo,
)
from aiogram.types.menu_button_web_app import MenuButtonWebApp

START = BotCommand(command="start", description="Start")
HELP = BotCommand(command="help", description="Help")


def declared(commands):
    """
    Identify commands by what they say, not by object equality.

    A result is mounted to the bot that asked for it, and pydantic counts that binding in
    ``__eq__`` while hiding it from ``__repr__`` — so a returned command never compares
    equal to a plainly declared constant, here or against real Telegram. What the world
    *stores* is unbound and does compare equal; that invariant has its own test below.
    """
    return [(command.command, command.description) for command in commands]


def scope_members():
    """Flatten the annotated discriminated union down to its member models."""
    members = []
    pending = [BotCommandScopeUnion]
    while pending:
        current = pending.pop()
        if isinstance(current, type):
            members.append(current)
        else:
            pending.extend(get_args(current))
    assert members, "the guard would silently skip if the union stopped flattening"
    return sorted(members, key=lambda item: item.__name__)


class TestScopeKeys:
    @pytest.mark.parametrize("member", scope_members(), ids=lambda item: item.__name__)
    def test_every_scope_member_produces_a_key(self, member):
        """Guard for design decision D5: keys come from the member's own fields."""
        required = {name: 1 for name, field in member.model_fields.items() if field.is_required()}

        assert scope_key(member(**required), None)

    def test_an_omitted_scope_matches_an_explicit_default(self):
        assert scope_key(None, None) == scope_key(BotCommandScopeDefault(), "")

    def test_scopes_differing_only_by_an_extra_field_do_not_collide(self):
        chat = scope_key(BotCommandScopeChat(chat_id=5), None)
        member = scope_key(BotCommandScopeChatMember(chat_id=5, user_id=7), None)

        assert chat != member

    def test_language_is_part_of_the_key(self):
        assert scope_key(None, "de") != scope_key(None, "fr")


class TestCommands:
    async def test_commands_round_trip_for_the_default_scope(self, env):
        await env.bot.set_my_commands(commands=[START, HELP])

        assert declared(await env.bot.get_my_commands()) == declared([START, HELP])

    async def test_commands_are_keyed_by_scope(self, env, private):
        await env.bot.set_my_commands(commands=[START])
        await env.bot.set_my_commands(
            commands=[HELP],
            scope=BotCommandScopeChat(chat_id=private.id),
        )

        assert declared(await env.bot.get_my_commands()) == declared([START])
        assert declared(
            await env.bot.get_my_commands(scope=BotCommandScopeChat(chat_id=private.id)),
        ) == declared([HELP])

    async def test_commands_do_not_fall_back_to_a_broader_scope(self, env, private):
        """The Bot API returns what was set for that exact key, or nothing."""
        await env.bot.set_my_commands(commands=[START])

        assert await env.bot.get_my_commands(scope=BotCommandScopeAllGroupChats()) == []

    async def test_commands_do_not_fall_back_across_languages(self, env):
        await env.bot.set_my_commands(commands=[START], language_code="de")

        assert await env.bot.get_my_commands(language_code="fr") == []
        assert declared(await env.bot.get_my_commands(language_code="de")) == declared([START])

    async def test_unset_commands_are_an_empty_list(self, env):
        assert await env.bot.get_my_commands() == []

    async def test_deleting_empties_only_that_key(self, env, private):
        await env.bot.set_my_commands(commands=[START])
        await env.bot.set_my_commands(
            commands=[HELP],
            scope=BotCommandScopeChat(chat_id=private.id),
        )

        await env.bot.delete_my_commands(scope=BotCommandScopeChat(chat_id=private.id))

        assert declared(await env.bot.get_my_commands()) == declared([START])
        assert (
            await env.bot.get_my_commands(
                scope=BotCommandScopeChat(chat_id=private.id),
            )
            == []
        )

    async def test_setting_replaces_rather_than_appends(self, env):
        await env.bot.set_my_commands(commands=[START])
        await env.bot.set_my_commands(commands=[HELP])

        assert declared(await env.bot.get_my_commands()) == declared([HELP])


class TestLocalizedTexts:
    async def test_name_round_trips(self, env):
        await env.bot.set_my_name(name="Helper")

        assert (await env.bot.get_my_name()).name == "Helper"

    async def test_an_unset_name_falls_back_to_the_bots_own(self, env, blueprint):
        assert (await env.bot.get_my_name()).name == blueprint.bot.first_name

    async def test_description_and_short_description_round_trip(self, env):
        await env.bot.set_my_description(description="Long")
        await env.bot.set_my_short_description(short_description="Short")

        assert (await env.bot.get_my_description()).description == "Long"
        assert (await env.bot.get_my_short_description()).short_description == "Short"

    async def test_unset_descriptions_are_empty_strings(self, env):
        assert (await env.bot.get_my_description()).description == ""
        assert (await env.bot.get_my_short_description()).short_description == ""

    async def test_a_localized_text_falls_back_to_the_default_language(self, env):
        await env.bot.set_my_description(description="For everyone")

        assert (await env.bot.get_my_description(language_code="de")).description == "For everyone"

    async def test_a_dedicated_language_wins_over_the_default(self, env):
        await env.bot.set_my_description(description="For everyone")
        await env.bot.set_my_description(description="Auf Deutsch", language_code="de")

        assert (await env.bot.get_my_description(language_code="de")).description == "Auf Deutsch"
        assert (await env.bot.get_my_description()).description == "For everyone"

    async def test_clearing_a_localized_text_restores_the_fallback(self, env):
        await env.bot.set_my_description(description="For everyone")
        await env.bot.set_my_description(description="Auf Deutsch", language_code="de")

        await env.bot.set_my_description(description="", language_code="de")

        assert (await env.bot.get_my_description(language_code="de")).description == "For everyone"

    async def test_clearing_a_name_falls_back_to_the_bots_own(self, env, blueprint):
        await env.bot.set_my_name(name="Helper")

        await env.bot.set_my_name(name="")

        assert (await env.bot.get_my_name()).name == blueprint.bot.first_name


class TestDefaultAdministratorRights:
    async def test_rights_round_trip_per_scope(self, env):
        rights = ChatAdministratorRights(
            **{
                **dict.fromkeys(ChatAdministratorRights.model_fields, False),
                "can_manage_chat": True,
            },
        )

        await env.bot.set_my_default_administrator_rights(rights=rights)

        assert (await env.bot.get_my_default_administrator_rights()).can_manage_chat is True
        assert (
            await env.bot.get_my_default_administrator_rights(for_channels=True)
        ).can_manage_chat is False

    async def test_unset_rights_are_all_false(self, env):
        rights = await env.bot.get_my_default_administrator_rights()

        assert not any(getattr(rights, name) for name in ChatAdministratorRights.model_fields)

    async def test_omitting_the_rights_clears_them(self, env):
        rights = ChatAdministratorRights(
            **{
                **dict.fromkeys(ChatAdministratorRights.model_fields, False),
                "can_manage_chat": True,
            },
        )
        await env.bot.set_my_default_administrator_rights(rights=rights)

        await env.bot.set_my_default_administrator_rights()

        assert (await env.bot.get_my_default_administrator_rights()).can_manage_chat is False


class TestMenuButton:
    async def test_the_default_button_round_trips(self, env):
        await env.bot.set_chat_menu_button(menu_button=MenuButtonCommands())

        assert isinstance(await env.bot.get_chat_menu_button(), MenuButtonCommands)

    async def test_an_unset_button_is_the_default_one(self, env):
        assert isinstance(await env.bot.get_chat_menu_button(), MenuButtonDefault)

    async def test_a_per_chat_button_overrides_the_default(self, env, private, team):
        await env.bot.set_chat_menu_button(menu_button=MenuButtonCommands())
        await env.bot.set_chat_menu_button(
            chat_id=private.id,
            menu_button=MenuButtonWebApp(
                text="Open",
                web_app=WebAppInfo(url="https://example.org"),
            ),
        )

        per_chat = await env.bot.get_chat_menu_button(chat_id=private.id)
        other = await env.bot.get_chat_menu_button(chat_id=team.id)

        assert isinstance(per_chat, MenuButtonWebApp)
        assert isinstance(other, MenuButtonCommands)

    async def test_omitting_the_button_stores_the_default(self, env, private):
        await env.bot.set_chat_menu_button(chat_id=private.id)

        assert isinstance(
            await env.bot.get_chat_menu_button(chat_id=private.id), MenuButtonDefault
        )

    @pytest.mark.parametrize("method_name", ["set_chat_menu_button", "get_chat_menu_button"])
    async def test_an_unknown_chat_fails(self, env, method_name):
        with pytest.raises(WorldLookupError, match="not declared in the blueprint"):
            await getattr(env.bot, method_name)(chat_id=-99)


class TestTheProfileKeepsItsOwnObjects:
    """
    What the profile stores is a copy, and what it reports is another one.

    A result is mounted to the calling bot, so both directions matter: storing the caller's
    ``BotCommand`` list would bind the test's constants the first time they are read back,
    and reporting the stored objects would bind the world's own state. The stored copies
    stay unbound, which is what makes an assertion against a declared constant possible at
    all — on the world, where the objects are values rather than answers.
    """

    async def test_the_commands_a_test_declared_are_not_captured(self, env):
        await env.bot.set_my_commands(commands=[START, HELP])

        stored = env.world.profile.commands[scope_key(None, None)]
        assert stored == [START, HELP]
        assert stored[0] is not START
        assert START.bot is None

    async def test_reading_the_commands_does_not_bind_the_stored_ones(self, env):
        await env.bot.set_my_commands(commands=[START])

        first = await env.bot.get_my_commands()
        second = await env.bot.get_my_commands()

        assert first[0] is not second[0]
        assert env.world.profile.commands[scope_key(None, None)] == [START]

    async def test_the_menu_button_is_stored_and_reported_as_a_copy(self, env):
        button = MenuButtonWebApp(text="Open", web_app=WebAppInfo(url="https://example.org"))

        await env.bot.set_chat_menu_button(menu_button=button)
        reported = await env.bot.get_chat_menu_button()

        assert button.bot is None
        assert env.world.profile.menu_buttons[None] is not button
        assert reported is not env.world.profile.menu_buttons[None]
        assert env.world.profile.menu_buttons[None] == button

    async def test_the_default_rights_are_stored_and_reported_as_a_copy(self, env):
        rights = ChatAdministratorRights(
            **dict.fromkeys(ChatAdministratorRights.model_fields, False),
        )

        await env.bot.set_my_default_administrator_rights(rights=rights)
        reported = await env.bot.get_my_default_administrator_rights()

        assert rights.bot is None
        assert env.world.profile.default_admin_rights[False] == rights
        assert reported is not env.world.profile.default_admin_rights[False]


class TestDeclaredProfile:
    @pytest.fixture
    def configured(self, dp):
        blueprint = Blueprint()
        alice = blueprint.add_user("Alice")
        blueprint.add_private_chat(alice)
        blueprint.set_bot_commands([START])
        blueprint.set_bot_profile(
            name="Declared",
            description="Declared description",
            short_description="Declared short",
            menu_button=MenuButtonCommands(),
        )
        environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            yield environment
        finally:
            environment.dispose_sync()

    async def test_declared_commands_are_readable_without_a_setter(self, configured):
        assert declared(await configured.bot.get_my_commands()) == declared([START])

    async def test_declared_texts_and_button_are_readable(self, configured):
        assert (await configured.bot.get_my_name()).name == "Declared"
        assert (await configured.bot.get_my_description()).description == "Declared description"
        assert (
            await configured.bot.get_my_short_description()
        ).short_description == "Declared short"
        assert isinstance(await configured.bot.get_chat_menu_button(), MenuButtonCommands)

    async def test_declared_rights_and_per_chat_button(self, dp):
        blueprint = Blueprint()
        alice = blueprint.add_user("Alice")
        chat = blueprint.add_private_chat(alice)
        rights = ChatAdministratorRights(
            **{
                **dict.fromkeys(ChatAdministratorRights.model_fields, False),
                "can_manage_chat": True,
            },
        )
        blueprint.set_bot_profile(
            default_admin_rights=rights,
            for_channels=True,
            menu_button=MenuButtonCommands(),
            menu_button_chat=chat,
        )
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            stored = await env.bot.get_my_default_administrator_rights(for_channels=True)

            assert stored.can_manage_chat is True
            assert isinstance(
                await env.bot.get_chat_menu_button(chat_id=chat.id),
                MenuButtonCommands,
            )
        finally:
            env.dispose_sync()

    async def test_profile_state_is_isolated_between_environments(self):
        blueprint = Blueprint()
        blueprint.set_bot_profile(name="Declared")

        first = BotTestEnvironment(blueprint=blueprint, dispatcher=Dispatcher())
        second = BotTestEnvironment(blueprint=blueprint, dispatcher=Dispatcher())
        try:
            await first.bot.set_my_name(name="Changed")

            assert (await second.bot.get_my_name()).name == "Declared"
            assert (await first.bot.get_my_name()).name == "Changed"
        finally:
            first.dispose_sync()
            second.dispose_sync()
