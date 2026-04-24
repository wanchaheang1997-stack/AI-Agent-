import os
import logging
import asyncio
import yfinance as yf
from datetime import datetime
import pytz
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

# Load variables
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_ID')

# Logging
logging.basicConfig(level=logging.INFO)

def get_market_intelligence():
    try:
        # ទាញយកទិន្នន័យមាស និង DXY (Dollar Index)
        gold = yf.download('GC=F', period='2d', interval='1h')
        dxy = yf.download('DX-Y.NYB', period='2d', interval='1d')
        
        curr_p = gold['Close'].iloc[-1]
        pdh, pdl = gold['High'].iloc[-2], gold['Low'].iloc[-2]
        dxy_val = dxy['Close'].iloc[-1]
        
        # Logic វិភាគ (Insight)
        bias = "BULLISH 🚀" if curr_p > pdh else "BEARISH 📉" if curr_p < pdl else "SIDEWAYS ↔️"
        
        report = (
            f"🏛 *E11 GLOBAL INTELLIGENCE V40*\n"
            f"⏰ `{datetime.now(pytz.timezone('Asia/Phnom_Penh')).strftime('%H:%M')}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 *XAUUSD PRICE:* `${curr_p:.2f}`\n"
            f"📊 *CURRENT BIAS:* {bias}\n\n"
            f"🌍 *MARKET INSIGHT:*\n"
            f"• DXY Index: `{dxy_val:.2f}`\n"
            f"• PDH (Resistance): `${pdh:.2f}`\n"
            f"• PDL (Support): `${pdl:.2f}`\n\n"
            f"📅 *CALENDAR & CONFLICTS:*\n"
            f"• ពិនិត្យ Conflictly សម្រាប់ស្ថានភាពភូមិសាស្ត្រនយោបាយ\n"
            f"• រង់ចាំ News USD នៅម៉ោងសហរដ្ឋអាមេរិក\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ *Plan your trade, trade your plan!*"
        )
        return report
    except Exception as e:
        return f"⚠️ Error fetching data: {e}"

async def send_daily_report(application):
    report = get_market_intelligence()
    await application.bot.send_message(chat_id=CHAT_ID, text=report, parse_mode='Markdown', message_thread_id=2)

async def manual_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    report = get_market_intelligence()
    await update.message.reply_text(report, parse_mode='Markdown')

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler('report', manual_report))
    
    # កំណត់ម៉ោងបាញ់ Report (ឧទាហរណ៍៖ ម៉ោង ៨:០០ ព្រឹក ម៉ោងខ្មែរ)
    scheduler = AsyncIOScheduler(timezone="Asia/Phnom_Penh")
    scheduler.add_job(send_daily_report, 'cron', hour=8, minute=0, args=[application])
    scheduler.start()
    
    print("Bot E11 កំពុងដើរ...")
    application.run_polling()
  
