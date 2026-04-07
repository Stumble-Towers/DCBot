import json
import os
import asyncio

TOKEN_FILE = "tokens.json"

def _load_store() -> dict[str, str]:
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    return {}

def _save_store(store: dict[str, str]):
    with open(TOKEN_FILE, "w") as f:
        json.dump(store, f, indent=2)


def save_token(user_id: int, access_token: str):
    store = _load_store()
    store[str(user_id)] = access_token  # JSON keys must be strings
    _save_store(store)


async def get_token(user_id: int) -> str | None:
    store = _load_store()
    return store.get(str(user_id))