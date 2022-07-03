from typing import TYPE_CHECKING, Any, Dict, Optional, Union, cast

from magic_filter import AttrDict, MagicFilter

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import HandlerObject


def extract_flags_from_object(obj: Any) -> Dict[str, Any]:
    if not hasattr(obj, "aiogram_flag"):
        return {}
    return cast(Dict[str, Any], obj.aiogram_flag)


def extract_flags(handler: Union["HandlerObject", Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract flags from handler or middleware context data

    :param handler: handler object or data
    :return: dictionary with all handler flags
    """
    if isinstance(handler, dict) and "handler" in handler:
        handler = handler["handler"]
    if not hasattr(handler, "flags"):
        return {}
    return handler.flags  # type: ignore


def get_flag(
    handler: Union["HandlerObject", Dict[str, Any]],
    name: str,
    *,
    default: Optional[Any] = None,
) -> Any:
    """
    Get flag by name

    :param handler: handler object or data
    :param name: name of the flag
    :param default: default value (None)
    :return: value of the flag or default
    """
    flags = extract_flags(handler)
    return flags.get(name, default)


def check_flags(handler: Union["HandlerObject", Dict[str, Any]], magic: MagicFilter) -> Any:
    """
    Check flags via magic filter

    :param handler: handler object or data
    :param magic: instance of the magic
    :return: the result of magic filter check
    """
    flags = extract_flags(handler)
    return magic.resolve(AttrDict(flags))
