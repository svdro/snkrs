from pprint import pprint
import asyncio

from parse import parse_info
from crawl import crawl_product_and_content_infos

async def main():
    infos = await crawl_product_and_content_infos()
    infos = [parse_info(*info) for info in infos]


    for info in infos:
        if info["exclusiveAccess"]:
            print("\n")
            pprint(info)



if __name__ == "__main__":
    asyncio.run(main())
