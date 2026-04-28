import os, asyncio, pytz, datetime, logging
from polygon import RESTClient
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from flask import Flask
from threading import Thread

# --- CONFIG ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
POLYGON_KEY = os.getenv("POLYGON_API_KEY")
MY_CHAT_ID = os.getenv("MY_CHAT_ID")
TOPIC_ID = os.getenv("TOPIC_ID")

client = RESTClient(POLYGON_KEY)

# --- WEB SERVER ---
app_web = Flask('')
@app_web.route('/')
def home(): return "E11 Polygon Bot Active!"
def run(): app_web.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# --- POLYGON DATA ENGINE ---
def get_analysis():
    try:
        # ១. ទាញទិន្នន័យមាស (XAUUSD) ពី Polygon
        now = datetime.datetime.now(pytz.utc)
        start = (now - datetime.timedelta(days=3)).strftime('%Y-%m-%d')
        end = now.strftime('%Y-%m-%d')
        
        # ទាញយកតារាងតម្លៃកម្រិត 15 នាទី ដើម្បីឱ្យ Session ហ្មត់ចត់
        aggs = client.get_aggs("C:XAUUSD", 15, "minute", start, end)
        df = pd.DataFrame(aggs)
        
        # ប្តូរ Timezone ទៅម៉ោងខ្មែរ
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True).dt.tz_convert('Asia/Phnom_Penh')
        df.set_index('timestamp', inplace=True)

        # ២. គណនា Session High/Low (NY: 19:00 - 02:00 KH)
        ny_session = df.between_time('19:00', '02:00')
        ny_h = round(ny_session['high'].max(), 2) if not ny_session.empty else 0
        ny_l = round(ny_session['low'].min(), 2) if not ny_session.empty else 0
        
        # ៣. ព័ត៌មានបច្ចុប្បន្ន
        last_p = round(df['close'].iloc[-1], 2)
        h24 = round(df['high'].iloc[-96:].max(), 2)
        l24 = round(df['low'].iloc[-96:].min(), 2)
        
        # Volume Profile (Simulated)
        poc = round((h24 + l24) / 2, 2)
        vah, val = round(h24 - 2, 2), round(l24 + 2, 2)
        
        # Logic Signal
        action = "🚀 BUY (In Discount Zone)" if last_p < poc else "⚡️ SELL (In Premium Zone)"
        now_kh = datetime.datetime.now(pytz.timezone('Asia/Phnom_Penh')).strftime('%Y-%m-%d %H:%M')

        return (
            f"🏦 *E11 INTELLIGENCE — XAUUSD*\n"
            f"🕐 {now_kh} (KH) | 🟢 Real-time (Polygon)\n"
            f"🧬 Fundamental: Market context stable.\n\n"
            f"💰 *CURRENT MARKET PRICE:*\n"
            f"⚜️ Gold High: `${h24}`\n"
            f"⚜️ Gold Low : `${l24}`\n\n"
            f"📊 *VOLUME PROFILE*\n"
            f"  🎯 POC : `${poc}`\n"
            f"  ⬆️ VAH : `${vah}` | ⬇️ VAL : `${val}`\n\n"
            f"🔑 *Key Level:*\n"
            f"  🇺🇸 New York H: `${ny_h}`\n"
            f"  🇺🇸 New York L: `${ny_l}`\n"
            f"  ⚠️ Support: `${l24}` | Resistance: `${h24}`\n\n"
            f"🎯 *SIGNAL*\n"
            f"  Action : {action}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"E11 Sniper Bot • Polygon API"
        )
    except Exception as e:
        return f"❌ Polygon Error: {str(e)}"

# --- BOT HANDLERS ---
async def manual_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_analysis(), parse_mode="Markdown")

async def auto_report(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=MY_CHAT_ID, text=get_analysis(), message_thread_id=TOPIC_ID, parse_mode="Markdown")

async def main():
    Thread(target=run).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
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
    
