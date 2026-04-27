import os, logging, datetime, asyncio, pytz
import yfinance as yf
import pandas as pd
import numpy as np
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIG ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
MY_CHAT_ID = os.getenv("MY_CHAT_ID")
TOPIC_ID = os.getenv("TOPIC_ID") # Topic សម្រាប់ Report
ALERT_TOPIC = "3" # Topic សម្រាប់ Alerts

class AdvancedICTEngine:
    @staticmethod
    def calculate_volume_profile(df):
        # គណនា Volume Profile លើ 1H
        price_min, price_max = df['Low'].min(), df['High'].max()
        bins = np.linspace(price_min, price_max, 20)
        vprofile = df.groupby(pd.cut(df['Close'], bins))['Volume'].sum()
        
        poc_bin = vprofile.idxmax()
        poc = (poc_bin.left + poc_bin.right) / 2
        
        # Value Area (70% of Volume)
        total_vol = vprofile.sum()
        vprofile_sorted = vprofile.sort_values(ascending=False)
        cumulative_vol = vprofile_sorted.cumsum()
        value_area_bins = vprofile_sorted[cumulative_vol <= total_vol * 0.7].index
        
        vah = max([b.right for b in value_area_bins]) if not value_area_bins.empty else poc * 1.01
        val = min([b.left for b in value_area_bins]) if not value_area_bins.empty else poc * 0.99
        
        return round(vah, 2), round(val, 2), round(poc, 2)

    @staticmethod
    async def get_market_data():
        try:
            gold = yf.Ticker("GC=F")
            df_h1 = gold.history(period="5d", interval="1h")
            df_m5 = gold.history(period="1d", interval="5m")
            if df_h1.empty: return None

            # 1. Volume Profile (1H)
            vah, val, poc = AdvancedICTEngine.calculate_volume_profile(df_h1)
            
            # 2. Liquidity (5ADR & Session)
            df_d = gold.history(period="10d", interval="1d")
            adr_range = (df_d['High'] - df_d['Low']).tail(5).mean()
            last_close = df_h1['Close'].iloc[-1]
            adr_h, adr_l = last_close + (adr_range/2), last_close - (adr_range/2)
            sess_h, sess_l = df_h1['High'].iloc[-24:].max(), df_h1['Low'].iloc[-24:].min()

            return {
                "price": round(last_close, 2), "vah": vah, "val": val, "poc": poc,
                "adr_h": round(adr_h, 2), "adr_l": round(adr_l, 2),
                "sess_h": round(sess_h, 2), "sess_l": round(sess_l, 2),
                "df_m5": df_m5
            }
        except Exception as e:
            logger.error(f"Data Error: {e}")
            return None

# --- ALERT SYSTEM (ឆែកតម្លៃរៀងរាល់នាទី) ---
async def price_monitor(context: ContextTypes.DEFAULT_TYPE):
    data = await AdvancedICTEngine.get_market_data()
    if not data: return

    price = data['price']
    msg = ""

    # 1. Sweep Liquidity Alert
    if price >= data['adr_h']: msg = f"🚨 *LIQUIDITY SWEEP!* \nTarget: 5ADR High (${data['adr_h']})"
    elif price <= data['adr_l']: msg = f"🚨 *LIQUIDITY SWEEP!* \nTarget: 5ADR Low (${data['adr_l']})"
    elif price >= data['sess_h']: msg = f"🧹 *SESSION SWEEP!* \nTarget: Session High (${data['sess_h']})"
    
    # 2. Volume Profile & Fair Value Price Alert
    if abs(price - data['poc']) < 1:
        msg = f"⚖️ *FAIR VALUE PRICE (POC)*\nPrice is at Point of Control: ${data['poc']}"
    elif abs(price - data['vah']) < 1:
        msg = f"📉 *VALUE AREA HIGH (VAH)*\nPotential Rejection Zone: ${data['vah']}"

    if msg:
        await context.bot.send_message(chat_id=MY_CHAT_ID, text=msg, message_thread_id=ALERT_TOPIC, parse_mode="Markdown")

# --- REGULAR REPORT ---
async def send_full_report(context: ContextTypes.DEFAULT_TYPE):
    data = await AdvancedICTEngine.get_market_data()
    if not data: return

    kh_tz = pytz.timezone('Asia/Phnom_Penh')
    now = datetime.datetime.now(kh_tz).strftime('%Y-%m-%d %H:%M')

    report = (
        "🏦 *E11 INTELLIGENCE — XAUUSD*\n"
        f"🕐 {now} (KH) | 🟢 Market Open\n\n"
        "💰 *CURRENT PRICE:* `${" + str(data['price']) + "}`\n\n"
        "📊 *VOLUME PROFILE (1H)*\n"
        f"  🔝 VAH : ${data['vah']}\n"
        f"  🎯 POC : ${data['poc']}\n"
        f"  🔻 VAL : ${data['val']}\n\n"
        "📏 *LIQUIDITY POOLS*\n"
        f"  🔴 5ADR High : ${data['adr_h']}\n"
        f"  🟢 5ADR Low  : ${data['adr_l']}\n"
        f"  🔵 Session H : ${data['sess_h']}\n\n"
        "💡 *STRATEGY NOTE*\n"
        "Confirm 5MN entry when price touches POC/VAH/VAL. Watch for M5 BOS after Liquidity Sweep."
    )
    await context.bot.send_message(chat_id=MY_CHAT_ID, text=report, message_thread_id=TOPIC_ID, parse_mode="Markdown")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    scheduler = AsyncIOScheduler(timezone=pytz.timezone('Asia/Phnom_Penh'))

    # ឆែកតម្លៃរៀងរាល់ ១ នាទីសម្រាប់ Alert
    scheduler.add_job(price_monitor, 'interval', minutes=1, args=[app])
    
    # ផ្ញើររបាយការណ៍តាមម៉ោង
    for hr in [8, 14, 19, 21]:
        scheduler.add_job(send_full_report, 'cron', hour=hr, minute=0, args=[app])

    app.add_handler(CommandHandler("report", lambda u, c: send_full_report(c)))
    
    async with app:
        await app.initialize()
        await app.start()
        scheduler.start()
        await app.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
    
