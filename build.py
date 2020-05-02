from pathlib import Path
from typing import Any, Dict

BUILD_PATH: Path = Path(__file__).parent
META_PATH: Path = BUILD_PATH / "aiogram" / "_meta.py"


def write_metadata(setup_kwargs: Dict[str, Any]) -> None:
    version = setup_kwargs["version"]
    description = setup_kwargs["description"]

    content = [f"VERSION = {version!r}", f"DESCRIPTION = {description!r}"]

    META_PATH.write_text("\n".join(content + [""]))


def build(setup_kwargs: Dict[str, Any]):
    write_metadata(setup_kwargs)
