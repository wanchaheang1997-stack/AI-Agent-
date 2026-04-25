import os, asyncio, yfinance as yf
from telegram.ext import ApplicationBuilder

# --- ១. CONFIG ---
TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('MY_CHAT_ID')
TOPIC_ID = os.environ.get('TOPIC_ID')

async def get_report():
    try:
        g = yf.download('GC=F', period='1d', interval='1m', progress=False)
        p = float(g['Close'].iloc[-1])
        return f"⚡ **SNIPER AUTO-TEST**\n💰 XAUUSD: `${p:.2f}`\n🤖 ស្ថានភាព: កំពុងបាញ់អូតូរាល់ ១ នាទី"
    except: return "⚠️ Error data!"

async def send_auto(context):
    """មុខងារបាញ់អូតូ"""
    tid = int(TOPIC_ID) if TOPIC_ID else None
    await context.bot.send_message(chat_id=CHAT_ID, text=await get_report(), parse_mode='Markdown', message_thread_id=tid)

def main():
    if not TOKEN: return
    app = ApplicationBuilder().token(TOKEN).build()
    
    # កំណត់ឱ្យបាញ់អូតូ រៀងរាល់ ៦០ វិនាទី (១ នាទីម្តង)
    if CHAT_ID:
        app.job_queue.run_repeating(send_auto, interval=60, first=5)
        print("🚀 Test Mode: បាញ់អូតូរាល់ ១ នាទីបានដំឡើងរួច!")

    # រត់ម៉ាស៊ីន
    app.run_polling()

if __name__ == '__main__':
    main()
    
