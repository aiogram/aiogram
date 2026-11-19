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
from aiogram.test.rejections import Rejection, rejection_fields, rejection_of

#: The exception type each error code the toolkit refuses with becomes.
EXCEPTION_FOR_CODE = {
    400: TelegramBadRequest,
    403: TelegramForbiddenError,
    429: TelegramRetryAfter,
}


@contextmanager
def refused_with(
    error_type: type[TelegramAPIError],
    rejection: Rejection,
    **fields: object,
):
    """
    Expect a call to fail as ``rejection`` declares, not as it words it.

    The exception type is the contract and the declaration says which
    of the rejections of that code fired, so a best-effort wording can
    change without a test noticing. Fields name what the description
    was filled in with, such as ``noun="polls"``.
    """
    with pytest.raises(error_type) as caught:
        yield
    assert rejection_of(caught.value) is rejection
    assert type(caught.value) is EXCEPTION_FOR_CODE[rejection.error_code]
    found = rejection_fields(caught.value)
    assert {name: found.get(name) for name in fields} == {
        name: str(value) for name, value in fields.items()
    }


@pytest.fixture(autouse=True)
def _every_rejection_keeps_its_contract(monkeypatch):
    """
    Check the error contract on every rejection a test causes.

    The code and the exception type are guaranteed, whatever the
    description says. Whenever the environment answers a rejection,
    the exception must be the type its code stands for, carry its
    ``retry_after``, and come from a declared rejection. A violation
    is recorded and fails the test at teardown, as a handler's broad
    ``except`` could swallow an assertion raised in the call.
    """
    refuse = BotTestEnvironment._refuse
    violations = []

    def checked(self, method, error: ApiRejection):
        if error.rejection is None:
            violations.append(f"{error.description!r} is not declared")
        try:
            refuse(self, method, error)
        except TelegramAPIError as raised:
            if type(raised) is not EXCEPTION_FOR_CODE.get(error.error_code):
                violations.append(f"{error.description!r} became {type(raised)}")
            if getattr(raised, "retry_after", None) != error.retry_after:
                violations.append(f"{error.description!r} lost its retry_after")
            raise

    monkeypatch.setattr(BotTestEnvironment, "_refuse", checked)
    yield
    assert not violations, violations


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
