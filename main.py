import os
import asyncio
import logging
import datetime
import pytz
import pandas as pd
from flask import Flask
from threading import Thread
from polygon import RESTClient
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# --- Flask Server សម្រាប់ Render ---
server = Flask("")
@server.route('/')
def home(): return "E11 Sniper is Running!"
def run_server(): server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# --- CONFIG ---
KH_TZ = pytz.timezone("Asia/Phnom_Penh")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
POLYGON_KEY = os.environ.get("POLYGON_API_KEY")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))
GROUP_ID = os.environ.get("GROUP_ID")
REPORT_TOPIC = int(os.environ.get("REPORT_TOPIC_ID", 2))

client = RESTClient(POLYGON_KEY)
logging.basicConfig(level=logging.INFO)

# --- ENGINE: MARKET REPORT ---
async def get_report():
    try:
        now = datetime.datetime.now()
        start = (now - datetime.timedelta(days=5)).strftime("%Y-%m-%d")
        aggs = client.get_aggs("C:XAUUSD", 1, "hour", start, now.strftime("%Y-%m-%d"))
        df = pd.DataFrame(aggs)
        lp = round(df["close"].iloc[-1], 2)
        ema = round(df["close"].ewm(span=200, adjust=False).mean().iloc[-1], 2)
        bias = "BULLISH 🚀" if lp > ema else "BEARISH 📉"
        
        return (
            f"🏛 *E11 MARKET INTELLIGENCE*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 *XAUUSD:* `${lp}`\n"
            f"📊 *BIAS:* {bias}\n"
            f"🌊 *EMA 200:* `${ema}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🕐 {datetime.datetime.now(KH_TZ).strftime('%H:%M')} KH\n"
        )
    except Exception as e: return f"❌ Error: {e}"

# --- TELEGRAM HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎯 E11 Sniper Bot V41 (Render) Active!")

async def manual_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    text = await get_report()
    await context.bot.send_message(chat_id=GROUP_ID, message_thread_id=REPORT_TOPIC, text=text, parse_mode="Markdown")

async def auto_job(bot):
    text = await get_report()
    await bot.send_message(chat_id=GROUP_ID, message_thread_id=REPORT_TOPIC, text=text, parse_mode="Markdown")

# --- MAIN ---
async def main():
    Thread(target=run_server).start() # រត់ Flask
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", manual_report))

    scheduler = AsyncIOScheduler(timezone=KH_TZ)
    for hr in [8, 14, 19, 21]:
        scheduler.add_job(auto_job, 'cron', hour=hr, minute=0, args=[app.bot])
    scheduler.start()

    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
  
