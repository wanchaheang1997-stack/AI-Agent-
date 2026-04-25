import logging
import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncioScheduler

# 1. ការកំណត់ Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ទាញយក Token និង Chat ID ពី Variables របស់ Railway
TOKEN = os.getenv("TELEGRAM_TOKEN")
MY_CHAT_ID = os.getenv("MY_CHAT_ID")

# 2. Function សម្រាប់បាញ់ Report អូតូ (មេអាចកែសម្រួលការវិភាគមាស XAUUSD នៅទីនេះ)
async def send_auto_report(context: ContextTypes.DEFAULT_TYPE):
    try:
        message = "🚀 **E11 Sniper Daily Report**\n\nទីផ្សារមាស XAUUSD ថ្ងៃនេះ៖ [ការវិភាគតាម SMC/ICT របស់មេ]"
        await context.bot.send_message(chat_id=MY_CHAT_ID, text=message, parse_mode='Markdown')
        logger.info("Sent daily report successfully!")
    except Exception as e:
        logger.error(f"Error sending report: {e}")

# 3. Command /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ជម្រាបសួរមេ! E11 Sniper Bot កំពុងដំណើរការយ៉ាងរលូន។")

def main():
    # ឆែកមើលថាមាន TOKEN ឬអត់ ដើម្បីការពារការ Crash
    if not TOKEN:
        logger.error("Error: TELEGRAM_TOKEN variable is missing!")
        return

    # បង្កើត Application
    application = ApplicationBuilder().token(TOKEN).build()

    # បន្ថែម Command
    application.add_handler(CommandHandler("start", start))

    # 4. កំណត់ Scheduler
    scheduler = AsyncioScheduler()
    # បាញ់រាល់ថ្ងៃ ម៉ោង ៨ ព្រឹក (មេអាចកែម៉ោងបានតាមចិត្ត)
    scheduler.add_job(send_auto_report, 'cron', hour=8, minute=0, args=[application])
    scheduler.start()

    logger.info("🚀 Bot is starting with run_polling()...")

    # 5. ប្រើ run_polling() បែបនេះទើបត្រឹមត្រូវ (កុំប្រើ start_polling() ដាច់ខាត)
    application.run_polling()

if __name__ == "__main__":
    main()
    
