"""
This module contains utility functions for working with dataclasses in Python.

DO NOT USE THIS MODULE DIRECTLY. IT IS INTENDED FOR INTERNAL USE ONLY.
"""

import sys
from typing import Any, Union


def dataclass_kwargs(
    init: Union[bool, None] = None,
    repr: Union[bool, None] = None,
    eq: Union[bool, None] = None,
    order: Union[bool, None] = None,
    unsafe_hash: Union[bool, None] = None,
    frozen: Union[bool, None] = None,
    match_args: Union[bool, None] = None,
    kw_only: Union[bool, None] = None,
    slots: Union[bool, None] = None,
    weakref_slot: Union[bool, None] = None,
) -> dict[str, Any]:
    """
    Generates a dictionary of keyword arguments that can be passed to a Python
    dataclass. This function allows specifying attributes related to the behavior
    and configuration of dataclasses, including attributes added in specific
    Python versions. This abstraction improves compatibility across different
    Python versions by ensuring only the parameters supported by the current
    version are included.

    :return: A dictionary containing the specified dataclass configuration that
        dynamically adapts to the current Python version.
    """
    params = {}

    # All versions
    if init is not None:
        params["init"] = init
    if repr is not None:
        params["repr"] = repr
    if eq is not None:
        params["eq"] = eq
    if order is not None:
        params["order"] = order
    if unsafe_hash is not None:
        params["unsafe_hash"] = unsafe_hash
    if frozen is not None:
        params["frozen"] = frozen

    # Added in 3.10
    if sys.version_info >= (3, 10):
        if match_args is not None:
            params["match_args"] = match_args
        if kw_only is not None:
            params["kw_only"] = kw_only
        if slots is not None:
            params["slots"] = slots

    # Added in 3.11
    if sys.version_info >= (3, 11):
        if weakref_slot is not None:
            params["weakref_slot"] = weakref_slot

    return params
