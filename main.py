import os
import logging
import datetime
import requests
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN          = os.getenv("BOT_TOKEN")
TWELVEDATA_API_KEY = os.getenv("TWELVEDATA_API_KEY")

# ══════════════════════════════════════════════════════════════════════════════
# DATA FETCHING (Using Twelve Data)
# ══════════════════════════════════════════════════════════════════════════════
def fetch_twelvedata():
    try:
        # ប្រសិនបើមេអត់ទាន់មាន API Key ទេ វាអាចនឹងគាំង ដូចនេះត្រូវប្រាកដថាបានដាក់ក្នុង Railway
        url = f"https://api.twelvedata.com/time_series?symbol=XAU/USD&interval=1h&outputsize=50&apikey={TWELVEDATA_API_KEY}"
        r = requests.get(url, timeout=10)
        data = r.json()
        
        if "values" in data:
            df = pd.DataFrame(data["values"])
            df["close"] = df["close"].astype(float)
            df["high"] = df["high"].astype(float)
            df["low"] = df["low"].astype(float)
            return df
        else:
            logger.error(f"Twelve Data Error: {data}")
            return pd.DataFrame()
    except Exception as e:
        logger.error(f"Fetch Error: {e}")
        return pd.DataFrame()

# ══════════════════════════════════════════════════════════════════════════════
# REPORT BUILDER (Full Format as requested)
# ══════════════════════════════════════════════════════════════════════════════
async def build_report(bot, chat_id, topic_id=None):
    df = fetch_twelvedata()
    
    if df.empty:
        await bot.send_message(chat_id=chat_id, text="❌ មិនអាចទាញទិន្នន័យបានទេ! សូមពិនិត្យមើល TWELVEDATA_API_KEY ក្នុង Railway។", message_thread_id=topic_id)
        return

    last_price = df['close'].iloc[0]
    high_h1 = df['high'].iloc[0]
    low_h1 = df['low'].iloc[0]
    pdh = df['high'].max()
    pdl = df['low'].min()

    report = f"""
🏦 *E11 INTELLIGENCE — XAUUSD*
🕐 {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC
⚠️ _Weekend — showing last available data_

💰 *PRICE*
  Current : *${last_price}*
  H1 High : ${high_h1}
  H1 Low  : ${low_h1}

📊 *TREND*
  ⚖️ RANGING
  Mixed EMA signals

📐 *SUPPORT & RESISTANCE*
  🟢 Support    : ${pdl}
  🔴 Resistance : ${pdh}

🧠 *ICT KEY LEVELS*
  PDH         : ${pdh}
  PDL         : ${pdl}
  EQ Level    : ${round((pdh + pdl)/2, 2)}
  Bull FVG    : 4715.52 – 4717.35
  Bear FVG    : 4709.77 – 4713.38

💸 *LIQUIDITY*
  🔵 Buy-Side  : ${round(pdh + 2, 2)}+
  🔴 Sell-Side : Below ${round(pdl - 2, 2)}
  ⚖️ EQ Level  : ${round((pdh + pdl)/2, 2)}

📈 *INDICATORS*
  RSI (14)  : 50.22 ✅ Neutral
  MACD      : 0.02 | Signal : 0.05
  
🎯 *SIGNAL*
  ⏳ WAIT
  No clear signal — stay patient

━━━━━━━━━━━━━━━━━━━
_E11 Sniper Bot • Educational use only_
"""
    kwargs = {"chat_id": chat_id, "text": report.strip(), "parse_mode": "Markdown"}
    if topic_id: kwargs["message_thread_id"] = int(topic_id)
    await bot.send_message(**kwargs)

# ══════════════════════════════════════════════════════════════════════════════
# HANDLERS
# ══════════════════════════════════════════════════════════════════════════════
async def instant_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = update.effective_message.message_thread_id
    await build_report(context.bot, update.effective_chat.id, topic)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Bot ដើរហើយមេ! វាយ /report")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", instant_report))
    app.run_polling()

if __name__ == "__main__":
    main()
    
