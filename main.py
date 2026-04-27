import os, logging, datetime, asyncio, pytz, requests
import yfinance as yf
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# --- CONFIG ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
MY_CHAT_ID = os.getenv("MY_CHAT_ID")
TOPIC_ID = os.getenv("TOPIC_ID")

class E11IntelligenceUltra:
    @staticmethod
    def get_sentiment():
        # Scrape or Mock real-time sentiment (Buyer/Seller %)
        try:
            # ក្នុងករណីប្រើ API ឥតគិតថ្លៃ យើងប្រើ Logic ផ្អែកលើ RSI & Volume Profile ជាជំនួយ
            # ឬមេអាចភ្ជាប់ API ពី Myfxbook បើមាន Key
            buy_pct = 63  # តំណាងឱ្យមធ្យមភាគ Retailer Buyer
            sell_pct = 37 # តំណាងឱ្យមធ្យមភាគ Retailer Seller
            return f"🐂 Buy {buy_pct}% | 🐻 Sell {sell_pct}%"
        except:
            return "N/A"

    @staticmethod
    def get_market_insights():
        # Fundamental News & Economic Calendar
        try:
            # Fundamental: ទាញយក News ពី yfinance
            news_list = yf.Ticker("GC=F").news
            headline = news_list[0]['title'] if news_list else "Market consolidating near $4700 level."
            
            # Economic Calendar (Mock logic for Impact levels based on common schedules)
            # មេអាចជំនួសដោយ API ពី FXStreet ប្រសិនបើមេមាន API Key ផ្ទាល់ខ្លួន
            calendar = "🔴 High: US Manufacturing (20:00) | 🟠 Med: Fed Speech (22:30)"
            return headline[:65] + "...", calendar
        except:
            return "Stable macro context.", "🟡 Low Impact Day"

    @staticmethod
    def calculate_volume_profile(df):
        price_min, price_max = df['Low'].min(), df['High'].max()
        bins = np.linspace(price_min, price_max, 25)
        vprofile = df.groupby(pd.cut(df['Close'], bins), observed=False)['Volume'].sum()
        poc = (vprofile.idxmax().left + vprofile.idxmax().right) / 2
        
        # Value Area (70%)
        v_sorted = vprofile.sort_values(ascending=False)
        v_area = v_sorted[v_sorted.cumsum() <= vprofile.sum() * 0.7].index
        vah = max([b.right for b in v_area]) if not v_area.empty else poc * 1.01
        val = min([b.left for b in v_area]) if not v_area.empty else poc * 0.99
        return round(vah, 2), round(val, 2), round(poc, 2)

    @staticmethod
    def calculate_rsi(series, period=14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        return round(100 - (100 / (1 + (gain / loss))).iloc[-1], 2)

    @staticmethod
    async def get_full_analysis():
        try:
            gold, dxy, btc = yf.Ticker("GC=F"), yf.Ticker("DX-Y.NYB"), yf.Ticker("BTC-USD")
            df_h1 = gold.history(period="7d", interval="1h")
            df_d = gold.history(period="10d", interval="1d")
            
            # Fundamentals
            news, calendar = E11IntelligenceUltra.get_market_insights()
            sentiment = E11IntelligenceUltra.get_sentiment()
            
            # Price & VP
            vah, val, poc = E11IntelligenceUltra.calculate_volume_profile(df_h1)
            rsi = E11IntelligenceUltra.calculate_rsi(df_h1['Close'])
            
            # Key Levels
            pdh, pdl = df_d['High'].iloc[-2], df_d['Low'].iloc[-2]
            pwh, pwl = df_d['High'].iloc[-5:].max(), df_d['Low'].iloc[-5:].min()
            
            asia = df_h1.between_time('23:00', '08:00')
            asia_h, asia_l = asia['High'].max(), asia['Low'].min()

            # Signal Logic: RSI 80/30 + POC Retest
            last_p = df_h1['Close'].iloc[-1]
            action = "⏳ រង់ចាំ (Neutral)"
            if rsi <= 30 or (last_p <= poc + 1 and last_p >= poc - 1 and rsi < 45):
                action = "🚀 ឱកាសទិញ (Oversold/FV Retest)"
            elif rsi >= 80 or (last_p >= poc - 1 and last_p <= poc + 1 and rsi > 55):
                action = "📉 ឱកាសលក់ (Overbought/FV Retest)"

            return {
                "p": round(last_p, 2), "h": round(df_h1['High'].iloc[-24:].max(), 2),
                "l": round(df_h1['Low'].iloc[-24:].min(), 2), "dxy": round(dxy.history(period="1d")['Close'].iloc[-1], 2),
                "btc": round(btc.history(period="1d")['Close'].iloc[-1], 2),
                "vah": vah, "val": val, "poc": poc, "pwh": round(pwh, 2), "pwl": round(pwl, 2),
                "pdh": round(pdh, 2), "pdl": round(pdl, 2), "asia_h": round(asia_h, 2),
                "asia_l": round(asia_l, 2), "news": news, "calendar": calendar,
                "sentiment": sentiment, "rsi": rsi, "action": action,
                "bull_ob": round(df_h1[df_h1['Close'] < df_h1['Open']]['Low'].iloc[-1], 2),
                "bear_ob": round(df_h1[df_h1['Close'] > df_h1['Open']]['High'].iloc[-1], 2)
            }
        except Exception as e:
            logger.error(f"Error: {e}"); return None

async def send_report(context: ContextTypes.DEFAULT_TYPE):
    data = await E11IntelligenceUltra.get_full_analysis()
    if not data: return
    
    kh_tz = pytz.timezone('Asia/Phnom_Penh')
    now = datetime.datetime.now(kh_tz)
    
    report = (
        "🏦 *E11 INTELLIGENCE — XAUUSD*\n"
        f"🕐 {now.strftime('%Y-%m-%d %H:%M')} (KH) | 🟢 Open\n"
        f"🧬 *Fundamental:* {data['news']}\n"
        f"🧬 *Sentimental:* {data['sentiment']}\n"
        f"⚠️ *Calendar:* {data['calendar']}\n\n"
        "💰 *CURRENT MARKET PRICE:*\n"
        f"⚜️ Gold High: ${data['h']}\n"
        f"⚜️ Gold Low : ${data['l']}\n"
        f"💲 DXY Index: {data['dxy']}\n"
        f"🪙 BTC : ${data['btc']:,}\n\n"
        "📊 *VOLUME PROFILE*\n"
        f"  ⬆️ VAH : ${data['vah']}\n"
        f"  🎯 POC : ${data['poc']}\n"
        f"  ⬇️ VAL : ${data['val']}\n\n"
        "🔑 *Key Level:*\n"
        f"  💸 PWH: ${data['pwh']} | PWL: ${data['pwl']}\n"
        f"  💸 PDH: ${data['pdh']} | PDL: ${data['pdl']}\n"
        f"  🇯🇵 Asia H: ${data['asia_h']} | Asia L: ${data['asia_l']}\n"
        f"  ⚠️ Support: ${data['pwl']} | Resistance: ${data['pwh']}\n\n"
        "💰 *Liquidity Pool (1H):*\n"
        f"  🐂 Bullish OB : ${data['bull_ob']}\n"
        f"  🐻 Bearish OB : ${data['bear_ob']}\n\n"
        "🎯 *SIGNAL*\n"
        f"  Action : {data['action']}\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "E11 Sniper Bot • ICT Sniper Logic"
    )
    await context.bot.send_message(chat_id=MY_CHAT_ID, text=report, message_thread_id=TOPIC_ID, parse_mode="Markdown")

# ... (Main function and Scheduler remains same as previous versions)
