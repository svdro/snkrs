import queries

from typing import Any
from sqlalchemy.orm import Session
from models import Product


def has_become_available(p: Product, sizes: list[str], restricted: bool) -> bool:
    prev_available = queries.is_available(p, -2, sizes=sizes, restricted=restricted)
    curr_available = queries.is_available(p, -1, sizes=sizes, restricted=restricted)
    return not prev_available and curr_available


def should_notify(
    session: Session,
    watchlist: dict[str, dict[str, Any]],
    all_changes: dict[str, list[int]],
) -> list[Product]:
    """
    returns:
    a list of products that have become available in the most recent step.
    """
    skus = list(watchlist.keys())
    watched_products = queries.query_products_by_style_color(session, style_colors=skus)

    notify = []
    for p in watched_products:
        info = watchlist[p.info[-1].style_color]

        if p is None:
            continue

        if p.id in all_changes["availability"] or all_changes["add"]:
            is_notify_restricted = has_become_available(p, info.get("sizes", []), True)
            is_notify = has_become_available(p, info.get("sizes", []), False)
            if is_notify or (is_notify_restricted and info.get("include_restricted")):
                notify.append(p)

        if p.id in all_changes["launch"]:
            pass

    return notify
