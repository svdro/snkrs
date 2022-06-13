# from psys.stdout.write import pprint
# import sys
import asyncio

# from datetime import datetime
from collections import defaultdict

# from tgram import application, subscriptions, dispatch_notifications
import tgram
from transactions import update_db, handle_discontinued_products
from parse import parse_info
from crawl import crawl_product_and_content_infos
from database import get_session


async def step():
    # raise ValueError("oh no error")
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

        return all_changes

async def answer_ping():
    for queue in tgram.subscriptions.values():
        assert  isinstance(queue, asyncio.Queue)
        while not queue.empty():
            v = await queue.get()
            print("received value from queue: ", v, " -> ",  queue.empty())
            queue.task_done()

async def loop():
    i = 0
    while True:
        i += 1
        await answer_ping()

        # all_changes, _ = await asyncio.gather(step(), asyncio.sleep(10))
        try:
            all_changes = await step()
        except Exception as e:
            print("exception: ")
            print(e)
            await asyncio.sleep(10)
            continue

        print(all_changes)

        # dispatch messages
        if any(all_changes.values()) or i == 3:
            text = str(all_changes)
            await tgram.dispatch_notifications(text)
            # await asyncio.gather(*[bot.send_message(chat_id = chat_id, text=text) for chat_id in subscriptions])
        await asyncio.sleep(5)


def main():
    # application = init_application()
    asyncio.ensure_future(loop())
    tgram.application.run_polling()
    # await loop()


if __name__ == "__main__":
    main()
