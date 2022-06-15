from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from models import Product, Info, Launch, Availability

def update_db(session: Session, product_dict: dict[str, Any]) -> dict[str, int]:
    """ 
    update_db compares a product update's pid with existing Product entries in 
    the database. If there is no existing matching product, a new Product is added 
    to the database. If any value belonging to "launch", "info", or "availability" has 
    changed, a new entry will be added/appended to the corresponding table.

    returns:
    a dict that indicates which product_ids (Product.id) have been updated.
    e.g: {"launch": 123, "availability": 123}
    """
    # changes = {"add": [], "info": [], "launch": [], "availability": []}
    changes = {}

    p_new = Product.from_dict(product_dict)
    p_old = session.query(Product).filter_by(pid=product_dict["pid"]).first()

    if p_old is None:
        session.add(p_new)
        session.commit()
        changes["add"] = p_new.id
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
        changes["info"] = p_old.id

    if p_old.launch[-1] != p_new.launch[-1]:
        launch = Launch.from_dict(product_dict)
        p_old.launch.append(launch)
        changes["launch"] = p_old.id

    if p_old.availability[-1] != p_new.availability[-1]:
        availability = Availability.from_dict(product_dict)
        p_old.availability.append(availability)
        changes["availability"] = p_old.id

    session.commit()
    return changes


def handle_discontinued_products(session: Session, pids: list[int]) -> list[int]:
    """
    Sometimes products disappear from feed.
    Find out if and which products Nike took out of their content updates,
    and update their availability accordingly.

    returns:
    a list of product_ids of discontinued products.
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
    discontinued_product_ids = []
    for pid in pids_left_over:
        p_old = session.query(Product).filter_by(pid=pid).first()
        assert(p_old is not None) # to make LSP happy
        p_old.availability.append(Availability.from_scratch())
        discontinued_product_ids.append(p_old.id)
    session.commit()

    return discontinued_product_ids
