import sys
import os
import asyncio
from flask import Flask
from threading import Thread
from telegram.ext import ApplicationBuilder, CommandHandler
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from utils.logger import logger
from telegram.bot_handlers import start_command, bias_command, news_command, sentiment_command, cot_command, session_command
from analysis.bias_generator import generate_full_market_report

# --- Flask Server សម្រាប់ទប់ Render កុំឱ្យ Sleep ---
flask_app = Flask("")

@flask_app.route('/')
def home():
    return "🎯 E11 Sniper High-Frequency Intelligence Server Status: ACTIVE"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port)

# --- Automated Schedules ---
async def scheduled_broadcast(bot: Bot):
    try:
        logger.info("Triggering scheduled market profile injection...")
        report = generate_full_market_report()
        await bot.send_message(chat_id=config.GROUP_ID, text=report, parse_mode="Markdown")
        logger.info("Successfully transmitted market profile to channel.")
    except Exception as e:
        logger.error(f"Cron broadcast transmission failed: {e}")

async def run_engine():
    app = ApplicationBuilder().token(config.BOT_TOKEN).build()
    
    # Mapping Telegram commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("bias", bias_command))
    app.add_handler(CommandHandler("analysis", bias_command))
    app.add_handler(CommandHandler("gold", bias_command))
    app.add_handler(CommandHandler("news", news_command))
    app.add_handler(CommandHandler("sentiment", sentiment_command))
    app.add_handler(CommandHandler("cot", cot_command))
    app.add_handler(CommandHandler("session", session_command))
    app.add_handler(CommandHandler("killzone", session_command))
    
    # Automation Chrono Timers
    scheduler = AsyncIOScheduler(timezone=config.KH_TZ)
    for hr in [8, 14, 19, 21]:
        scheduler.add_job(scheduled_broadcast, 'cron', hour=hr, minute=0, args=[app.bot])
    scheduler.start()
    
    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        await asyncio.Event().wait()

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    asyncio.run(run_engine())
    
