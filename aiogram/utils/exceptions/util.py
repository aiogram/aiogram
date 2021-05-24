def mark_line(text: str, offset: int, length: int = 1) -> str:
    try:
        if offset > 0 and (new_line_pos := text[:offset].rindex("\n")):
            text = "..." + text[:new_line_pos]
            offset -= new_line_pos - 3
    except ValueError:
        pass

    if offset > 10:
        text = "..." + text[offset - 10 :]
        offset = 13

    mark = " " * offset
    mark += "^" * length
    try:
        if new_line_pos := text[len(mark) :].index("\n"):
            text = text[:new_line_pos].rstrip() + "..."
    except ValueError:
        pass
    return text + "\n" + mark
