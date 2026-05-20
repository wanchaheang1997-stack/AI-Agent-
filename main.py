import sys
import os  # ⚠️ ថែម os ការពារ Error Status 2 ដាច់ខាត!
import asyncio
import time
from flask import Flask, request, jsonify
import requests
from threading import Thread
from telegram.ext import ApplicationBuilder, CommandHandler
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# បើកផ្លូវឱ្យ Python ស្វែងរកឃើញ Folder ក្នុងគម្រោង
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from utils.logger import logger
from telegram.bot_handlers import start_command, bias_command, news_command, sentiment_command, cot_command, session_command
from analysis.bias_generator import generate_full_market_report

# --- 🌐 ១. បង្កើត Flask Server ---
flask_app = Flask("")

# ប្រព័ន្ធការពារការផ្ញើសារជាន់គ្នា (Anti-Spam Cache ៥ នាទី)
LAST_SIGNALS = {}
SIGNAL_COOLDOWN = 300 

def send_telegram_signal(message):
    try:
        url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": config.GROUP_ID,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        # កំណត់ timeout = 5 វិនាទី ការពារកូដគាំងរង់ចាំបណ្តាញ
        return requests.post(url, json=payload, timeout=5)
    except Exception as e:
        logger.error(f"Error sending to Telegram: {e}")
        return None

# --- 📥 ២. ផ្លូវ Webhook ទទួលទិន្នន័យពី TradingView (រត់លឿនបំផុត) ---
@flask_app.route('/webhook', methods=['POST'])
def webhook():
    global LAST_SIGNALS
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No JSON data received"}), 400

    action = data.get("action", "SIGNAL").upper()  
    ticker = data.get("ticker", "XAUUSD").upper()
    price  = data.get("price", "N/A")
    timeframe = data.get("timeframe", "5") 

    signal_key = f"{ticker}_{action}"
    current_time = time.time()

    # 🛑 ឆែក Cooldown កុំឱ្យផ្ញើជាន់គ្នា
    if signal_key in LAST_SIGNALS:
        if current_time - LAST_SIGNALS[signal_key] < SIGNAL_COOLDOWN:
            return jsonify({"status": "ignored", "message": "Signal is in cooldown"}), 200

    LAST_SIGNALS[signal_key] = current_time

    if "BUY" in action:
        signal_type = "🟢 SIGNAL: BUY / LONG"
    else:
        signal_type = "🔴 SIGNAL: SELL / SHORT"
    
    msg = (
        f"🚨 *E11 LAB - ALGO FLOW* 🚨\n\n"
        f"{signal_type}\n"
        f"📊 *ASSET:* {ticker}\n"
        f"💵 *ENTRY PRICE:* {price}\n"
        f"⏱️ *TIMEFRAME:* {timeframe}\n\n"
        f"🔗 [E11 Lab Library](https://t.me/E11_Lab_Library)"
    )

    # ដំណើរការផ្ញើទៅ Telegram
    response = send_telegram_signal(msg)
    
    if response and response.status_code == 200:
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"status": "failed"}), 500

@flask_app.route('/')
def home():
    return "🎯 E11 Sniper Intelligence Engine Status: ACTIVE"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port)

# --- 📅 ៣. Automated Schedules (បាញ់ Report តាមម៉ោង) ---
async def scheduled_broadcast(bot: Bot):
    try:
        logger.info("Triggering scheduled market profile injection...")
        # បង្កើត Report ដោយឡែកមិនឱ្យរំខានដល់ Webhook ឡើយ
        report = generate_full_market_report()
        await bot.send_message(chat_id=config.GROUP_ID, text=report, parse_mode="Markdown")
        logger.info("Successfully transmitted market profile.")
    except Exception as e:
        logger.error(f"Cron broadcast failed: {e}")

async def run_engine():
    app = ApplicationBuilder().token(config.BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("bias", bias_command))
    app.add_handler(CommandHandler("analysis", bias_command))
    app.add_handler(CommandHandler("gold", bias_command))
    app.add_handler(CommandHandler("news", news_command))
    app.add_handler(CommandHandler("sentiment", sentiment_command))
    app.add_handler(CommandHandler("cot", cot_command))
    app.add_handler(CommandHandler("session", session_command))
    app.add_handler(CommandHandler("killzone", session_command))
    
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
    # ១. រត់ Web Server ទប់ Render កុំឱ្យ Sleep
    Thread(target=run_flask, daemon=True).start()
    
    # ២. រត់ Core Bot Engine
    asyncio.run(run_engine())
    
