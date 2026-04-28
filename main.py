import os, asyncio, logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- CONFIG ---
BOT_TOKEN = os.getenv("BOT_TOKEN")

# បន្ថែម Command តេស្តងាយៗ
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 សួស្តីមេ! ខ្ញុំ Sniper Bot រាយការណ៍ខ្លួន! វាយ /report ដើម្បីមើលមាស។")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 កំពុងទាញទិន្នន័យមាសជូនមេ... (កូដវិភាគរបស់មេដើរនៅទីនេះ)")

async def main():
    # ប្រើ Token ថ្មីដែលមេបានដាក់ក្នុង Render
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # ដាក់ Command ចូលក្នុង Bot
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", report))

    print("🚀 E11 Sniper Bot is Starting...")
    
    async with app:
        await app.initialize()
        await app.start()
        # ប្រើ drop_pending_updates ដើម្បីកុំឱ្យវាឆ្លើយសារចាស់ៗដែលមេចុចមុនហ្នឹង
        await app.updater.start_polling(drop_pending_updates=True)
        print("✅ Bot is Online and Waiting for messages!")
        while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    from threading import Thread
    from flask import Flask
    # កូដសម្រាប់ឱ្យ Render លោត Live
    web_app = Flask('')
    @web_app.route('/')
    def home(): return "Bot is Live"
    def run(): web_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
    Thread(target=run).start()
    
    asyncio.run(main())
    
