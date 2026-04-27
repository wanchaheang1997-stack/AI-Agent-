import os
import logging
import datetime
import asyncio
import yfinance as yf
import pandas as pd
import numpy as np
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# --- ការកំណត់ Logging ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# --- ទាញយក Variable ពី Railway ---
BOT_TOKEN   = os.getenv("BOT_TOKEN")
MY_CHAT_ID  = os.getenv("MY_CHAT_ID")
TOPIC_ID    = os.getenv("TOPIC_ID")

# --- មុខងារទាញទិន្នន័យមាសឱ្យដូច TradingView ---
def fetch_live_gold_data():
    try:
        # 'GC=F' គឺជា Gold Futures ដែលតម្លៃវាដើរស្របគ្នាជាមួយ XAUUSD នៅលើ TradingView បំផុត
        gold = yf.Ticker("GC=F")
        # ទាញយកទិន្នន័យនាទីចុងក្រោយ (1m) ដើម្បីបានតម្លៃ Live
        data = gold.history(period="1d", interval="1m")
        if data.empty:
            return None
        return data
    except Exception as e:
        logger.error(f"Error fetching live data: {e}")
        return None

# --- មុខងារគណនា SMC/ICT (ដូចក្នុង TradingView Indicators) ---
def analyze_smc(df):
    latest_price = round(df["Close"].iloc[-1], 2)
    h1_high = round(df["High"].tail(60).max(), 2) # High ក្នុងរយៈពេល ៦០ នាទី
    h1_low = round(df["Low"].tail(60).min(), 2)   # Low ក្នុងរយៈពេល ៦០ នាទី
    
    # គណនា POC (Point of Control) បែបងាយ
    poc = round(df["Close"].tail(60).mean(), 2)
    
    return latest_price, h1_high, h1_low, poc

# --- មុខងារផ្ញើរបាយការណ៍ ---
async def build_report(bot, chat_id, topic_id=None):
    df = fetch_live_gold_data()
    if df is None:
        return

    price, h1_high, h1_low, poc = analyze_smc(df)
    now_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    
    report = (
        "🏦 *E11 INTELLIGENCE — XAUUSD*\n"
        f"🕐 {now_str}\n\n"
        "💰 *PRICE (LIVE)*\n"
        f"  Current : *${price}* ⚡\n"
        f"  H1 High : ${h1_high} | H1 Low : ${h1_low}\n\n"
        "📊 *MARKET PROFILE*\n"
        f"  POC Level : ${poc}\n\n"
        "🧠 *ICT STATUS*\n"
        "  Structure : Ranging\n"
        "  FVG Zone  : Monitoring...\n\n"
        "🎯 *SIGNAL*\n"
        "  ⏳ WAIT — No clear entry\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "E11 Sniper Bot • Live Data Feed"
    )

    kwargs = {"chat_id": chat_id, "text": report, "parse_mode": "Markdown"}
    if topic_id:
        kwargs["message_thread_id"] = int(topic_id)
    
    try:
        await bot.send_message(**kwargs)
        logger.info("Live Report Sent!")
    except Exception as e:
        logger.error(f"Failed to send message: {e}")

# --- Bot Commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 *E11 Sniper Bot (Railway Version) Is Online!*")

async def manual_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await build_report(context.bot, update.effective_chat.id, TOPIC_ID)

# --- Main Engine ---
async def main_async():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is missing!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # បង្កើត Scheduler ផ្ញើ Report ស្វ័យប្រវត្តិតាមម៉ោង (រៀងរាល់ ១ ម៉ោង)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: build_report(app.bot, MY_CHAT_ID, TOPIC_ID), 'interval', hours=1)
    scheduler.start()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", manual_report))

    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        logger.info("Bot is running on Railway...")
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main_async())
    except (KeyboardInterrupt, SystemExit):
        pass
        
