from typing import Any, Dict, Optional, TypeVar, Union

from aiogram.filters.base import Filter
from aiogram.types import ChatMember, ChatMemberUpdated

MarkerT = TypeVar("MarkerT", bound="_MemberStatusMarker")
MarkerGroupT = TypeVar("MarkerGroupT", bound="_MemberStatusGroupMarker")
TransitionT = TypeVar("TransitionT", bound="_MemberStatusTransition")


class _MemberStatusMarker:
    __slots__ = (
        "name",
        "is_member",
    )

    def __init__(self, name: str, *, is_member: Optional[bool] = None) -> None:
        self.name = name
        self.is_member = is_member

    def __str__(self) -> str:
        result = self.name.upper()
        if self.is_member is not None:
            result = ("+" if self.is_member else "-") + result
        return result  # noqa: RET504

    def __pos__(self: MarkerT) -> MarkerT:
        return type(self)(name=self.name, is_member=True)

    def __neg__(self: MarkerT) -> MarkerT:
        return type(self)(name=self.name, is_member=False)

    def __or__(
        self, other: Union["_MemberStatusMarker", "_MemberStatusGroupMarker"]
    ) -> "_MemberStatusGroupMarker":
        if isinstance(other, _MemberStatusMarker):
            return _MemberStatusGroupMarker(self, other)
        if isinstance(other, _MemberStatusGroupMarker):
            return other | self
        raise TypeError(
            f"unsupported operand type(s) for |: "
            f"{type(self).__name__!r} and {type(other).__name__!r}"
        )

    __ror__ = __or__

    def __rshift__(
        self, other: Union["_MemberStatusMarker", "_MemberStatusGroupMarker"]
    ) -> "_MemberStatusTransition":
        old = _MemberStatusGroupMarker(self)
        if isinstance(other, _MemberStatusMarker):
            return _MemberStatusTransition(old=old, new=_MemberStatusGroupMarker(other))
        if isinstance(other, _MemberStatusGroupMarker):
            return _MemberStatusTransition(old=old, new=other)
        raise TypeError(
            f"unsupported operand type(s) for >>: "
            f"{type(self).__name__!r} and {type(other).__name__!r}"
        )

    def __lshift__(
        self, other: Union["_MemberStatusMarker", "_MemberStatusGroupMarker"]
    ) -> "_MemberStatusTransition":
        new = _MemberStatusGroupMarker(self)
        if isinstance(other, _MemberStatusMarker):
            return _MemberStatusTransition(old=_MemberStatusGroupMarker(other), new=new)
        if isinstance(other, _MemberStatusGroupMarker):
            return _MemberStatusTransition(old=other, new=new)
        raise TypeError(
            f"unsupported operand type(s) for <<: "
            f"{type(self).__name__!r} and {type(other).__name__!r}"
        )

    def __hash__(self) -> int:
        return hash((self.name, self.is_member))

    def check(self, *, member: ChatMember) -> bool:
        # Not all member types have `is_member` attribute
        is_member = getattr(member, "is_member", None)
        status = getattr(member, "status", None)
        if self.is_member is not None and is_member != self.is_member:
            return False
        return self.name == status


class _MemberStatusGroupMarker:
    __slots__ = ("statuses",)

    def __init__(self, *statuses: _MemberStatusMarker) -> None:
        if not statuses:
            raise ValueError("Member status group should have at least one status included")
        self.statuses = frozenset(statuses)

    def __or__(
        self: MarkerGroupT, other: Union["_MemberStatusMarker", "_MemberStatusGroupMarker"]
    ) -> MarkerGroupT:
        if isinstance(other, _MemberStatusMarker):
            return type(self)(*self.statuses, other)
        if isinstance(other, _MemberStatusGroupMarker):
            return type(self)(*self.statuses, *other.statuses)
        raise TypeError(
            f"unsupported operand type(s) for |: "
            f"{type(self).__name__!r} and {type(other).__name__!r}"
        )

    def __rshift__(
        self, other: Union["_MemberStatusMarker", "_MemberStatusGroupMarker"]
    ) -> "_MemberStatusTransition":
        if isinstance(other, _MemberStatusMarker):
            return _MemberStatusTransition(old=self, new=_MemberStatusGroupMarker(other))
        if isinstance(other, _MemberStatusGroupMarker):
            return _MemberStatusTransition(old=self, new=other)
        raise TypeError(
            f"unsupported operand type(s) for >>: "
            f"{type(self).__name__!r} and {type(other).__name__!r}"
        )

    def __lshift__(
        self, other: Union["_MemberStatusMarker", "_MemberStatusGroupMarker"]
    ) -> "_MemberStatusTransition":
        if isinstance(other, _MemberStatusMarker):
            return _MemberStatusTransition(old=_MemberStatusGroupMarker(other), new=self)
        if isinstance(other, _MemberStatusGroupMarker):
            return _MemberStatusTransition(old=other, new=self)
        raise TypeError(
            f"unsupported operand type(s) for <<: "
            f"{type(self).__name__!r} and {type(other).__name__!r}"
        )

    def __str__(self) -> str:
        result = " | ".join(map(str, sorted(self.statuses, key=str)))
        if len(self.statuses) != 1:
            return f"({result})"
        return result

    def check(self, *, member: ChatMember) -> bool:
        return any(status.check(member=member) for status in self.statuses)


class _MemberStatusTransition:
    __slots__ = (
        "old",
        "new",
    )

    def __init__(self, *, old: _MemberStatusGroupMarker, new: _MemberStatusGroupMarker) -> None:
        self.old = old
        self.new = new

    def __str__(self) -> str:
        return f"{self.old} >> {self.new}"

    def __invert__(self: TransitionT) -> TransitionT:
        return type(self)(old=self.new, new=self.old)

    def check(self, *, old: ChatMember, new: ChatMember) -> bool:
        return self.old.check(member=old) and self.new.check(member=new)


CREATOR = _MemberStatusMarker("creator")
ADMINISTRATOR = _MemberStatusMarker("administrator")
MEMBER = _MemberStatusMarker("member")
RESTRICTED = _MemberStatusMarker("restricted")
LEFT = _MemberStatusMarker("left")
KICKED = _MemberStatusMarker("kicked")

IS_MEMBER = CREATOR | ADMINISTRATOR | MEMBER | +RESTRICTED
IS_ADMIN = CREATOR | ADMINISTRATOR
IS_NOT_MEMBER = LEFT | KICKED | -RESTRICTED

JOIN_TRANSITION = IS_NOT_MEMBER >> IS_MEMBER
LEAVE_TRANSITION = ~JOIN_TRANSITION
PROMOTED_TRANSITION = (MEMBER | RESTRICTED | LEFT | KICKED) >> ADMINISTRATOR


class ChatMemberUpdatedFilter(Filter):
    __slots__ = ("member_status_changed",)

    def __init__(
        self,
        member_status_changed: Union[
            _MemberStatusMarker,
            _MemberStatusGroupMarker,
            _MemberStatusTransition,
        ],
    ):
        self.member_status_changed = member_status_changed

    def __str__(self) -> str:
        return self._signature_to_string(
            member_status_changed=self.member_status_changed,
        )

    async def __call__(self, member_updated: ChatMemberUpdated) -> Union[bool, Dict[str, Any]]:
        old = member_updated.old_chat_member
        new = member_updated.new_chat_member
        rule = self.member_status_changed

        if isinstance(rule, (_MemberStatusMarker, _MemberStatusGroupMarker)):
            return rule.check(member=new)
        if isinstance(rule, _MemberStatusTransition):
            return rule.check(old=old, new=new)

        # Impossible variant in due to pydantic validation
        return False  # pragma: no cover
