import os, json
from typing import Any


def flatten(list_of_lists: list[list[Any]]) -> list[Any]:
    return [item for sublist in list_of_lists for item in sublist]


def read_token(path: str = ".credentials.json") -> tuple[str, str]:
    """returns: (token, admin_chat_id)"""
    if os.path.exists(path):
        creds = read_json(path)
        return creds["token"], creds["chat_id"]

    raise FileNotFoundError(f"path does not exist")


def read_json(path: str):
    with open(path, "r") as f:
        return json.load(f)


if __name__ == "__main__":
    data = read_json("watchlist.json")
    for r in data:
        print(data[r], "\n")
