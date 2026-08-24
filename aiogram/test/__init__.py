"""
Integration testing toolkit for aiogram bots.

Feeds real updates through a real :class:`~aiogram.dispatcher.dispatcher.Dispatcher`
against a stateful fake Telegram, so filters, middlewares, dependency injection, FSM and
Scenes all run — while every Bot API call is answered from, and applied to, an isolated
in-memory world.

Nothing here imports :mod:`pytest`; the fixtures live in :mod:`aiogram.test.plugin`,
which pytest loads through the ``pytest11`` entry point.
"""

from .actors import UserActor
from .blueprint import (
    Blueprint,
    BusinessConnectionSpec,
    ChatSpec,
    CommunitySpec,
    MemberSpec,
    TopicSpec,
    UserSpec,
    default_blueprint,
)
from .calls import CallLog, NoSuchCallError
from .environment import BotTestEnvironment, build_environment
from .errors import WaitTimeoutError
from .overrides import Outcome, OverrideBuilder
from .routing import detach_router
from .session import FakeTelegramSession
from .synthesis import SynthesisContext, SynthesisError, synthesize, synthesize_result
from .world import (
    BASE_DATE,
    BotProfileState,
    BusinessConnectionState,
    ChatState,
    CommunityState,
    InviteLinkState,
    MemberState,
    TopicState,
    UserState,
    World,
    WorldLookupError,
    administrator_rights,
)

__all__ = (
    "BASE_DATE",
    "Blueprint",
    "BotProfileState",
    "BotTestEnvironment",
    "BusinessConnectionSpec",
    "BusinessConnectionState",
    "CallLog",
    "ChatSpec",
    "ChatState",
    "CommunitySpec",
    "CommunityState",
    "InviteLinkState",
    "FakeTelegramSession",
    "MemberSpec",
    "MemberState",
    "NoSuchCallError",
    "Outcome",
    "OverrideBuilder",
    "SynthesisContext",
    "SynthesisError",
    "TopicSpec",
    "TopicState",
    "UserActor",
    "UserSpec",
    "UserState",
    "WaitTimeoutError",
    "World",
    "WorldLookupError",
    "administrator_rights",
    "build_environment",
    "default_blueprint",
    "detach_router",
    "synthesize",
    "synthesize_result",
)
