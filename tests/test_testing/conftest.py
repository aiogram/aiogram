import pytest

from aiogram import Dispatcher
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.test import Blueprint, BotTestEnvironment, administrator_rights

#: What the bot holds in a chat a test has it moderate: an ordinary
#: administrator's rights, plus promoting others.
MODERATOR_RIGHTS = administrator_rights(can_promote_members=True)


@pytest.fixture
def blueprint():
    blueprint = Blueprint()
    alice = blueprint.add_user("Alice", username="alice")
    blueprint.add_private_chat(alice)
    blueprint.add_supergroup("Team", members={alice: ChatMemberStatus.ADMINISTRATOR})
    blueprint.add_business_connection(alice)
    return blueprint


@pytest.fixture
def dp():
    return Dispatcher()


@pytest.fixture
def env(blueprint, dp):
    environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
    try:
        yield environment
    finally:
        environment.dispose_sync()


@pytest.fixture
def alice(env, blueprint):
    return env.user(blueprint.users[0])


@pytest.fixture
def private(env, blueprint):
    return env.chat(blueprint.chats[0])


@pytest.fixture
def team(env, blueprint):
    return env.chat(blueprint.chats[1])


@pytest.fixture
def connection(env, blueprint):
    return env.business_connection(blueprint.business_connections[0])


@pytest.fixture
def moderated():
    """
    Declare the bot a moderator of every group-like chat of a blueprint.

    The bot's own calls are checked against its rights, so a test of
    banning, restricting, promoting or pinning declares the rights it
    uses; this is the one declaration those tests share. Override the
    ``blueprint`` fixture with it::

        @pytest.fixture
        def blueprint(self, blueprint, moderated):
            return moderated(blueprint)
    """

    def declare(blueprint: Blueprint) -> Blueprint:
        for chat in blueprint.chats:
            if chat.type != ChatType.PRIVATE:
                blueprint.set_member(chat, blueprint.bot, rights=MODERATOR_RIGHTS)
        return blueprint

    return declare
