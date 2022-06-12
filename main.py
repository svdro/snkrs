# from psys.stdout.write import pprint
import sys
import asyncio


from datetime import datetime
from collections import defaultdict
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from parse import parse_info
from crawl import crawl_product_and_content_infos
from models import Product, Info, Launch, Availability
from database import get_session

def update_db(session: Session, product_dict: dict[str, Any]) -> dict[str, bool]:
    """ 
    update_db compares a product update's pid with existing Product entries in 
    the database. If there is no existing matching product, a new Product is added 
    to the database. If any value belonging to "launch", "info", or "availability" has 
    changed, a new entry will be added/appended to the corresponding table.

    returns:
    a dict that indicates which updates have been performed.
    """
    changes = {"add": False, "info": False, "launch": False, "availability": False}

    p_new = Product.from_dict(product_dict)
    p_old = session.query(Product).filter_by(pid=product_dict["pid"]).first()

    if p_old is None:
        session.add(p_new)
        session.commit()
        changes["add"] = True
        return changes

    if all(
        (
            p_old.info[-1] == p_new.info[-1],
            p_old.launch[-1] == p_new.launch[-1],
            p_old.availability[-1] == p_new.availability[-1],
        )
    ):
        return changes

    if p_old.info[-1] != p_new.info[-1]:
        info = Info.from_dict(product_dict)
        p_old.info.append(info)
        changes["info"] = True

    if p_old.launch[-1] != p_new.launch[-1]:
        launch = Launch.from_dict(product_dict)
        p_old.launch.append(launch)
        changes["launch"] = True

    if p_old.availability[-1] != p_new.availability[-1]:
        availability = Availability.from_dict(product_dict)
        p_old.availability.append(availability)
        changes["availability"] = True

    session.commit()
    return changes


def handle_discontinued_products(session: Session, pids: list[int]) -> int:
    """
    Sometimes products disappear from feed.
    Find out if and which products Nike took out of their content updates,
    and update their availability accordingly.

    returns:
    the number of products missing from the most recent update.
    """

    # find all products joined with their last available availability status.
    products = session \
        .query(Product.pid, Availability.included_in_last_update) \
        .join(Availability) \
        .group_by(Availability.product_id) \
        .having(func.max(Availability.timestamp)) \
        .all()


    # keep only pids where product id was included in the last update.
    pids_old = set([p[0] for p in products if p[1] == 1])
    pids_: set[int] = set(pids)
    insec = pids_.intersection(pids_old)
    pids_left_over = pids_old - insec

    # update Product/Availability tables for discontinued product_ids.
    for pid in pids_left_over:
        p_old = session.query(Product).filter_by(pid=pid).first()
        assert(p_old is not None) # to make LSP happy
        p_old.availability.append(Availability.from_scratch())
    session.commit()

    return len(pids_left_over)


async def step():
    infos = await crawl_product_and_content_infos()
    product_dicts = [parse_info(*info) for info in infos]

    # keeps track of all changes made to db.
    all_changes = defaultdict(int) 
    with get_session() as session:
        # find discontinued products and update availability in db.
        n = handle_discontinued_products(session, [int(p["pid"]) for p in product_dicts])
        all_changes["discontinued"] += n



        pids = []
        for product_dict in product_dicts:
            # ignore duplicates
            pid = product_dict["pid"]
            if pid in pids:
                continue

            pids.append(pid)
            changes = update_db(session, product_dict)
            for k, v in changes.items():
                all_changes[k] += int(v)



    # msg = ".join([f"{k}: {v}" for k, v in all_changes.items()])
    msg = ", ".join([f"{k}: {v}" for k, v in all_changes.items()])
    msg = f'{datetime.now().strftime("%H:%M:%S")} -- {msg}'
    sys.stdout.write(f"\n{msg}\n")
    sys.stdout.flush()

async def main():
    await step()

if __name__ == "__main__":
    asyncio.run(main())
