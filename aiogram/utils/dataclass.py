"""
This module contains utility functions for working with dataclasses in Python.

DO NOT USE THIS MODULE DIRECTLY. IT IS INTENDED FOR INTERNAL USE ONLY.
"""

from typing import Any


def dataclass_kwargs(
    init: bool | None = None,
    repr: bool | None = None,
    eq: bool | None = None,
    order: bool | None = None,
    unsafe_hash: bool | None = None,
    frozen: bool | None = None,
    match_args: bool | None = None,
    kw_only: bool | None = None,
    slots: bool | None = None,
    weakref_slot: bool | None = None,
) -> dict[str, Any]:
    """
    Generates a dictionary of keyword arguments that can be passed to a Python
    dataclass. Only the parameters that were explicitly set (not ``None``) are
    included, so callers can forward optional configuration without having to
    build the keyword arguments by hand.

    :return: A dictionary containing the specified dataclass configuration.
    """
    params = {}

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
    if match_args is not None:
        params["match_args"] = match_args
    if kw_only is not None:
        params["kw_only"] = kw_only
    if slots is not None:
        params["slots"] = slots
    if weakref_slot is not None:
        params["weakref_slot"] = weakref_slot

    return params
