import asyncio
import logging
import os  # បន្ថែម os សម្រាប់ទាញយក Variables ពី Railway
from telegram.ext import ApplicationBuilder, CommandHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- ចំណុចមេត្រូវផ្ទៀងផ្ទាត់ ---
# ទាញយក Token និង ID ពី Variables ដែលមេបានដាក់ក្នុង Railway
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("MY_CHAT_ID") 

async def send_auto_report(bot):
    if CHAT_ID:
        try:
            await bot.send_message(chat_id=CHAT_ID, text="📊 **E11 Sniper Daily Report**: ទីផ្សារមាសថ្ងៃនេះ...")
        except Exception as e:
            logger.error(f"Error sending report: {e}")

async def start(update, context):
    await update.message.reply_text("ជម្រាបសួរមេ! E11 Sniper Bot រួចរាល់ហើយ។")

def main():
    if not TOKEN:
        logger.error("❌ រកមិនឃើញ TELEGRAM_TOKEN ក្នុង Variables ទេ។ សូមឆែកក្នុង Railway!")
        return

    # Build the application
    application = ApplicationBuilder().token(TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))

    # Set up APScheduler
    scheduler = AsyncIOScheduler()
    # កំណត់ម៉ោងបាញ់ Report (hour=9, minute=0 គឺម៉ោង ៩ ព្រឹក)
    scheduler.add_job(
        send_auto_report,
        trigger="cron",
        hour=9,
        minute=0,
        args=[application.bot]
    )
    scheduler.start()
    
    logger.info("🚀 Bot is running... Waiting for commands.")

    # ✅ វិធីសាស្ត្រត្រឹមត្រូវសម្រាប់ v20+
    application.run_polling()

if __name__ == "__main__":
    main() 
