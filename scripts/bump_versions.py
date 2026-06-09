import json
import re
from pathlib import Path

import toml

BASE_PATTERN = r'({variable} = ").+(")'
PACKAGE_VERSION = re.compile(BASE_PATTERN.format(variable="__version__"))
API_VERSION = re.compile(BASE_PATTERN.format(variable="__api_version__"))
API_VERSION_BADGE = re.compile(r"(API-)[\d.]+(-blue\.svg)")
API_VERSION_LINE = re.compile(
    r"(Supports `Telegram Bot API )[\d.]+( <https://core\.telegram\.org/bots/api>`_ )"
)

STAGE_MAPPING = {
    "alpha": "a",
    "beta": "b",
}


def get_package_version() -> str:
    data = toml.load(Path("pyproject.toml").absolute())
    raw_version: str = data["tool"]["poetry"]["version"]
    if "-" not in raw_version:
        return raw_version

    version, stage_build = raw_version.split("-", maxsplit=1)
    if stage_build:
        stage, build = stage_build.split(".")
        if stage_str := STAGE_MAPPING.get(stage):
            version += f"{stage_str}{build}"
        else:
            return raw_version

    return version


def get_telegram_api_version() -> str:
    path = Path.cwd() / ".butcher" / "schema" / "schema.json"
    schema = json.loads(path.read_text())
    version = schema["api"]["version"]
    path = Path.cwd() / ".apiversion"
    path.write_text(version + "\n")
    return version


def replace_line(content: str, pattern: re.Pattern, new_value: str) -> str:
    return pattern.sub(f"\\g<1>{new_value}\\g<2>", content)


def write_package_meta(api_version: str) -> None:
    path = Path.cwd() / "aiogram" / "__meta__.py"
    content = path.read_text()

    content = replace_line(content, API_VERSION, api_version)

    print(f"Write {path}")  # noqa: T201
    path.write_text(content)


def write_readme(api_version: str) -> None:
    path = Path.cwd() / "README.rst"
    content = path.read_text()
    content = replace_line(content, API_VERSION_BADGE, api_version)
    content = replace_line(content, API_VERSION_LINE, api_version)
    print(f"Write {path}")  # noqa: T201
    path.write_text(content)


def write_docs_index(api_version: str) -> None:
    path = Path.cwd() / "docs" / "index.rst"
    content = path.read_text()
    content = replace_line(content, API_VERSION_BADGE, api_version)
    print(f"Write {path}")  # noqa: T201
    path.write_text(content)


def main():
    api_version = get_telegram_api_version()

    print(f"Telegram Bot API version: {api_version}")  # noqa: T201
    write_package_meta(api_version=api_version)
    write_readme(api_version=api_version)
    write_docs_index(api_version=api_version)


if __name__ == "__main__":
    main()
