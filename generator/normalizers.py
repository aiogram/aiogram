import functools

from generator.consts import BUILTIN_TYPES, RETURN_PATTERNS, READ_MORE_PATTERN, SYMBOLS_MAP


def normalize_description(text: str) -> str:
    for bad, good in SYMBOLS_MAP.items():
        text = text.replace(bad, good)
    text = READ_MORE_PATTERN.sub("", text)
    text.strip()
    return text


def normalize_annotation(item: dict):
    for key in list(item.keys()):
        item[key.lower()] = item.pop(key)

    item["description"] = normalize_description(item["description"])


def normalize_method_annotation(item: dict):
    normalize_annotation(item)
    item["required"] = {"Optional": False, "Yes": True}[item["required"]]
    item["name"] = item.pop("parameter")


def normalize_type_annotation(item: dict):
    normalize_annotation(item)

    item["name"] = item.pop("field")

    if item["description"].startswith("Optional"):
        item["required"] = False
        item["description"] = item["description"][10:]
    else:
        item["required"] = True


@functools.lru_cache()
def normalize_type(string, required=True):
    if not string:
        return "typing.Any"

    union = "typing.Union" if required else "typing.Optional"

    lower = string.lower()
    split = lower.split()

    if split[0] == "array":
        new_string = string[lower.index("of") + 2 :].strip()
        return f"typing.List[{normalize_type(new_string)}]"
    if "or" in split:
        split_types = string.split(" or ")
        norm_str = ", ".join(map(normalize_type, map(str.strip, split_types)))
        return f"{union}[{norm_str}]"
    if "number" in lower:
        return normalize_type(string.replace("number", "").strip())
    if lower in ["true", "false"]:
        return "bool"
    if string not in BUILTIN_TYPES and string[0].isupper():
        return f"types.{string}"
    elif string in BUILTIN_TYPES:
        return BUILTIN_TYPES[string]
    return "typing.Any"


@functools.lru_cache()
def get_returning(description):
    parts = list(filter(lambda item: "return" in item.lower(), description.split(".")))
    if not parts:
        return "typing.Any", ""
    sentence = ". ".join(map(str.strip, parts))
    return_type = None

    for pattern in RETURN_PATTERNS:
        temp = pattern.search(sentence)
        if temp:
            return_type = temp.group("type")
            if "other" in temp.groupdict():
                otherwise = temp.group("other")
                return_type += f" or {otherwise}"
        if return_type:
            break

    return return_type, sentence + "."
