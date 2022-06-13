import asyncio
import json
import telegram
import telegram.constants

from telegram import Update
from telegram.ext import filters, ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler

from utils import read_token
from queries import  get_launch_date, get_launch_method
from models import Product
from database import get_session
from queries import query_all_available_products, query_hidden_products, query_product_by_product_id
from queries import query_restricted_products, get_last_change_date

token = read_token()
print("GOT TOKEN")

# subscriptions is a dict[chat_id: ping_queue]
subscriptions: dict[int, asyncio.Queue] = {}

keyboard = [
    ["/subscribe", "/unsubscribe"], 
    ["/available", "/hidden" ], 
    ["/exclusive_access", "/ping"]
]

application = ApplicationBuilder().token(token).build()

def get_chat_id(update: Update) -> int:
    """ utility to avoid lsp complaining """
    assert update.effective_chat is not None
    return update.effective_chat.id

def format_products_message(products: list[Product]) -> str:
    html = ""
    for p in products:
        title = p.info[-1].title
        html += f'\n<b>{title}</b> /pid_{p.id}'
    return html

async def dispatch_notifications(text: str):
    """ genereric function to dispatch notifications to all subscribed chats."""
    bot = application.bot
    await asyncio.gather(*[bot.send_message(chat_id = chat_id, text=text) for chat_id in subscriptions])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = telegram.ReplyKeyboardMarkup(keyboard)
    await context.bot.send_message( chat_id=get_chat_id(update), text="HI", reply_markup=reply_markup)

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = get_chat_id(update)

    text = "You are already subscribed!"
    if chat_id not in subscriptions:
        text = "You are now subscribed!"
        subscriptions[chat_id] = asyncio.Queue()

    await context.bot.send_message(chat_id=chat_id, text=text)

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = get_chat_id(update)
    chat_id = get_chat_id(update)

    if chat_id in subscriptions:
        subscriptions.pop(chat_id)

    text = "you are unsubscribed"
    await context.bot.send_message(chat_id=chat_id, text=text)

async def available(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with get_session() as session:
        products = query_all_available_products(session)
        html = "available:" +  format_products_message(products)
        html += f"\ntotal available: {len(products)}"
    await context.bot.send_message(chat_id=get_chat_id(update), text=html, parse_mode=telegram.constants.ParseMode.HTML, disable_web_page_preview=True)

async def hidden(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with get_session() as session:
        products = query_hidden_products(session)
        html = "hidden_products: " + format_products_message(products)
    await context.bot.send_message(chat_id=get_chat_id(update), text=html, parse_mode=telegram.constants.ParseMode.HTML, disable_web_page_preview=True)

async def restricted(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with get_session() as session:
        products = query_restricted_products(session)
        html = "exclusive access: " + format_products_message(products)
    await context.bot.send_message(chat_id=get_chat_id(update), text=html, parse_mode=telegram.constants.ParseMode.HTML, disable_web_page_preview=True)

def format_product_message(p: Product) -> str:
    html = f"<b>{p.info[-1].title}</b>"
    html += f"\n(<i>{p.info[-1].style_color}</i>)"
    html += f"\n{get_launch_method(p)}: {get_launch_date(p)}"
    html += f"\nlast change: {get_last_change_date(p)}"
    html += f'\n<a href="{p.info[-1].im_url}">url</a>'
    html += "\n"


    html += f"\navailable: {p.availability[-1].available}"
    html += f"\nstatus: {p.availability[-1].status}"

    html += f'\nskus:'

    skus = json.loads(p.availability[-1].avail_skus)
    for k, v in skus.items():
        html += f"\n\t\t{k}: {v}"

    return html

async def send_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = get_chat_id(update)

    if "/pid_" not in update.message.text:
        await context.bot.send_message(chat_id=chat_id, text=f'message "{update.message.text}" not supported')
        return

    pid = update.message.text.replace("/pid_", "")
    if not pid.isnumeric():
        await context.bot.send_message(chat_id=chat_id, text="you must specify a product_id")
        return

    with get_session() as session:
        p = query_product_by_product_id(session, int(pid))
        html = format_product_message(p)
    await context.bot.send_message(chat_id=chat_id, text=html, parse_mode=telegram.constants.ParseMode.HTML)


async def ping_loop(update: Update, context: ContextTypes.DEFAULT_TYPE ):
    """ 
    ping loop sends a message to the loop coroutine. As soon as the message 
    has been read, queue.join() will stop blocking and a "pong" message is 
    sent to the caller.
    """
    chat_id = get_chat_id(update)
    queue = subscriptions.get(chat_id)
    if queue is None:
        await context.bot.send_message(chat_id=chat_id, text="you need to be subscribed to ping")
        return

    # assert isinstance(queue, asyncio.Queue)
    async def wait_for_pong():
        try:
            await asyncio.wait_for(queue.join(), 30)
            await context.bot.send_message(chat_id=chat_id, text="pong")
        except Exception as e:
            print("timed out waiting for queue to join!\n", e)

    await queue.put("ping")
    asyncio.ensure_future(wait_for_pong())


handlers = {
        "start_handler": CommandHandler("start", start),
        "subscribe_handler": CommandHandler("subscribe", subscribe),
        "unsubscribe_handler": CommandHandler("unsubscribe", unsubscribe),
        "available_handler": CommandHandler("available", available),
        "hidden_handler": CommandHandler("hidden", hidden),
        "restricted_handler": CommandHandler("exclusive_access", restricted),
        "ping_handler": CommandHandler("ping", ping_loop),
        "view_product_handler": MessageHandler(filters.TEXT, send_product),
}

for handler in handlers.values():
    application.add_handler(handler)
