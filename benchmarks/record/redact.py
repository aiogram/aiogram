"""
Redact a recorded trace before it goes into the corpus.

Usage::

    uv run python -m benchmarks.record.redact RAW.jsonl -o benchmarks/corpus/traces/<id>.jsonl

What is replaced, consistently within one trace (the same input always maps to the same output):

- bot tokens become ``<pseudonymised bot id>:***``;
- user and chat ids (ints of five or more digits under ``id`` / ``*_chat_id`` / ``*_user_id``
  keys) become other numbers with the same sign and digit count, so text offsets stay valid; the
  same numbers are also replaced wherever they occur inside strings (``tg://user?id=…``);
- usernames become same-length placeholders, also as ``@mentions`` inside strings;
- phone numbers become same-length digit runs, also inside strings;
- first / last names, author signatures and chat titles become placeholders;
- numeric string ids (``id``, ``*_query_id``: callback / inline query ids embed the sender's user
  id) become same-length digit runs, matching between the update and the answering request;
- file ids and unique file ids become ``file-N`` / ``uniq-N``, also where a request passes one as a
  parameter value;
- e-mail addresses, vCards and invite links become ``<redacted>``; each distinct coordinate becomes
  a placeholder (0.001, 0.002, …), so a trace places nothing on a real map.

Message text is not rewritten beyond the above: review the output by hand before committing it.
"""

import argparse
import datetime
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

TOKEN_RE = re.compile(r"(?<!\d)(\d{5,}):[A-Za-z0-9_-]{30,}")
# One pass over free text, so a pseudonym is never looked up again as an original.
TEXT_RE = re.compile(
    r"(?<!\d)(?P<bot>\d{5,}):[A-Za-z0-9_-]{30,}"
    r"|@(?P<mention>[A-Za-z0-9_]{5,32})"
    r"|(?<!\d)(?P<sign>-?)(?P<num>\d{5,})(?!\d)"
)

ID_KEYS = {"id", "user_id", "chat_id"}
NAME_KEYS = {"first_name": "First", "last_name": "Last", "author_signature": "Author"}
FILE_KEYS = {
    "file_id": "file",
    "big_file_id": "file",
    "small_file_id": "file",
    "file_unique_id": "uniq",
    "big_file_unique_id": "uniq",
    "small_file_unique_id": "uniq",
}
SECRET_KEYS = {"email", "vcard", "invite_link"}
COORD_KEYS = {"latitude", "longitude"}
CHAT_TYPES = {"private", "group", "supergroup", "channel"}
MIN_ID = 10_000  # smaller ints under id keys are topic / story ids, not users or chats
CHANNEL_ID_DIGITS = 13  # "-100" + 10 digits: the -100 prefix is kept


def _is_id_key(key: str) -> bool:
    return key in ID_KEYS or key.endswith(("_chat_id", "_user_id"))


class Redactor:
    def __init__(self) -> None:
        self.numbers: dict[str, str] = {}
        self.usernames: dict[str, str] = {}
        self.strings: dict[tuple[str, str], str] = {}
        self._counters: Counter[str] = Counter()

    def _next(self, namespace: str) -> int:
        self._counters[namespace] += 1
        return self._counters[namespace]

    def number(self, digits: str) -> str:
        """Same sign, same length; a supergroup/channel ``-100`` prefix is kept."""
        if digits not in self.numbers:
            sign = "-" if digits.startswith("-") else ""
            body = digits.lstrip("-+")
            channel = sign and len(body) == CHANNEL_ID_DIGITS and body.startswith("100")
            prefix = "100" if channel else ""
            body = body[len(prefix) :]
            n = self._next(f"num:{sign}{prefix}{len(body)}")
            self.numbers[digits] = f"{sign}{prefix}{10 ** (len(body) - 1) + n}"
        return self.numbers[digits]

    def username(self, name: str) -> str:
        key = name.lower()
        if key not in self.usernames:
            n = str(self._next("username"))
            self.usernames[key] = "u" + n.zfill(len(name) - 1)
        return self.usernames[key]

    def string(self, namespace: str, value: str, template: str) -> str:
        key = (namespace, value)
        if key not in self.strings:
            self.strings[key] = template.format(self._next(namespace))
        return self.strings[key]

    # Pass 1: register every identifier so pass 2 can also find it inside free text.
    def collect(self, obj: Any, key: str = "") -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                self.collect(v, k)
        elif isinstance(obj, list):
            for v in obj:
                self.collect(v, key)
        elif isinstance(obj, bool):
            return
        elif isinstance(obj, int) and _is_id_key(key) and abs(obj) >= MIN_ID:
            self.number(str(obj))
        elif isinstance(obj, str):
            if key == "username":
                self.username(obj)
            elif key == "phone_number":
                self.number(obj.lstrip("+"))
            elif key in FILE_KEYS:
                self.string(FILE_KEYS[key], obj, FILE_KEYS[key] + "-{:06d}")
            elif (
                (key == "id" or key.endswith("_query_id")) and obj.isdigit() and int(obj) >= MIN_ID
            ):
                # Callback / inline query ids carry the sender's user id in their high 32 bits.
                self.number(obj)
            for match in TOKEN_RE.finditer(obj):
                self.number(match.group(1))

    # Pass 2: rewrite.
    def rewrite(self, obj: Any, key: str = "") -> Any:
        if isinstance(obj, dict):
            is_chat = obj.get("type") in CHAT_TYPES and "id" in obj
            return {
                k: (
                    self.string("title", v, "Chat {}")
                    if is_chat and k == "title" and isinstance(v, str)
                    else self.rewrite(v, k)
                )
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [self.rewrite(v, key) for v in obj]
        if isinstance(obj, bool):
            return obj
        if isinstance(obj, (int, float)) and key in COORD_KEYS:
            return float(self.string(key, str(obj), "0.{:03d}"))
        if isinstance(obj, int):
            return int(self.numbers.get(str(obj), obj))
        if not isinstance(obj, str):
            return obj
        if key in SECRET_KEYS:
            return "<redacted>"
        if key in NAME_KEYS:
            return self.string(key, obj, NAME_KEYS[key] + "{}")
        if key == "username":
            return self.username(obj)
        if key == "phone_number":
            return ("+" if obj.startswith("+") else "") + self.number(obj.lstrip("+"))
        for namespace in ("file", "uniq"):
            if (namespace, obj) in self.strings:
                return self.strings[namespace, obj]
        return self.text(obj)

    def text(self, value: str) -> str:
        return TEXT_RE.sub(self._text_match, value)

    def _text_match(self, match: re.Match[str]) -> str:
        if bot_id := match.group("bot"):
            return self.number(bot_id) + ":***"
        if mention := match.group("mention"):
            return "@" + self.usernames.get(mention.lower(), mention)
        sign, digits = match.group("sign"), match.group("num")
        if sign + digits in self.numbers:
            return self.numbers[sign + digits]
        return sign + self.numbers.get(digits, digits)


def redact_trace(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Redact a whole trace at once, so pseudonyms are stable across all of its records."""
    redactor = Redactor()
    for record in records:
        redactor.collect(record)
    result = [redactor.rewrite(record) for record in records]
    for record in result:
        if "provenance" in record:
            record["provenance"]["redacted"] = datetime.date.today().isoformat()  # noqa: DTZ011
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("source", type=Path, help="raw JSONL trace written by the recorder")
    parser.add_argument("-o", "--output", type=Path, required=True)
    args = parser.parse_args()

    lines = args.source.read_text(encoding="utf-8").splitlines()
    records = redact_trace([json.loads(line) for line in lines if line.strip()])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in records),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
