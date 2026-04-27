import os
import logging
import datetime
import asyncio
import yfinance as yf
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.error import BadRequest
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# --- Logging ---
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Variables ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
MY_CHAT_ID = os.getenv("MY_CHAT_ID")
TOPIC_ID = os.getenv("TOPIC_ID") # លេខ Topic ឧទាហរណ៍: 3

async def fetch_gold_data():
    try:
        gold = yf.Ticker("GC=F") # ប្រើ Yahoo Finance មិនជាប់ Block
        df = gold.history(period="2d", interval="1h")
        return df if not df.empty else None
    except Exception as e:
        logger.error(f"Data Fetch Error: {e}")
        return None

async def send_report(context: ContextTypes.DEFAULT_TYPE, is_alert=False):
    df = await fetch_gold_data()
    if df is None: return

    price = round(df["Close"].iloc[-1], 2)
    report = (
        "🏦 *E11 INTELLIGENCE — XAUUSD*\n"
        f"🕐 {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"💰 PRICE: *${price}*\n"
        "🎯 SIGNAL: ⏳ WAIT"
    )

    # កំណត់ Topic: បើ Alert ឱ្យចូល Topic 3 បើធម្មតាចូល Topic ID ដែលមេមាន
    thread_id = 3 if is_alert else TOPIC_ID
    
    try:
        await context.bot.send_message(
            chat_id=MY_CHAT_ID,
            text=report,
            message_thread_id=thread_id,
            parse_mode="Markdown"
        )
    except BadRequest as e:
        logger.warning(f"Thread error ({e}), sending to main chat.")
        await context.bot.send_message(chat_id=MY_CHAT_ID, text=report, parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Bot is Online!")

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_report(context)

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Scheduler សម្រាប់ Alert ទៅ Topic 3 រៀងរាល់ម៉ោង
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_report, 'interval', hours=1, args=[app, True])
    scheduler.start()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", report_command))

    logger.info("Bot is running...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
    
