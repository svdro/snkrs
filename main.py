import sys
import asyncio

from collections import defaultdict

import tgram
from datetime import datetime
from transactions import update_db, handle_discontinued_products
from parse import parse_info
from crawl import crawl_product_and_content_infos
from database import get_session


async def step():
    # crawl and parse
    infos = await crawl_product_and_content_infos()
    product_dicts = [parse_info(*info) for info in infos]

    # keeps track of all changes made to db.
    all_changes = defaultdict(list) 
    all_changes = {"discontinued": [], "availability": [], "launch": [], "info": [], "add": []}
    with get_session() as session:
        # find discontinued products and update availability in db.
        discontinued = handle_discontinued_products(session, [int(p["pid"]) for p in product_dicts])
        if discontinued:
            all_changes["discontinued"] += discontinued

        # update db 
        pids = []
        for product_dict in product_dicts:
            # ignore duplicates
            pid = product_dict["pid"]
            if pid in pids:
                continue
            pids.append(pid)

            changes = update_db(session, product_dict)
            for k, v in changes.items():
                all_changes[k].append(v)

        # alarm and notifications.
        await tgram.dispatch_alarm(all_changes)


        # dispatch messages
        if any(all_changes.values()):
            sys.stdout.write("\n" + " || ".join([f"{k}: {v}" for k , v in all_changes.items()]) + "\n")

async def answer_ping():
    for sub in tgram.subscriptions.values():
        assert  isinstance(sub.queue, asyncio.Queue)
        while not sub.queue.empty():
            v = await sub.queue.get()
            print("received value from queue: ", v, " -> ",  sub.queue.empty())
            sub.queue.task_done()

async def loop(throttle_sec: int=10, throttle_sec_on_error: int=60):
    _throttle_sec = 0

    while True:
        await asyncio.sleep(_throttle_sec)
        await answer_ping()

        try:
            await step()
            sys.stdout.write(f'{datetime.now().strftime("%H:%M:%S")}: slept for {_throttle_sec} seconds.\n')
        except Exception as e:
            sys.stdout.write(f"\nreceived error:\n{e}\n")
            _throttle_sec = throttle_sec_on_error
            await tgram.dispatch_to_admin(f"received exception:\n{e}")
        sys.stdout.flush()

        _throttle_sec = throttle_sec

def main():
    asyncio.ensure_future(loop())
    tgram.application.run_polling()

if __name__ == "__main__":
    main()
