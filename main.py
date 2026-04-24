import os
import logging
import asyncio
import yfinance as yf
from datetime import datetime
import pytz
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# --- ១. ការកំណត់ CONFIG ---
TOKEN = os.environ.get('BOT_TOKEN', '')
CHAT_ID = os.environ.get('MY_CHAT_ID', '')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- ២. មុខងារទាញទិន្នន័យមាស ---
def get_intelligence_report():
    try:
        gold = yf.download('GC=F', period='5d', interval='1h', progress=False)
        dxy = yf.download('DX-Y.NYB', period='5d', interval='1h', progress=False)
        
        curr_p = float(gold['Close'].iloc[-1])
        pdh = float(gold['High'].iloc[-2])
        pdl = float(gold['Low'].iloc[-2])
        dxy_val = float(dxy['Close'].iloc[-1])
        
        bias = "BULLISH 🚀" if curr_p > pdh else "BEARISH 📉" if curr_p < pdl else "NEUTRAL ↔️"
        
        return (
            f"🏛 *E11 GLOBAL INTELLIGENCE*\n"
            f"💰 *XAUUSD:* `${curr_p:.2f}`\n"
            f"📊 *BIAS:* {bias}\n"
            f"🌍 *DXY:* `{dxy_val:.2f}`\n"
            f"✅ _Master Sniper System_"
        )
    except Exception as e:
        logger.error(f"Data Error: {e}")
        return "⚠️ Error fetching data!"

# --- ៣. មុខងារ Bot ---
async def send_auto_report(application):
    if CHAT_ID:
        report = get_intelligence_report()
        await application.bot.send_message(chat_id=CHAT_ID, text=report, parse_mode='Markdown')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎯 Bot Active! ប្រើ /report")

async def manual_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    report = get_intelligence_report()
    thread_id = update.effective_message.message_thread_id if update.effective_message.is_topic_message else None
    await update.message.reply_text(report, parse_mode='Markdown', message_thread_id=thread_id)

# --- ៤. ដំណោះស្រាយសម្រាប់ Error Event Loop ---
async def main():
    if not TOKEN:
        logger.error("❌ BOT_TOKEN missing!")
        return

    # បង្កើត Application
    application = ApplicationBuilder().token(TOKEN).build()
    
    # បន្ថែម Command
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('report', manual_report))
    
    # បើកម៉ាស៊ីន Scheduler ក្នុង Loop ជាមួយគ្នា
    scheduler = AsyncIOScheduler(timezone="Asia/Phnom_Penh")
    scheduler.add_job(send_auto_report, 'cron', day_of_week='mon-fri', hour=8, minute=0, args=[application])
    scheduler.start()
    
    logger.info("🚀 Bot is running...")

    # រត់ Bot តាមរបៀប Async ត្រឹមត្រូវ
    async with application:
        await application.initialize()
        await application.start_polling()
        # រក្សា Loop ឱ្យនៅរស់រហូត
        while True:
            await asyncio.sleep(3600)

if __name__ == '__main__':
    # នេះជាបេះដូងនៃដំណោះស្រាយ៖ ប្រើ asyncio.run ដើម្បីគ្រប់គ្រង Loop តែមួយ
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
        
