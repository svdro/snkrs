import time
from typing import Any
from sqlalchemy import Column, Boolean, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base, engine


class Product(Base):
    __tablename__: str = "products"

    id = Column(Integer, primary_key=True, index=True)
    pid = Column(Integer, unique=True, index=True, nullable=False)
    info = relationship("Info", back_populates="product")
    launch = relationship("Launch", back_populates="product")
    availability = relationship("Availability", back_populates="product")

    def __repr__(self):
        return f"id: {self.id}, pid: {self.pid}, info ({len(self.info)}), launch ({len(self.launch)}), availability ({len(self.availability)})"

    @classmethod
    def from_dict(cls, x: dict[str, Any]):
        """ create a new Product instance from a key value mapping of all relevant data fields. """
        return cls(
            info=[Info.from_dict(x)],
            pid=x["pid"],
            launch=[Launch.from_dict(x)],
            availability=[Availability.from_dict(x)],
        )


class Info(Base):
    __tablename__: str = "info"

    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String)
    title = Column(String)
    title_alt = Column(String)
    brand = Column(String)
    style_color = Column(String)
    product_type = Column(String)
    countries = Column(String)
    genders = Column(String)
    im_url = Column(String)

    timestamp = Column(Integer)

    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product = relationship("Product", back_populates="info")

    def __eq__(self, other) -> bool:
        return all(
            (
                self.uid == other.uid,
                self.title == other.title,
                self.title_alt == other.title_alt,
                self.brand == other.brand,
                self.style_color == other.style_color,
                self.product_type == other.product_type,
                self.countries == other.countries,
                self.genders == other.genders,
                self.im_url == other.im_url,
            )
        )

    @classmethod
    def from_dict(cls, x: dict[str, Any]):
        return cls(
            uid=x["id"],
            title=x["title"],
            title_alt=x["title_alt"],
            brand=x["brand"],
            style_color=x["styleColor"],
            product_type=x["productType"],
            countries=x["countries"],
            genders=x["genders"],
            im_url=x["im_url"],
            timestamp=int(time.time()),
        )


class Launch(Base):
    __tablename__: str = "launch"

    id = Column(Integer, primary_key=True, index=True)

    publish_type = Column(String)
    method = Column(String)
    hard_launch = Column(Boolean)
    quantity_limit = Column(Integer)
    exclusive_access = Column(Boolean)

    modification_date = Column(Integer)
    commerce_start_date = Column(Integer)
    commerce_end_date = Column(Integer)
    commerce_publish_date = Column(Integer)
    soft_launch_date = Column(Integer)
    start_entry_date = Column(Integer)

    timestamp = Column(Integer)

    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product = relationship("Product", back_populates="launch")

    def __eq__(self, other) -> bool:
        return all(
            (
                self.publish_type == other.publish_type,
                self.method == other.method,
                self.hard_launch == other.hard_launch,
                self.quantity_limit == other.quantity_limit,
                self.exclusive_access == other.exclusive_access,

                self.modification_date == other.modification_date,
                self.commerce_start_date == other.commerce_start_date,
                self.commerce_end_date == other.commerce_end_date,
                self.commerce_publish_date == other.commerce_publish_date,
                self.soft_launch_date == other.soft_launch_date,
                self.start_entry_date == other.start_entry_date,
            )
        )

    @classmethod
    def from_dict(cls, x: dict[str, Any]):
        return cls(
            publish_type=x["publishType"],
            method=x["method"],
            hard_launch=x["hardLaunch"],
            quantity_limit=x["quantityLimit"],
            exclusive_access=x["exclusiveAccess"],

            modification_date=x["modificationDate"],
            commerce_start_date=x["commerceStartDate"],
            commerce_end_date=x["commerceEndDate"],
            commerce_publish_date=x["commercePublishDate"],
            soft_launch_date=x["softLaunchDate"],
            start_entry_date=x["start_entry_date"],
            timestamp=int(time.time()),
        )


class Availability(Base):
    __tablename__: str = "availability"

    id = Column(Integer, primary_key=True, index=True)
    included_in_last_update = Column(Boolean, nullable=False)

    available = Column(Boolean)
    status = Column(String)
    avail_skus = Column(String)
    hide_from_csr = Column(Boolean)
    hide_from_search = Column(Boolean)
    hide_from_upcoming = Column(String)
    restricted = Column(Boolean)

    timestamp = Column(Integer)

    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product = relationship("Product", back_populates="availability")

    def __eq__(self, other) -> bool:
        # if self.restricted != other.restricted:
        # import sys
        # sys.stdout.write(f"\n{type(self.restricted)}, {type(other.restricted)} -> {self.restricted}, {other.restricted}\n")
        # pass

        return all(
            (
                self.included_in_last_update == other.included_in_last_update,
                self.available == other.available,
                self.status == other.status,
                self.avail_skus == other.avail_skus,
                self.hide_from_csr == other.hide_from_csr,
                self.hide_from_search == other.hide_from_search,
                self.hide_from_upcoming == other.hide_from_upcoming,
                self.restricted == other.restricted,
            )
        )

    @classmethod
    def from_dict(cls, x: dict[str, Any]):
        return cls(
            included_in_last_update = True,
            available=x["available"],
            status=x["status"],
            avail_skus=x["avail_skus"],
            hide_from_csr=x["hideFromCSR"],
            hide_from_search=x["hideFromSearch"],
            hide_from_upcoming=x["hide_from_upcoming"],
            restricted=x["restricted"],
            timestamp=int(time.time()),
        )

    @classmethod
    def from_scratch(cls):
        return cls(
            included_in_last_update = False,
            timestamp=int(time.time()),
        )

Base.metadata.create_all(bind=engine)
