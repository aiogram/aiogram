import importlib
from typing import Any


def import_module(target: str) -> Any:
    if not isinstance(target, str):
        raise ValueError(f"Target should be string not {type(target).__class__.__name__}")

    module_name, _, attr_name = target.partition(":")
    if not module_name or not attr_name:
        raise ValueError(f'Import string "{target}" must be in format "<module>:<attribute>"')

    try:
        module = importlib.import_module(module_name)
    except ImportError:
        raise ValueError(f'Could not import module "{module_name}".')

    try:
        attribute = getattr(module, attr_name)
    except AttributeError:
        raise ValueError(f'Module "{module_name}" has no attribute "{attr_name}"')

    return attribute
