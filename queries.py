import json
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from utils import flatten
from models import Product, Launch, Info, Availability


def has_size(avail: Availability, sizes: list[str]):
    """returns True if at least one size in sizes is available"""
    avail_skus = avail.avail_skus

    if not isinstance(avail_skus, str):
        return False

    avail_skus = json.loads(avail_skus)
    levels = [avail_skus.get(size) for size in sizes]
    if not any([level != "OOS" for level in levels if level is not None]):
        return False

    return True


def is_available(
    p: Product, idx: int = -1, sizes: list[str] = [], restricted: bool = False
):
    if len(p.availability) < abs(idx):
        return False

    avail = p.availability[idx]
    if sizes and not has_size(avail, sizes):
        return False

    launch_date = get_launch_date(p)
    return all(
        [
            avail.status == "ACTIVE",
            avail.available,
            avail.restricted if restricted else not avail.restricted,
            avail.included_in_last_update,
            launch_date <= datetime.now(),
        ]
    )


def get_last_change_date(p: Product) -> datetime:
    last_update_ts = max(
        p.info[-1].timestamp, p.availability[-1].timestamp, p.launch[-1].timestamp
    )
    return datetime.fromtimestamp(last_update_ts)


def get_launch_date(p: Product) -> datetime:
    """
    products with publish_type==LAUNCH have start_entry_date.
    products with publish_type==FLOW have commerce_start_date.

    returns:
    the relevant date.
    """
    l: Launch = p.launch[-1]
    ts = l.start_entry_date or l.commerce_start_date
    assert isinstance(ts, int)
    return datetime.fromtimestamp(ts)


def get_launch_method(p: Product) -> str:
    """
    products with publish_type==LAUNCH have method==LEO|DAN.
    products with publish_type==FLOW have method==None.

    returns:
    either "LEO", "DAN", or "FLOW"
    """
    l: Launch = p.launch[-1]
    method = l.method or l.publish_type
    # method = method or ""
    assert isinstance(method, str)
    return method


def filter_hidden_products(products: list[Product]) -> list[Product]:
    hidden = [
        json.loads(p.availability[-1].hide_from_upcoming)
        for p in products
        if p.availability[-1].hide_from_upcoming
    ]
    hidden = set(flatten([[p["styleColor"] for p in h] for h in hidden]))

    return [p for p in products if p.info[-1].style_color in hidden]


def query_all_available_products(session: Session) -> list[Product]:
    products: list[Product] = session.query(Product).all()
    products = [p for p in products if p.info[-1].product_type == "FOOTWEAR"]
    products = [p for p in products if is_available(p, restricted=False)]
    return products


def query_restricted_products(session: Session) -> list[Product]:
    """restricted is not necessarily the same as exclusive assess"""
    products: list[Product] = session.query(Product).all()
    products = [p for p in products if is_available(p, restricted=True)]
    return products


def query_hidden_products(session: Session) -> list[Product]:
    products = query_all_available_products(session)
    products = filter_hidden_products(products)
    return products


def query_product_by_product_id(session: Session, product_id: int) -> Product:
    product = session.query(Product).filter(Product.id == product_id).first()
    assert product is not None

    return product


def query_product_by_style_color(
    session: Session, style_color: str
) -> Optional[Product]:
    product = (
        session.query(Product)
        .join(Info)
        .group_by(Info.product_id)
        .having(func.max(Info.timestamp))
        .where(Info.style_color == style_color)
        .first()
    )

    return product


def query_products_by_style_color(
    session: Session, style_colors: list[str]
) -> list[Product]:
    product = (
        session.query(Product)
        .join(Info)
        .group_by(Info.product_id)
        .having(func.max(Info.timestamp))
        .filter(Info.style_color.in_(style_colors))
        .all()
    )

    return product


if __name__ == "__main__":
    from database import get_session
    from watchlist import should_notify
    from utils import read_json

    watchlist = read_json("watchlist.json")

    sku = "DM0807-400"
    all_changes = {"add": [], "launch": [], "discontinued": [], "availability": [13]}

    with get_session() as session:
        notify = should_notify(session, watchlist, all_changes)
        print("notification list: ", notify)

        # p = query_product_by_product_id(session, 13)
        # avail = is_available(p, idx=-6, sizes=[])
        # name = p.info[-1].title
        # url = p.info[-1].im_url
        # print(name, avail, url, p.info[-1].style_color)
        # # print(products)
