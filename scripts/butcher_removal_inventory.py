"""Write the 4.0 removal inventory: every field and type that 3.x marks deprecated.

Reads ``.butcher/**/entity.json`` directly (no butcher). Throwaway PD-10 tooling for C-26; it
writes no registry entries (3x-23 does).
Usage: ``python scripts/butcher_removal_inventory.py --out <file>``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUTCHER = ROOT / ".butcher"
DEFAULT_OUT = ROOT / "aiogram" / "_migration" / "data" / "removal_inventory_3x.json"

# Replacement where the Bot API changelog names one; everything else stays null (unknown).
FIELD_REPLACEMENTS = {
    "allow_sending_without_reply": "reply_parameters",
    "reply_to_message_id": "reply_parameters",
    "disable_web_page_preview": "link_preview_options",
    "request_user": "request_users",
    "user_shared": "users_shared",
}
FORWARD_FIELDS = {
    "forward_date",
    "forward_from",
    "forward_from_chat",
    "forward_from_message_id",
    "forward_sender_name",
    "forward_signature",
}
ENTITY_REPLACEMENTS = {
    "KeyboardButtonRequestUser": "KeyboardButtonRequestUsers",
    "UserShared": "UsersShared",
}


def _replacement(entity: str, kind: str, name: str | None) -> str | None:
    if kind == "types" and name is None:
        return ENTITY_REPLACEMENTS.get(entity)
    if entity == "Chat" and kind == "types":
        return "ChatFullInfo"
    if name in FORWARD_FIELDS:
        return "forward_origin"
    return FIELD_REPLACEMENTS.get(name)  # type: ignore[arg-type]


def build() -> list[dict[str, str | None]]:
    records: list[dict[str, str | None]] = []
    for path in sorted(BUTCHER.glob("*/*/entity.json")):
        kind = path.parent.parent.name
        data = json.loads(path.read_text(encoding="utf-8"))
        entity = data["object"]["name"]
        if kind == "methods":
            entity = entity[0].upper() + entity[1:]  # the Python class, e.g. SendMessage
        if "deprecated" in data.get("meta", {}):
            records.append(
                {
                    "entity": entity,
                    "kind": "type",
                    "field": None,
                    "removed_in": data["meta"]["deprecated"]["version"],
                    "replacement": _replacement(entity, kind, None),
                }
            )
        records.extend(
            {
                "entity": entity,
                "kind": "method" if kind == "methods" else "type",
                "field": ann["name"],
                "removed_in": ann["deprecated"]["version"],
                "replacement": _replacement(entity, kind, ann["name"]),
            }
            for ann in data["object"].get("annotations", [])
            if "deprecated" in ann
        )
    records.sort(key=lambda r: (r["entity"], r["field"] or ""))  # type: ignore[arg-type,return-value]
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    text = json.dumps({"schema": 1, "records": build()}, indent=2, ensure_ascii=False) + "\n"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
