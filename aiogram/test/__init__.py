"""
Integration testing toolkit for aiogram bots.

Feeds real updates through a real :class:`~aiogram.dispatcher.dispatcher.Dispatcher`
against a stateful fake Telegram, so filters, middlewares, dependency injection, FSM and
Scenes all run — while every Bot API call is answered from, and applied to, an isolated
in-memory world.

Nothing here imports :mod:`pytest`; the fixtures live in :mod:`aiogram.test.plugin`,
which pytest loads through the ``pytest11`` entry point.
"""

from . import rejections
from .actors import UserActor, Withheld
from .blueprint import (
    Blueprint,
    BusinessConnectionSpec,
    ChatSpec,
    CommunitySpec,
    MemberSpec,
    PollSpec,
    TopicSpec,
    UserSpec,
    default_blueprint,
)
from .calls import CallLog, NoSuchCallError
from .environment import BotTestEnvironment, RouteRecord, build_environment
from .errors import (
    ApiRejection,
    BackgroundTaskError,
    DrainedTaskError,
    NoFileContentError,
    WaitTimeoutError,
)
from .flood import RateLimit, RateLimits
from .overrides import (
    ADDRESSING_FIELDS,
    BLOCKED_BY_USER,
    BLOCKED_METHODS,
    DELIVERY_METHODS,
    MethodMatcher,
    Outcome,
    OverrideBuilder,
    OverrideHandle,
    OverrideRule,
)
from .rejections import rejection_fields, rejection_of
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
    default_chat_permissions,
)

__all__ = (
    "ADDRESSING_FIELDS",
    "BASE_DATE",
    "BLOCKED_BY_USER",
    "BLOCKED_METHODS",
    "DELIVERY_METHODS",
    "ApiRejection",
    "BackgroundTaskError",
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
    "DrainedTaskError",
    "FakeTelegramSession",
    "InviteLinkState",
    "MemberSpec",
    "MemberState",
    "MethodMatcher",
    "NoFileContentError",
    "NoSuchCallError",
    "Outcome",
    "OverrideBuilder",
    "OverrideHandle",
    "OverrideRule",
    "PollSpec",
    "RateLimit",
    "RateLimits",
    "RouteRecord",
    "SynthesisContext",
    "SynthesisError",
    "TopicSpec",
    "TopicState",
    "UserActor",
    "UserSpec",
    "UserState",
    "WaitTimeoutError",
    "Withheld",
    "World",
    "WorldLookupError",
    "administrator_rights",
    "build_environment",
    "default_blueprint",
    "default_chat_permissions",
    "detach_router",
    "rejection_fields",
    "rejection_of",
    "rejections",
    "synthesize",
    "synthesize_result",
)
