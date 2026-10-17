from contextlib import contextmanager

import pytest

from aiogram import Dispatcher
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
)
from aiogram.test import ApiRejection, Blueprint, BotTestEnvironment, administrator_rights
from aiogram.test.refusals import Refusal, refusal_of

#: The exception type each error code the toolkit refuses with becomes.
EXCEPTION_FOR_CODE = {
    400: TelegramBadRequest,
    403: TelegramForbiddenError,
    429: TelegramRetryAfter,
}


@contextmanager
def refused_with(error_type: type[TelegramAPIError], refusal: Refusal):
    """
    Expect a call to fail as ``refusal`` declares, without matching its text.

    The exception type is the contract and the declaration says which
    of the refusals of that code fired, so a best-effort wording can
    change without a test noticing.
    """
    with pytest.raises(error_type) as caught:
        yield
    assert refusal_of(caught.value) is refusal
    assert type(caught.value) is EXCEPTION_FOR_CODE[refusal.error_code]


@pytest.fixture(autouse=True)
def _every_refusal_keeps_its_contract(monkeypatch):
    """
    Check the error contract on every refusal any test in this package causes.

    The error code and the exception type are guaranteed, whatever the text says.
    So whenever the environment answers a refusal, the exception that comes out
    must be the type its code stands for, a 429 must carry its ``retry_after``,
    and the refusal must be one declared in :mod:`aiogram.test.refusals`.
    """
    refuse = BotTestEnvironment._refuse

    def checked(self, method, error: ApiRejection):
        assert error.refusal is not None, f"{error.description!r} is not a declared refusal"
        try:
            refuse(self, method, error)
        except TelegramAPIError as raised:
            assert type(raised) is EXCEPTION_FOR_CODE[error.error_code], error.description
            if error.retry_after is not None:
                assert raised.retry_after == error.retry_after
            raise

    monkeypatch.setattr(BotTestEnvironment, "_refuse", checked)


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
