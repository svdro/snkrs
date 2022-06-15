import os, json
from typing import Any

def flatten(list_of_lists: list[list[Any]]) -> list[Any]:
    return [item for sublist in list_of_lists for item in sublist]

def read_token(path: str = ".credentials.json") -> tuple[str, str]:
    """ returns: (token, admin_chat_id) """
    if os.path.exists(path):
        with open(path, "r") as f:
            creds= json.load(f)
            return creds["token"], creds["chat_id"]

    raise FileNotFoundError(f"path does not exist")

