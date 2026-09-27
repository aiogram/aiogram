"""
The boundary between the fake world and the code under test.

Every object in a test either belongs to the world — bound to the environment's bot, so
its shortcuts work — or belongs to whoever built it and must stay unbound. This module
owns both halves of that policy, and nothing else does:

* :func:`mount` claims genuinely fresh objects for a bot as they leave towards the code
  under test, and leaves alone anything that already has an owner;
* :func:`detach` and :func:`detached_copy` produce objects nobody owns, for the moments
  something crosses the boundary the other way — a canned result handed out, a caller's
  constant taken into the world, an update arriving from another environment;
* :func:`owned_or_copied` is the boundary *inwards*, where the two are mixed: a value a
  test hands the world may be the test's own or may be the world's own, and only the
  former may be copied.

:func:`bindables` is the single walk underneath all of them.
"""

from __future__ import annotations

import copy
from collections.abc import Iterable, Iterator, Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from pydantic import BaseModel

from aiogram.client.context_controller import BotContextController

if TYPE_CHECKING:
    from aiogram.client.bot import Bot

__all__ = (
    "bindables",
    "bound_elsewhere",
    "detach",
    "detached_copy",
    "mount",
    "owned_or_copied",
)

_Value = TypeVar("_Value")


def mount(value: Any, bot: Bot) -> Any:
    """
    Bind every *unbound* object reachable from ``value`` to ``bot``, and return ``value``.

    A real session deserializes every response with ``context={"bot": bot}``, which pydantic
    threads through the whole object tree — so ``message.delete()``, ``message.answer()``
    and the shortcuts of nested objects such as ``message.reply_to_message`` all work on
    whatever a Bot API call returned.

    The fake world hands back objects that were *constructed*, not parsed, so that context
    never runs and every shortcut on them would raise. Re-parsing them to reuse pydantic's
    mechanism is not an option: pydantic skips validation of model instances
    (``revalidate_instances`` is ``"never"``), so binding would require a dump/validate
    round-trip — which mints copies, severing the identity between a returned message and
    the one the world keeps, and quietly reshapes unions and sentinel defaults along the
    way. Walking the tree and calling
    :meth:`~aiogram.client.context_controller.BotContextController.as_` mirrors what the
    context does while leaving the objects themselves untouched.

    This is the toolkit's single binding mechanism. It runs at every point where an object
    enters the fake world or leaves it towards the code under test: when a chat stores a
    message (:meth:`aiogram.test.world.ChatState.add_message`), when an update is fed
    (:meth:`aiogram.test.BotTestEnvironment.feed`) and when a call is answered
    (:meth:`aiogram.test.FakeTelegramSession.make_request`).

    **Ownership rule: an object that already carries a bot is left alone, and the walk
    stops there.** Because everything is bound the moment it enters the world, an object
    that is already bound belongs to the environment, and a later caller must not claim it.
    That matters as soon as a *second* :class:`~aiogram.client.bot.Bot` shares the session
    — the documented recipe for testing a bot that sends through a module-level instance:
    rebinding a stored message to it would silently change which
    :class:`~aiogram.client.default.DefaultBotProperties` every later shortcut on that
    message resolves against. Only genuinely fresh objects, minted for this very call, are
    bound to the caller.

    Pruning is what keeps the walk cheap, too: re-answering with a stored message stops the
    walk at that message instead of re-walking everything it transitively refers to.
    """
    for node in bindables(value, prune_bound=True):
        if node.bot is None:
            node.as_(bot)
    return value


def detach(value: _Value) -> _Value:
    """
    Unbind every object reachable from ``value``, in place, and return ``value``.

    The inverse of :func:`mount`, for an object that is *derived* from one the world owns:
    :meth:`~pydantic.BaseModel.model_copy` carries the original's binding over, so the
    derived object would be pruned at its root and everything the derivation brought with
    it — a new chat, a new sender, a new keyboard — would stay unbound and raise on its
    first shortcut. A derived object is a fresh object; this is what makes it one.

    Use :func:`detached_copy` instead when the original must survive untouched.
    """
    for node in bindables(value):
        node.as_(None)
    return value


def bound_elsewhere(value: Any, bot: Bot) -> bool:
    """
    Whether anything reachable from ``value`` already belongs to a *different* bot.

    Identity, not equality: :meth:`aiogram.client.bot.Bot.__eq__` compares token hashes, so
    two environments built from the same blueprint have equal — and therefore
    indistinguishable — bots, while only one of them owns any given object.
    """
    return any(
        node.bot is not None and node.bot is not bot for node in bindables(value, prune_bound=True)
    )


def detached_copy(value: Any, *, bot: Bot | None = None) -> Any:
    """
    A copy of ``value`` that shares no *state* with it, bound to ``bot`` or to nobody.

    Copying is what keeps two owners apart when neither may be disturbed: a canned result
    the test declared once at module level and the answer a call hands out, a caller's
    ``reply_markup`` constant and the message the world stores, an update fed to a second
    environment and the first environment that still owns it.

    **What is rebuilt, and what is shared.** The copy is assembled out of the three shapes
    a Bot API value is made of — pydantic models, mappings and lists — plus the immutable
    containers a test may wrap them in. Everything else is a *leaf* and is handed on as it
    is: a date, an enum, a sentinel, an uploaded :class:`~aiogram.types.input_file.InputFile`.
    That is the rule that makes a live :class:`~aiogram.client.bot.Bot` impossible to clone.
    :func:`copy.deepcopy` would follow a leaf's attributes, and one leaf really does hold a
    bot — ``URLInputFile(url, bot=...)`` keeps one to stream through — so copying leaves
    used to mint a twin of the bot, of its session, of the whole environment and world
    behind it. Nothing here ever constructs an object it does not recognise, so nothing
    reachable through a leaf can be duplicated; a shared leaf carries no world state and no
    binding of its own, which is why sharing it is also correct.

    Bindings are decided as the copy is made rather than by a second pass over it: a model's
    ``_bot`` lives in its private attributes, which the walk never follows. Passing ``bot``
    also lets the answer path hand the session an already-owned object, whose :func:`mount`
    then prunes at the root instead of walking the whole graph again.

    The model graph is walked iteratively, for the same reason :func:`bindables` is: a reply
    chain or a canned result is as deep as a test cares to build, and :func:`copy.deepcopy`
    recurses once per level — it gives up around 200 levels deep, far short of what the
    mount walk handles. Round-tripping through ``model_dump``/``model_validate`` is no
    better: pydantic-core's serializer refuses even sooner, reporting the depth as a
    circular reference.
    """
    # id() -> the copy of the object with that id. Every original stays alive through
    # `value` for as long as this runs, so the ids cannot be recycled underneath us. No
    # entry is ever a reservation, so a lookup that hits is always a finished copy.
    memo: dict[int, Any] = {}
    # Containers whose copy exists but is still empty, in discovery order.
    shells: list[tuple[Any, Any]] = []
    # Immutable containers already walked. They have no shell to fill — they are built from
    # finished children by `copied`, on the way into whatever holds them — so the memo
    # cannot stand in for "seen" while the walk is still running.
    walked: set[int] = set()

    stack: list[Any] = [value]
    while stack:
        node = stack.pop()
        # Cheap rejection first, exactly as in `bindables`.
        if node is None or isinstance(node, (str, bytes, int, float)) or id(node) in memo:
            continue
        if isinstance(node, BaseModel):
            shell = copy.copy(node)
            if isinstance(shell, BotContextController):
                shell.as_(bot)
            memo[id(node)] = shell
            shells.append((node, shell))
            stack.extend(node.__dict__.values())
            stack.extend((node.__pydantic_extra__ or {}).values())
        elif isinstance(node, Mapping):
            mapping: dict[Any, Any] = {}
            memo[id(node)] = mapping
            shells.append((node, mapping))
            stack.extend(node.values())
        elif isinstance(node, list):
            items: list[Any] = []
            memo[id(node)] = items
            shells.append((node, items))
            stack.extend(node)
        elif isinstance(node, (tuple, set, frozenset)) and id(node) not in walked:
            # Only to give whatever is inside a shell of its own; the container itself is
            # rebuilt by `copied`.
            walked.add(id(node))
            stack.extend(node)
        # Anything else is a leaf, and is shared rather than copied.

    def copied(item: Any) -> Any:
        if id(item) in memo:
            return memo[id(item)]
        if isinstance(item, (tuple, set, frozenset)):
            # An immutable container cannot be filled after the fact, so it is built from
            # finished children. Recursion is bounded by how deeply such containers nest —
            # no Bot API type has a tuple, set or frozenset field at all, so in practice
            # this is one level of whatever a test wrapped a result in.
            #
            # A `set` rehashes its elements here, and a model copy may still be an unfilled
            # shell at this point — but its hash cannot move underneath the set, so the
            # buckets it lands in are the final ones. A shell is `copy.copy`, which carries
            # the original's ``__dict__`` over, so it hashes like the original from the
            # moment it exists; filling it then swaps each child for a copy of that child,
            # and pydantic hashes a model by the tuple of its field values, where a copy is
            # equal to — and therefore hashes like — what it was copied from, all the way
            # down to the shared scalar leaves. What a copy does *not* carry over is the
            # binding, which lives in the private attributes the hash never reads.
            contents = [copied(inner) for inner in item]
            rebuilt = tuple(contents) if isinstance(item, tuple) else type(item)(contents)
            memo[id(item)] = rebuilt
            return rebuilt
        return item

    for node, shell in shells:
        if isinstance(node, BaseModel):
            shell.__dict__.update((name, copied(item)) for name, item in node.__dict__.items())
            extra = node.__pydantic_extra__
            if extra:
                shell.__pydantic_extra__.update(
                    (name, copied(item)) for name, item in extra.items()
                )
        elif isinstance(shell, dict):
            shell.update((key, copied(item)) for key, item in node.items())
        else:
            shell.extend(copied(item) for item in node)

    return copied(value)


def owned_or_copied(value: Any, *, owner: Bot | None, bind: Bot | None = None) -> Any:
    """
    ``value`` itself wherever it already belongs to ``owner``, a copy everywhere else.

    The rule for everything a test hands *into* the world — the ``fields`` of a trigger, the
    ``changes`` of an edit — where the values are of two kinds and only one of them may be
    copied.

    A value the caller built is the caller's: a module-level ``MENU`` keyboard, a constant
    reaction list. Letting one of those into the world binds it to a bot as the world mounts
    whatever it stores, so a constant shared across a session stops being equal to the
    unbound copy the world keeps. Those are copied, exactly as
    :func:`detached_copy` describes.

    A value already bound to ``owner`` is the *world's* own object instead — most often a
    message the same chat already holds, passed as ``reply_to_message`` — and copying it is
    the bug this exists to prevent: the copy is a snapshot, so a later edit to the stored
    message no longer shows through it, and two fields that aliased one stored object become
    two unrelated copies. Such a value is returned untouched.

    ``dict`` and ``list`` are walked so that a world object nested inside them is recognised
    too; everything else — unbound, or bound to some *other* bot — is copied. Copies are
    minted bound to ``bind``, for the callers whose result goes straight into the world and
    would otherwise have to be bound by a second walk.
    """
    if isinstance(value, dict):
        return {
            name: owned_or_copied(item, owner=owner, bind=bind) for name, item in value.items()
        }
    if isinstance(value, list):
        return [owned_or_copied(item, owner=owner, bind=bind) for item in value]
    if owner is not None and isinstance(value, BotContextController) and value.bot is owner:
        return value
    return detached_copy(value, bot=bind)


def bindables(value: Any, *, prune_bound: bool = False) -> Iterator[BotContextController]:
    """
    Walk the object graph of ``value``, yielding every bindable object it reaches.

    The walk is iterative rather than recursive because the graphs are not shallow: the
    fake nests ``reply_to_message`` as deep as a reply chain is long, and a recursive
    walker hit Python's recursion limit on chains a test can plausibly build.

    ``prune_bound`` stops the walk at objects that already carry a bot — see :func:`mount`
    for why that is the correct ownership rule and not merely an optimization. Such an
    object is still yielded, so a caller can see *whose* it is; what it holds is not, since
    that belongs to the same owner.
    """
    seen: set[int] = set()
    stack: list[Any] = [value]
    while stack:
        current = stack.pop()
        # Cheap rejection first: results are most often `bool`, `int` or `str`.
        if current is None or isinstance(current, (str, bytes, int, float)):
            continue

        identity = id(current)
        if identity in seen:
            # The world stores objects by reference, so the same `Chat` shows up on every
            # message of a chat, and a message may transitively refer back to itself.
            continue
        seen.add(identity)

        if isinstance(current, BaseModel):
            if isinstance(current, BotContextController):
                # Read before yielding: the consumer is `mount` as often as not, and it
                # binds what it is handed — asking afterwards would prune every object the
                # walk had just claimed, and with it everything nested inside.
                owned = current.bot is not None
                yield current
                if prune_bound and owned:
                    continue
            # `__dict__` holds the validated fields; `extra="allow"` parks unknown ones,
            # which may carry objects from a future Bot API version, in
            # `__pydantic_extra__`.
            stack.extend(current.__dict__.values())
            stack.extend((current.__pydantic_extra__ or {}).values())
        elif isinstance(current, Mapping):
            stack.extend(current.values())
        elif isinstance(current, Iterable):
            # Nested lists are real: `InlineKeyboardMarkup.inline_keyboard` is a list of rows.
            stack.extend(current)
