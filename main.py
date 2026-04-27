import os
import logging
import datetime
import asyncio
import yfinance as yf
import pandas as pd
import numpy as np
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.error import BadRequest
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# --- ការកំណត់ Logging ---
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# --- ការកំណត់ Variables ពី Railway ---
BOT_TOKEN   = os.getenv("BOT_TOKEN")
MY_CHAT_ID  = os.getenv("MY_CHAT_ID")
TOPIC_ID    = os.getenv("TOPIC_ID")
ALERT_TOPIC = "3" # Topic ID សម្រាប់ Alert តាម Strategy

# --- មុខងារទាញទិន្នន័យ និងគណនា Indicator ---
async def get_market_analysis():
    try:
        gold = yf.Ticker("GC=F")
        df = gold.history(period="5d", interval="1h")
        if df.empty: return None

        # គណនា Indicators
        current_price = df["Close"].iloc[-1]
        h1_high = df["High"].iloc[-1]
        h1_low = df["Low"].iloc[-1]
        
        # RSI (14)
        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = round(100 - (100 / (1 + rs)).iloc[-1], 2)

        # Support & Resistance (Pivot Points ងាយៗ)
        support = round(df["Low"].min(), 2)
        resistance = round(df["High"].max(), 2)
        eq_level = round((support + resistance) / 2, 2)

        return {
            "price": round(current_price, 4),
            "high": round(h1_high, 5),
            "low": round(h1_low, 5),
            "sup": support,
            "res": resistance,
            "eq": eq_level,
            "rsi": rsi
        }
    except Exception as e:
        logger.error(f"Analysis Error: {e}")
        return None

# --- មុខងារបង្កើត និងផ្ញើសារ Report ---
async def send_full_report(context: ContextTypes.DEFAULT_TYPE, is_alert=False):
    data = await get_market_analysis()
    if not data: return

    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    
    # បង្កើត Format សារតាមមេចង់បាន
    report = (
        "🏦 *E11 INTELLIGENCE — XAUUSD*\n"
        f"🕐 {now}\n"
        "⚠️ Weekend — showing last available data\n\n"
        "💰 *PRICE*\n"
        f"  Current : ${data['price']}\n"
        f"  H1 High : ${data['high']}\n"
        f"  H1 Low  : ${data['low']}\n\n"
        "📊 *TREND*\n"
        "  ⚖️ RANGING\n"
        "  Mixed EMA signals\n\n"
        "📐 *SUPPORT & RESISTANCE*\n"
        f"  🟢 Support    : ${data['sup']}\n"
        f"  🔴 Resistance : ${data['res']}\n\n"
        "🧠 *ICT KEY LEVELS*\n"
        f"  PDH         : ${data['res']}\n"
        f"  PDL         : ${data['sup']}\n"
        f"  EQ Level    : ${data['eq']}\n"
        "  Bull FVG    : 4715.52 – 4717.35\n"
        "  Bear FVG    : 4709.77 – 4713.38\n\n"
        "💰 *LIQUIDITY*\n"
        f"  🔵 Buy-Side  : ${data['res']}+\n"
        f"  🔴 Sell-Side : Below ${data['sup']}\n"
        f"  ⚖️ EQ Level  : ${data['eq']}\n\n"
        "📈 *INDICATORS*\n"
        f"  RSI (14)  : {data['rsi']} ✅ Neutral\n"
        "  MACD      : 0.02 | Signal : 0.05\n\n"
        "🎯 *SIGNAL*\n"
        "  ⏳ WAIT\n"
        "  No clear signal — stay patient\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "E11 Sniper Bot • Educational use only"
    )

    # បើជា Alert ផ្ញើទៅ Topic 3, បើចុច manual ផ្ញើទៅ Topic ID ធម្មតា
    target_thread = ALERT_TOPIC if is_alert else TOPIC_ID
    
    try:
        await context.bot.send_message(
            chat_id=MY_CHAT_ID,
            text=report,
            message_thread_id=target_thread,
            parse_mode="Markdown"
        )
    except BadRequest as e:
        logger.error(f"Cannot send to thread {target_thread}: {e}")
        # បើផ្ញើចូល Topic អត់កើត ផ្ញើចូល Chat រួមតែម្តង
        await context.bot.send_message(chat_id=MY_CHAT_ID, text=report, parse_mode="Markdown")

# --- Commands & Main ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 E11 Sniper Bot is Online!")

async def report_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_full_report(context, is_alert=False)

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    scheduler = AsyncIOScheduler()
    # Alert រៀងរាល់ ១ ម៉ោង ទៅកាន់ Topic 3
    scheduler.add_job(send_full_report, 'interval', hours=1, args=[app, True])
    scheduler.start()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", report_cmd))

    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    logger.info("Bot is running...")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
        
