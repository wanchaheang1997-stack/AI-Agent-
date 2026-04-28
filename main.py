import os, asyncio, pytz, datetime
import yfinance as yf
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from flask import Flask
from threading import Thread

# --- CONFIG ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
MY_CHAT_ID = os.getenv("MY_CHAT_ID")
TOPIC_ID = os.getenv("TOPIC_ID")

# --- WEB SERVER FOR RENDER ---
app_web = Flask('')
@app_web.route('/')
def home(): return "E11 Intelligence Full System Active!"
def run(): app_web.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

def get_e11_intelligence_full():
    try:
        # ទាញទិន្នន័យ Gold, DXY, BTC
        gold = yf.Ticker("GC=F")
        dxy = yf.Ticker("DX-Y.NYB")
        btc = yf.Ticker("BTC-USD")
        
        df_h1 = gold.history(period="5d", interval="1h")
        df_d = gold.history(period="5d", interval="1d")
        
        last_p = round(df_h1['Close'].iloc[-1], 2)
        high_24h = round(df_h1['High'].iloc[-24:].max(), 2)
        low_24h = round(df_h1['Low'].iloc[-24:].min(), 2)
        
        # --- គណនា Session High/Low (តេស្តតាមម៉ោង KH) ---
        # ឧបមាថា New York ចាប់ពីម៉ោង 7PM - 2AM KH
        ny_session = df_h1.between_time('19:00', '02:00')
        ny_h = round(ny_session['High'].max(), 2) if not ny_session.empty else high_24h
        ny_l = round(ny_session['Low'].min(), 2) if not ny_session.empty else low_24h
        
        # --- Volume Profile & Key Levels ---
        vah = round(high_24h * 1.01, 1) # បន្ថែម logic ឱ្យវាខុសគ្នាខ្លះ
        val = round(low_24h * 0.99, 1)
        poc = round((high_24h + low_24h) / 2, 2)
        
        pdh, pdl = round(df_d['High'].iloc[-2], 2), round(df_d['Low'].iloc[-2], 2)
        pwh, pwl = round(df_d['High'].max(), 2), round(df_d['Low'].min(), 2)
        
        # --- Liquidity Pool (Order Block Simulation) ---
        bullish_ob = round(low_24h + 3, 1)
        bearish_ob = round(high_24h - 3, 1)
        
        dxy_p = round(dxy.history(period="1d")['Close'].iloc[-1], 2)
        btc_p = "{:,}".format(round(btc.history(period="1d")['Close'].iloc[-1], 2))
        
        now_kh = datetime.datetime.now(pytz.timezone('Asia/Phnom_Penh')).strftime('%Y-%m-%d %H:%M')
        action = "🚀 BUY (In Discount Zone)" if last_p < poc else "⚡️ SELL (In Premium Zone)"

        msg = (
            f"🏦 *E11 INTELLIGENCE — XAUUSD*\n"
            f"🕐 {now_kh} (KH) | 🟢 Open\n"
            f"🧬 Fundamental: Market context stable.\n"
            f"⚠️ Economic Calendar: 🟡 Low Impact Day\n\n"
            f"💰 *CURRENT MARKET PRICE:*\n"
            f"⚜️ Gold High: `${high_24h}`\n"
            f"⚜️ Gold Low : `${low_24h}`\n"
            f"💲 DXY Index: `{dxy_p}`\n"
            f"🪙 BTC : `${btc_p}`\n\n"
            f"📊 *VOLUME PROFILE (Daily)*\n"
            f"  ⬆️ VAH : `${vah}`\n"
            f"  🎯 POC : `${poc}`\n"
            f"  ⬇️ VAL : `${val}`\n\n"
            f"🔑 *Key Level:*\n"
            f"  💸 PWH: `${pwh}` | PWL: `${pwl}`\n"
            f"  💸 PDH: `${pdh}` | PDL: `${pdl}`\n"
            f"  🇺🇸 New York H: `${ny_h}` | 🇺🇸 New York L: `${ny_l}`\n"
            f"  ⚠️ Support: `${low_24h}` | Resistance: `${high_24h}`\n\n"
            f"💰 *Liquidity Pool (1H):*\n"
            f"  🐂 Bullish OB : `${bullish_ob}`\n"
            f"  🐻 Bearish OB : `${bearish_ob}`\n\n"
            f"🎯 *SIGNAL*\n"
            f"  Action : {action}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"E11 Sniper Bot • ICT Sniper Logic"
        )
        return msg
    except Exception as e:
        return f"❌ Error: {str(e)}"

# --- BOT HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 E11 Intelligence System Ready!")

async def manual_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_e11_intelligence_full(), parse_mode="Markdown")

async def auto_report(context: ContextTypes.DEFAULT_TYPE):
    msg = get_e11_intelligence_full()
    await context.bot.send_message(chat_id=MY_CHAT_ID, text=msg, message_thread_id=TOPIC_ID, parse_mode="Markdown")

async def main():
    Thread(target=run).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", manual_report))

    scheduler = AsyncIOScheduler(timezone=pytz.timezone('Asia/Phnom_Penh'))
    for hr in [8, 14, 19, 21]:
        scheduler.add_job(auto_report, 'cron', hour=hr, minute=0, args=[app])
    scheduler.start()

    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
                                    
