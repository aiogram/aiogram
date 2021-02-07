import re
from pathlib import Path

import toml

BASE_PATTERN = r'({variable} = ")[a-z0-9.+]+(")'
PACKAGE_VERSION = re.compile(BASE_PATTERN.format(variable="__version__"))
API_VERSION = re.compile(BASE_PATTERN.format(variable="__api_version__"))

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
    path = Path.cwd() / ".apiversion"
    version = path.read_text().strip()
    return version


def replace_line(content: str, pattern: re.Pattern, new_value: str) -> str:
    return pattern.sub(f"\\g<1>{new_value}\\g<2>", content)


def write_package_meta(package_version: str, api_version: str) -> None:
    path = Path.cwd() / "aiogram" / "__init__.py"
    content = path.read_text()

    content = replace_line(content, PACKAGE_VERSION, package_version)
    content = replace_line(content, API_VERSION, api_version)

    print(f"Write {path}")
    path.write_text(content)


def write_docs_meta(package_version: str, api_version: str) -> None:
    api_meta = Path.cwd() / "docs" / "_api_version.md"
    package_meta = Path.cwd() / "docs" / "_package_version.md"

    print(f"Write {api_meta}")
    api_meta.write_text(api_version + "\n")
    print(f"Write {package_meta}")
    package_meta.write_text(package_version + "\n")


def main():
    package_version = get_package_version()
    api_version = get_telegram_api_version()

    print(f"Package version: {package_version}")
    print(f"Telegram Bot API version: {api_version}")
    write_package_meta(package_version=package_version, api_version=api_version)
    write_docs_meta(package_version=package_version, api_version=api_version)


if __name__ == "__main__":
    main()
