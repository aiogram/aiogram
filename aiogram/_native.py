import sys
import sysconfig
from importlib.machinery import EXTENSION_SUFFIXES
from importlib.util import find_spec

INSTALL_DOCS_URL = "https://docs.aiogram.dev/en/latest/install.html"


def require_core() -> None:
    """Raise ImportError when no compiled ``aiogram._core`` fits this interpreter.

    It only looks the extension up and does not load it, so ``import aiogram`` stays free of
    ``_core`` (tests/test_core/test_build.py).
    """
    spec = find_spec("aiogram._core")
    # without the .so, the stub-only aiogram/_core/ directory resolves as a namespace package
    # (no origin). Any other loader is accepted: freezers (Nuitka) bring their own.
    if spec is not None and spec.origin is not None and spec.submodule_search_locations is None:
        return
    implementation = "cp" if sys.implementation.name == "cpython" else sys.implementation.name
    free_threaded = "t" if sysconfig.get_config_var("Py_GIL_DISABLED") else ""
    tag = f"{implementation}{sys.version_info.major}{sys.version_info.minor}{free_threaded}"
    msg = (
        f"aiogram's compiled core is missing: no aiogram/_core{EXTENSION_SUFFIXES[0]} for this "
        f"interpreter ({tag}, {sysconfig.get_platform()}). Install a wheel built for {tag}, or "
        f"build aiogram from the sdist with Rust installed. See {INSTALL_DOCS_URL}"
    )
    raise ImportError(msg, name="aiogram._core")


require_core()
