import re

DOCS_URL = "https://core.telegram.org/bots/api"

RE_FLAGS = re.IGNORECASE
ANCHOR_HEADER_PATTERN = re.compile(r"^h([34])$")
RETURN_PATTERNS = [
    re.compile(r"(?P<type>Array of [a-z]+) objects", flags=RE_FLAGS),
    re.compile(r"a (?P<type>[a-z]+) object", flags=RE_FLAGS),
    re.compile(r"Returns (?P<type>[a-z]+) on success", flags=RE_FLAGS),
    re.compile(r"(?P<type>[a-z]+) on success", flags=RE_FLAGS),
    re.compile(
        r"(?P<type>[a-z]+) is returned, otherwise (?P<other>[a-zA-Z]+) is returned", flags=RE_FLAGS
    ),
    re.compile(
        r"returns the edited (?P<type>[a-z]+), otherwise returns (?P<other>[a-zA-Z]+)",
        flags=RE_FLAGS,
    ),
    re.compile(r"(?P<type>[a-z]+) is returned", flags=RE_FLAGS),
    re.compile(r"Returns (?P<type>[a-z]+)", flags=RE_FLAGS),
]
BUILTIN_TYPES = {
    "String": "str",
    "Integer": "int",
    "Float": "float",
    "Boolean": "bool",
    "InputFile": "types.InputFile",
}
READ_MORE_PATTERN = re.compile(
    r" ((More info on|More about)([\W\w]+»)|»)", flags=re.MULTILINE & re.IGNORECASE
)
SYMBOLS_MAP = {"“": "'", "”": "'"}
