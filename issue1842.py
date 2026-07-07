import signal
import time

from aiogram import __version__
from aiogram.types import Update


class _T(Exception):
    pass


def _h(s, f):
    raise _T()


signal.signal(signal.SIGALRM, _h)


def nested_blocks(depth):
    root = {"type": "blockquote", "blocks": []}
    node = root
    for _ in range(depth):
        child = {"type": "blockquote", "blocks": []}
        node["blocks"].append(child)
        node = child
    return [root]


def make_update(depth):
    return {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "date": 0,
            "chat": {"id": 1, "type": "private"},
            "from": {"id": 1, "is_bot": False, "first_name": "x"},
            "rich_message": {"blocks": nested_blocks(depth)},
        },
    }


print("aiogram", __version__)
for depth in [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 50]:
    upd = make_update(depth)
    signal.setitimer(signal.ITIMER_REAL, 20)  # abort a single validation after 20s
    start = time.perf_counter()
    try:
        u: Update = Update.model_validate(upd)
        # print(u.message.rich_message.blocks)
    except _T:
        print(f"depth={depth:5d}  >20s  TIMEOUT (hang)")
        break
    signal.setitimer(signal.ITIMER_REAL, 0)
    print(f"depth={depth:5d}  {time.perf_counter() - start:.8f}s")
