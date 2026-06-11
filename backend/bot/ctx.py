import os
from collections import defaultdict

MAX_TURNS = int(os.getenv("MAX_HISTORY_TURNS", "5"))

_history: dict[str, list] = defaultdict(list)


def get_history(user_id: str) -> list:
    return list(_history[user_id])


def add_exchange(user_id: str, user_msg: str, assistant_msg: str):
    _history[user_id].append({"role": "user", "content": user_msg})
    _history[user_id].append({"role": "assistant", "content": assistant_msg})
    if len(_history[user_id]) > MAX_TURNS * 2:
        _history[user_id] = _history[user_id][-MAX_TURNS * 2:]


def clear_history(user_id: str):
    _history[user_id] = []
