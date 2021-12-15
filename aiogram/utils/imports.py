import importlib
from typing import Any, Set
from pathlib import Path


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


DEFAULT_EXCLUDE_MODULES = frozenset({"__pycache__", "__init__.py", "__main__.py"})


def import_all_modules(
    root: str,
    package: str = None,
    exclude: Set[str] = DEFAULT_EXCLUDE_MODULES
):
    """
    imports all modules inside root and inside all subdirectories, sub-subdirectories etc of root

    The 'package' argument is required when performing a relative import. It
    specifies the package to use as the anchor point from which to resolve the
    relative import to an absolute import.

    :param root: root directory where function will start importing and digging to subdirectories
    :param package: your top-level package name if 'root' is not absolute (starts with .)
    :param exclude: set of names that will be ignored,
        if it is a directory - also doesn't iterate over its insides
    """
    root_module = importlib.import_module(root, package)
    root_dir = root_module.__path__[0]
    for sub_dir in Path(root_dir).iterdir():
        if sub_dir.name in exclude:
            continue
        if sub_dir.is_dir():
            import_all_modules(f"{root}.{sub_dir.stem}", package)
        else:
            importlib.import_module(f"{root}.{sub_dir.stem}", package)
