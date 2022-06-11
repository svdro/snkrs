import math
import json

from datetime import datetime, timedelta
from typing import Any

MERCH_KEYS = [
    "brand",
    "publishType",
    "modificationDate",
    "commercePublishDate",
    "commerceStartDate",
    "commerceEndDate",
    "softLaunchDate",
    "exclusiveAccess",
    "hardLaunch",
    "status",
    "id",
    "styleColor",
    "quantityLimit",
    "hideFromCSR",
    "hideFromSearch",
    "productType",
    "pid",
    "genders",
    "im_url",
]

# Nike time strings are in UTC time. Need to now diff to get accurate timestamp.
time_delta = datetime.now() - datetime.utcnow()
time_delta = timedelta(minutes = math.ceil(time_delta.seconds / 60))

def parse_nike_time(time_str: str) -> int:
    """
    Nike time strings are in UTC time. This needs to be accounted for 
    when server time is different. Returns timestamp in seconds.
    """
    dt = datetime.strptime(time_str[:-1], "%Y-%m-%dT%H:%M:%S.%f")
    return int((dt + time_delta).timestamp())


def parse_launchView(info: dict[str, Any]) -> dict[str, Any]:
    """
    launch View is only available when publish type is "LAUNCH"
    rather than "FLOW".
    """
    lv = info.get("launchView")
    if lv is None:
        return {"start_entry_date": None, "method": None}

    ts = parse_nike_time(lv["startEntryDate"])
    return {"start_entry_date": ts, "method": lv["method"]}


def parse_available_skus(info: dict[str, Any]) -> dict[str, str]:
    available_skus = info.get("availableSkus")
    skus = info.get("skus")

    if available_skus is None or skus is None:
        return {}

    return {k["nikeSize"]: v["level"] for k, v in zip(skus, available_skus)}

def parse_content_info(content_info: dict[str, Any]) -> dict[str, Any]:
    hide_from_upcoming = content_info["properties"]["custom"].get("hideFromUpcoming")
    hide_from_upcoming = json.dumps(hide_from_upcoming) if hide_from_upcoming else None
    return {
            "restricted": content_info["properties"]["custom"].get("restricted"),
            "hide_from_upcoming": hide_from_upcoming,
            "countries": json.dumps(content_info["properties"]["publish"]["countries"]),
            "title_alt": content_info["properties"]["title"],
    }


def parse_info(content_info: dict[str, Any], product_info: dict[str, Any]):
    mp = product_info["merchProduct"]

    info = {k: mp.get(k) for k in MERCH_KEYS}
    info.update(
        {
            k: parse_nike_time(v)
            for k, v in info.items()
            if "Date" in k and v is not None
        }
    )
    info.update(parse_launchView(product_info))
    info.update(parse_content_info(content_info))

    info["title"] = product_info["productContent"]["title"]
    info["available"] = product_info["availability"]["available"]
    info["im_url"] = product_info["imageUrls"]["productImageUrl"]

    info["avail_skus"] = json.dumps(parse_available_skus(product_info))

    return info
