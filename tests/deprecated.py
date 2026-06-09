from contextlib import contextmanager

import pytest
from packaging import version

import aiogram


@contextmanager
def check_deprecated(
    max_version: str,
    exception: type[Exception],
    warning: type[Warning] = DeprecationWarning,
) -> None:
    """
    Should be used for modules that are being deprecated or already removed from aiogram
    """

    parsed_max_version = version.parse(max_version)
    current_version = version.parse(aiogram.__version__)

    if parsed_max_version <= current_version:
        with pytest.raises(exception):
            yield
    else:
        with pytest.warns(warning, match=max_version):
            yield
