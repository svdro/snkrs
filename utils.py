import os, json
from typing import Any

def flatten(list_of_lists: list[list[Any]]) -> list[Any]:
    return [item for sublist in list_of_lists for item in sublist]

def read_token(path: str = ".credentials.json") -> str:
    if os.path.exists(path):
        with open(path, "r") as f:
            creds= json.load(f)
            return creds["token"]

    raise FileNotFoundError(f"path does not exist")

