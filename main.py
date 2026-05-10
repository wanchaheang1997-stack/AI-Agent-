"""
E11 Sniper Bot — Full Edition
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Report Topic  ← Market intelligence (auto 4x/day + on-demand)
⚡ Alert Topic   ← LuxAlgo M15 signals (auto every 2 min)

Env vars required:
  BOT_TOKEN         — from @BotFather
  POLYGON_API_KEY   — from polygon.io
  ADMIN_ID          — your Telegram numeric ID
  GROUP_ID          — your group chat ID  (e.g. -1001234567890)
  REPORT_TOPIC_ID   — thread_id of 📊Report topic
  ALERT_TOPIC_ID    — thread_id of #Alert topic
"""

import os
import asyncio
import logging
import datetime

import pytz
import numpy as np
import pandas as pd
from flask import Flask
from threading import Thread
from polygon import RESTClient

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
BOT_TOKEN        = os.environ["BOT_TOKEN"]
POLYGON_KEY      = os.environ["POLYGON_API_KEY"]
ADMIN_ID         = int(os.environ["ADMIN_ID"])
GROUP_ID         = os.environ["GROUP_ID"]           # keep as str for send_message
REPORT_TOPIC_ID  = int(os.environ["REPORT_TOPIC_ID"])
ALERT_TOPIC_ID   = int(os.environ["ALERT_TOPIC_ID"])

KH_TZ   = pytz.timezone("Asia/Phnom_Penh")
UTC_TZ  = pytz.utc
client  = RESTClient(POLYGON_KEY)

# ─────────────────────────────────────────────────────────────────────────────
#  Flask keep-alive (Railway needs an open port)
# ─────────────────────────────────────────────────────────────────────────────

flask_app = Flask("")

@flask_app.route("/")
def home():
    return "E11 Sniper Bot is Online! 🎯"

def run_flask():
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# ─────────────────────────────────────────────────────────────────────────────
#  Core Send Helpers
# ─────────────────────────────────────────────────────────────────────────────

async def send_report(bot, text: str):
    """Post to 📊 Report topic."""
    await bot.send_message(
        chat_id=GROUP_ID,
        message_thread_id=REPORT_TOPIC_ID,
        text=text,
        parse_mode="Markdown",
    )

async def send_alert(bot, text: str):
    """Post to ⚡ Alert topic."""
    await bot.send_message(
        chat_id=GROUP_ID,
        message_thread_id=ALERT_TOPIC_ID,
        text=text,
        parse_mode="Markdown",
    )

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

def kh_now() -> str:
    return datetime.datetime.now(KH_TZ).strftime("%H:%M")

def utc_now() -> str:
    return datetime.datetime.now(UTC_TZ).strftime("%d %b %Y  •  %H:%M UTC")

# ─────────────────────────────────────────────────────────────────────────────
#  ENGINE 1 — Market Intelligence Report
# ─────────────────────────────────────────────────────────────────────────────

async def build_report() -> str:
    try:
        now        = datetime.datetime.now(UTC_TZ)
        start_date = (now - datetime.timedelta(days=10)).strftime("%Y-%m-%d")
        aggs       = client.get_aggs("C:XAUUSD", 1, "hour", start_date, now.strftime("%Y-%m-%d"))
        df         = pd.DataFrame(aggs)

        if df.empty:
            return "❌ No market data available right now."

        last_p = round(df["close"].iloc[-1], 2)

        # RSI (14)
        delta  = df["close"].diff()
        gain   = delta.where(delta > 0, 0).rolling(14).mean()
        loss   = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi    = round(100 - (100 / (1 + gain / loss)).iloc[-1], 2)

        # RSI zone label
        if rsi >= 70:
            rsi_label = "🔴 Overbought"
        elif rsi <= 30:
            rsi_label = "🟢 Oversold"
        else:
            rsi_label = "⚪ Neutral"

        # EMA 50 & 200
        ema50  = round(df["close"].ewm(span=50,  adjust=False).mean().iloc[-1], 2)
        ema200 = round(df["close"].ewm(span=200, adjust=False).mean().iloc[-1], 2)

        # Bias
        if last_p > ema200 and ema50 > ema200:
            bias = "📈 Bullish"
        elif last_p < ema200 and ema50 < ema200:
            bias = "📉 Bearish"
        else:
            bias = "⚖️ Neutral / Mixed"

        # Pivot Points (based on previous candle)
        h, l, c = df["high"].iloc[-2], df["low"].iloc[-2], df["close"].iloc[-2]
        pivot = (h + l + c) / 3
        r1    = round(2 * pivot - l, 2)
        r2    = round(pivot + (h - l), 2)
        s1    = round(2 * pivot - h, 2)
        s2    = round(pivot - (h - l), 2)

        # 24h change
        open_24h = df["close"].iloc[-24] if len(df) >= 24 else df["close"].iloc[0]
        change   = round(last_p - open_24h, 2)
        chg_icon = "🟢" if change >= 0 else "🔴"

        return (
            f"┌─────────────────────────────┐\n"
            f"│  🏦  *E11 MARKET INTELLIGENCE*\n"
            f"└─────────────────────────────┘\n\n"
            f"💰 *Price*      `${last_p}`\n"
            f"{chg_icon} *24h Change*  `{'+' if change >= 0 else ''}{change}`\n\n"
            f"┌─ INDICATORS ─────────────────\n"
            f"│ ⚡ RSI (14)   `{rsi}`  {rsi_label}\n"
            f"│ 🌊 EMA 50    `${ema50}`\n"
            f"│ 🌊 EMA 200   `${ema200}`\n"
            f"└───────────────────────────────\n\n"
            f"📊 *BIAS:*  {bias}\n\n"
            f"┌─ KEY LEVELS ─────────────────\n"
            f"│ 🚧 R2  `${r2}`\n"
            f"│ 🚧 R1  `${r1}`\n"
            f"│ 📌 Pivot `${round(pivot, 2)}`\n"
            f"│ 🛡 S1  `${s1}`\n"
            f"│ 🛡 S2  `${s2}`\n"
            f"└───────────────────────────────\n\n"
            f"🕐  {utc_now()}  •  {kh_now()} KH\n"
            f"_Powered by E11 Sniper · Polygon.io_"
        )

    except Exception as e:
        logger.error(f"Report error: {e}")
        return f"❌ Analysis error: {e}"


# ─────────────────────────────────────────────────────────────────────────────
#  ENGINE 2 — LuxAlgo M15 Signal
# ─────────────────────────────────────────────────────────────────────────────

# Track last signal to avoid repeat spam
_last_signal: str | None = None

async def check_luxalgo_signal():
    global _last_signal
    try:
        now        = datetime.datetime.now(UTC_TZ)
        start_date = (now - datetime.timedelta(days=3)).strftime("%Y-%m-%d")
        aggs       = client.get_aggs("C:XAUUSD", 15, "minute", start_date, now.strftime("%Y-%m-%d"))
        df         = pd.DataFrame(aggs)

        if df.empty:
            return None, None

        length = 14
        df["tr"] = np.maximum(
            df["high"] - df["low"],
            np.maximum(
                abs(df["high"] - df["close"].shift(1)),
                abs(df["low"]  - df["close"].shift(1)),
            ),
        )
        slope = df["tr"].rolling(window=length).mean() / length

        df["ph"] = np.where(
            df["high"] == df["high"].rolling(window=length * 2 + 1, center=True).max(),
            df["high"], np.nan,
        )
        df["pl"] = np.where(
            df["low"] == df["low"].rolling(window=length * 2 + 1, center=True).min(),
            df["low"], np.nan,
        )

        upper = np.zeros(len(df))
        lower = np.zeros(len(df))
        u_slp = l_slp = 0
        upper[0], lower[0] = df["high"].iloc[0], df["low"].iloc[0]

        for i in range(1, len(df)):
            if not np.isnan(df["ph"].iloc[i]):
                upper[i], u_slp = df["ph"].iloc[i], slope.iloc[i]
            else:
                upper[i] = upper[i - 1] - u_slp

            if not np.isnan(df["pl"].iloc[i]):
                lower[i], l_slp = df["pl"].iloc[i], slope.iloc[i]
            else:
                lower[i] = lower[i - 1] + l_slp

        last_c = df["close"].iloc[-1]
        prev_c = df["close"].iloc[-2]

        if last_c > upper[-1] and prev_c <= upper[-2]:
            signal = "BUY"
        elif last_c < lower[-1] and prev_c >= lower[-2]:
            signal = "SELL"
        else:
            signal = None

        # Suppress duplicate consecutive signals
        if signal == _last_signal:
            return None, last_c

        if signal:
            _last_signal = signal

        return signal, round(last_c, 2)

    except Exception as e:
        logger.error(f"LuxAlgo error: {e}")
        return None, None


def build_signal_message(signal: str, price: float) -> str:
    if signal == "BUY":
        icon      = "🟢"
        action    = "B U Y"
        arrow     = "📈"
        sl_hint   = f"`${round(price - 8, 2)}`"
        tp1_hint  = f"`${round(price + 15, 2)}`"
        tp2_hint  = f"`${round(price + 30, 2)}`"
    else:
        icon      = "🔴"
        action    = "S E L L"
        arrow     = "📉"
        sl_hint   = f"`${round(price + 8, 2)}`"
        tp1_hint  = f"`${round(price - 15, 2)}`"
        tp2_hint  = f"`${round(price - 30, 2)}`"

    return (
        f"┌─────────────────────────────┐\n"
        f"│  {arrow}  *LUXALGO M15 SIGNAL*\n"
        f"└─────────────────────────────┘\n\n"
        f"{icon}  *{action}  —  XAUUSD*\n\n"
        f"┌─ LEVELS ──────────────────────\n"
        f"│ 📌 Entry    `${price}`\n"
        f"│ 🛑 SL (est)  {sl_hint}\n"
        f"│ 🎯 TP1 (est) {tp1_hint}\n"
        f"│ 🎯 TP2 (est) {tp2_hint}\n"
        f"└───────────────────────────────\n\n"
        f"⏱ Timeframe: *M15*\n"
        f"🕐  {utc_now()}  •  {kh_now()} KH\n\n"
        f"_⚠️ Not financial advice. Always manage your risk._"
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Scheduler Jobs
# ─────────────────────────────────────────────────────────────────────────────

async def job_report(bot):
    text = await build_report()
    await send_report(bot, text)
    logger.info("✅ Scheduled report sent.")

async def job_signal(bot):
    signal, price = await check_luxalgo_signal()
    if signal and price:
        msg = build_signal_message(signal, price)
        await send_alert(bot, msg)
        logger.info(f"✅ Signal sent: {signal} @ {price}")


# ─────────────────────────────────────────────────────────────────────────────
#  Telegram Commands
# ─────────────────────────────────────────────────────────────────────────────

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("👋 E11 Sniper Bot is online!")
        return
    await update.message.reply_text(
        "✅ *E11 Sniper Bot — Online*\n\n"
        "📊 *Report Topic Commands:*\n"
        "`/report` — Trigger market intelligence now\n\n"
        "⚡ *Alert Topic Commands:*\n"
        "`/scan` — Force LuxAlgo M15 scan now\n\n"
        "📋 *Info:*\n"
        "`/status` — Bot & config status\n\n"
        "⏰ *Auto Schedule (KH Time):*\n"
        "Reports → 08:00, 14:00, 19:00, 21:00\n"
        "Signals → Every 2 minutes",
        parse_mode="Markdown",
    )

async def report_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text("📊 Fetching report...")
    text = await build_report()
    await send_report(context.bot, text)
    await update.message.reply_text("✅ Report posted to Report topic.")

async def scan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text("🔍 Scanning M15...")
    signal, price = await check_luxalgo_signal()
    if signal and price:
        msg = build_signal_message(signal, price)
        await send_alert(context.bot, msg)
        await update.message.reply_text(f"✅ Signal posted: {signal} @ ${price}")
    else:
        await update.message.reply_text("🔇 No signal detected right now.")

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(
        f"📊 *E11 Sniper Bot Status*\n\n"
        f"✅ Online\n"
        f"👤 Admin ID:         `{ADMIN_ID}`\n"
        f"💬 Group ID:         `{GROUP_ID}`\n"
        f"📊 Report Topic:     `{REPORT_TOPIC_ID}`\n"
        f"⚡ Alert Topic:      `{ALERT_TOPIC_ID}`\n\n"
        f"⏰ *Auto Reports (KH):*\n"
        f"08:00 · 14:00 · 19:00 · 21:00\n\n"
        f"🔍 *Signal Scan:* every 2 min\n"
        f"🕐 {utc_now()}  •  {kh_now()} KH",
        parse_mode="Markdown",
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────────────────────

async def main():
    # Start Flask in background thread
    Thread(target=run_flask, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start",  start_cmd))
    app.add_handler(CommandHandler("report", report_cmd))
    app.add_handler(CommandHandler("scan",   scan_cmd))
    app.add_handler(CommandHandler("status", status_cmd))

    # Scheduler
    scheduler = AsyncIOScheduler(timezone=KH_TZ)

    # Auto reports — 4x per day KH time
    for hour in [8, 14, 19, 21]:
        scheduler.add_job(
            job_report, "cron",
            hour=hour, minute=0,
            args=[app.bot],
            name=f"report_{hour}h",
        )

    # LuxAlgo scan — every 2 minutes
    scheduler.add_job(
        job_signal, "interval",
        minutes=2,
        args=[app.bot],
        name="luxalgo_scan",
    )

    scheduler.start()
    logger.info("✅ E11 Sniper Bot is live.")

    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        while True:
            await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
