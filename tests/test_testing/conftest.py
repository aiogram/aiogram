import pytest

from aiogram import Dispatcher
from aiogram.enums import ChatMemberStatus
from aiogram.test import Blueprint, BotTestEnvironment


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
