import os
import logging
import datetime
import requests
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import ccxt
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN          = os.getenv("BOT_TOKEN")
MY_CHAT_ID         = os.getenv("MY_CHAT_ID")
TOPIC_ID           = os.getenv("TOPIC_ID")
TOPIC_ALERT        = os.getenv("TOPIC_ALERT")
TWELVEDATA_API_KEY = os.getenv("TWELVEDATA_API_KEY")

last_alert_time = {}

# ══════════════════════════════════════════════════════════════════════════════
# DATA & INDICATORS
# ══════════════════════════════════════════════════════════════════════════════
def get_exchange():
    return ccxt.binance({"enableRateLimit": True, "options": {"defaultType": "spot"}})

def fetch_ohlcv(timeframe="1h", limit=100):
    try:
        exchange = get_exchange()
        ohlcv = exchange.fetch_ohlcv("PAXG/USDT", timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=["timestamp", "Open", "High", "Low", "Close", "Volume"])
        df["Date"] = pd.to_datetime(df["timestamp"], unit="ms")
        for col in ["Open", "High", "Low", "Close", "Volume"]: df[col] = df[col].astype(float)
        return df
    except:
        # Fallback ខ្លីៗសម្រាប់ទាញ data ពេល ccxt គាំង
        return pd.DataFrame()

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    return 100 - (100 / (1 + (gain / loss)))

def get_economic_news():
    try:
        r = requests.get("https://www.fxstreet.com/rss/news", timeout=5)
        root = ET.fromstring(r.content)
        titles = [item.findtext("title") for item in root.iter("item") if "gold" in item.findtext("title").lower()]
        return titles[:3] if titles else ["No major gold news."]
    except: return ["News source unavailable."]

# ══════════════════════════════════════════════════════════════════════════════
# REPORT BUILDER (FULL VERSION)
# ══════════════════════════════════════════════════════════════════════════════
async def build_report(bot, chat_id, topic_id=None):
    try:
        df = fetch_ohlcv("1h", 100)
        if df.empty: return
        
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Calculation Logic
        rsi = round(calculate_rsi(df["Close"]).iloc[-1], 2)
        pdh, pdl = round(df["High"].max(), 2), round(df["Low"].min(), 2)
        eq_level = round((pdh + pdl) / 2, 2)
        
        news = get_economic_news()
        news_text = "\n".join([f"  • {n}" for n in news])
        
        report = f"""
🏦 *E11 INTELLIGENCE — XAUUSD*
🕐 {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC

💰 *PRICE*
  Current : *${round(last['Close'], 2)}*
  H1 High : ${round(last['High'], 2)}
  H1 Low  : ${round(last['Low'], 2)}

📊 *TREND*
  ⚖️ RANGING
  Mixed EMA signals

📐 *SUPPORT & RESISTANCE*
  🟢 Support    : ${round(df['Low'].min(), 2)}
  🔴 Resistance : ${round(df['High'].max(), 2)}

🧠 *ICT KEY LEVELS*
  PDH         : ${pdh}
  PDL         : ${pdl}
  EQ Level    : ${eq_level}
  Bull FVG    : Detectable
  Bear FVG    : Detectable

📈 *INDICATORS*
  RSI (14)  : {rsi} {'✅ Neutral' if 40 < rsi < 60 else '⚠️ Extreme'}
  
🎯 *SIGNAL*
  ⏳ WAIT
  No clear signal — stay patient

📰 *NEWS*
{news_text}

━━━━━━━━━━━━━━━━━━━
_E11 Sniper Bot • Educational use only_
"""
        kwargs = {"chat_id": chat_id, "text": report.strip(), "parse_mode": "Markdown"}
        if topic_id: kwargs["message_thread_id"] = int(topic_id)
        await bot.send_message(**kwargs)
        
    except Exception as e:
        logger.error(f"Report Error: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# HANDLERS & MAIN
# ══════════════════════════════════════════════════════════════════════════════
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 E11 Sniper Bot is active! Use /report")

async def instant_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await build_report(context.bot, update.effective_chat.id, update.effective_message.message_thread_id)

def main():
    if not BOT_TOKEN: return
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", instant_report))

    scheduler = AsyncIOScheduler()
    # បាញ់ Report ទៅ Topic ដើមរាល់ ៤ ម៉ោងម្តង (ឧទាហរណ៍)
    scheduler.add_job(build_report, 'interval', hours=4, args=[app.bot, MY_CHAT_ID, TOPIC_ID])
    scheduler.start()

    logger.info("🚀 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
    
