import asyncio
import aiohttp

from typing import Any

NIKE_HEADERS = {
    "Accept-Encoding": "gzip, deflate",
    "User-Agent": "SNKRS-inhouse/4.26.0 (com.nike.onenikecommerce",
}

URL_TEMPLATE = "https://snkrs.services.nike.com/snkrs/content/v1/?anchor={}&language=fr&marketplace=FR&includeContentThreads=true&format=v5&exclusiveAccess=true%2Cfalse"


async def get_request(session: aiohttp.ClientSession, url: str) -> dict:
    async with session.get(url, headers=NIKE_HEADERS) as res:
        res.raise_for_status()
        return await res.json()


def flatten(list_of_dict: list[dict[str, dict]], key: str = "objects") -> list[dict]:
    new_list = []
    for d in list_of_dict:
        new_list += d[key]

    return new_list


def filter_out_duplicates(data: list):
    new_data, data_ids = [], []
    for d in data:
        if d["id"] not in data_ids:
            new_data.append(d)
            data_ids.append(d["id"])

    return new_data


async def crawl_product_and_content_infos() -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """ 
    Crawl_product_and_content_infos fetches nike's product feed, and does 
    some amount of preliminary data manipulation to get from nike's nested json 
    format to relatively simpler python dictionaries.

    returns:
    a list of (content_info, product_info ) tuples.
    """
    urls = [URL_TEMPLATE.format(i) for i in range(0, 200, 40)]
    # urls = [URL_TEMPLATE.format(i) for i in range(0, 200, 40)]

    async with aiohttp.ClientSession() as session:
        # request nike sneakers app content (feed).
        data_ = await asyncio.gather(*[get_request(session, url) for url in urls])

        # transform data_ into list in which each entry is a product card.
        data: list[dict] = flatten(list(data_), "objects")

        # get rid of duplicates, keep only cards that have "product info.
        data = filter_out_duplicates(data)
        data = [d for d in data if d.get("productInfo") is not None]

        ### return extract lists of productInfos and publishedContents from data.
        content_infos = [d["publishedContent"] for d in data for _ in range(len(d["productInfo"]))]
        product_infos =  [item for d in data for item in d["productInfo"]]

        infos = [(content_infos[i], product_infos[i]) for i in range(len(product_infos))]

        return infos
