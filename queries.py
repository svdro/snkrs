import json
from datetime import datetime 
from sqlalchemy.orm import Session

from utils import flatten
from models import Product, Launch

def is_available(p: Product, exclusive_access: bool=False):
    avail = p.availability[-1]
    launch_date = get_launch_date(p)
    return all([ 
            avail.status == "ACTIVE", 
            avail.available,
            avail.restricted if exclusive_access else not avail.restricted ,
            avail.included_in_last_update,
            launch_date <= datetime.now()
            ])

def get_last_change_date(p: Product) -> datetime:
    last_update_ts = max(p.info[-1].timestamp, p.availability[-1].timestamp, p.launch[-1].timestamp)
    return datetime.fromtimestamp(last_update_ts)

def get_launch_date(p: Product) -> datetime:
    """ 
    products with publish_type==LAUNCH have start_entry_date.
    products with publish_type==FLOW have commerce_start_date.

    return the relevant date.
    """
    l: Launch = p.launch[-1]
    ts =  l.start_entry_date or l.commerce_start_date
    assert isinstance(ts, int)
    return datetime.fromtimestamp(ts)

def get_launch_method(p: Product) -> str:
    """ 
    products with publish_type==LAUNCH have method==LEO|DAN.
    products with publish_type==FLOW have method==None.

    return either LEO, DAN, or FLOW
    """
    l: Launch = p.launch[-1]
    method = l.method or l.publish_type
    # method = method or ""
    assert isinstance(method, str)
    return method

def filter_hidden_products(products: list[Product]) -> list[Product]:
    hidden = [json.loads(p.availability[-1].hide_from_upcoming)
            for p in products if p.availability[-1].hide_from_upcoming]
    hidden = set(flatten([[p["styleColor"] for p in h] for h in hidden]))

    return [p for p in products if p.info[-1].style_color in hidden]

def query_all_available_products(session: Session) -> list[Product]:
    products: list[Product] = session.query(Product).all()
    products = [p for p in products if is_available(p, False)]
    return products

def query_restricted_products(session:Session) -> list[Product]:
    """ restricted is not necessarily the same as exclusive assess """
    products: list[Product] = session.query(Product).all()
    products = [p for p in products if is_available(p, True)]
    return products

def query_hidden_products(session: Session):
  products = query_all_available_products(session)
  products = filter_hidden_products(products)
  return products

def query_product_by_product_id(session: Session, product_id: int):
  product = session.query(Product).filter(Product.id==product_id).first()
  assert product is not None

  return product


if __name__ == "__main__":
    from database import get_session

    # session: Session = get_session()

    with get_session() as session:
        # products = query_all_available_products(session)
        products: list[Product] = session.query(Product).all()
        print(len(products))
        for p in products:
            method = get_launch_method(p)
            date = get_launch_date(p)
            print(method, date)
