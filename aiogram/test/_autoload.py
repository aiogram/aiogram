"""
What pytest's ``pytest11`` entry point loads: installing aiogram enables
:mod:`aiogram.test.plugin` in every pytest session, and ``-p no:aiogram`` turns it off.

It names the plugin instead of being it, so pytest registers the plugin under its module
name and a project that also enables it explicitly (``-p aiogram.test.plugin`` or
``pytest_plugins``) loads it once rather than failing with "Plugin already registered
under a different name". Before pytest 8, which the plugin needs, it registers nothing: a
session that never asked for the toolkit must not break on it.
"""

import pytest

pytest_plugins: list[str] = (
    ["aiogram.test.plugin"] if getattr(pytest, "version_tuple", (0,)) >= (8,) else []
)
