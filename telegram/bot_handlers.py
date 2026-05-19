from telegram import Update
from telegram.ext import ContextTypes
from analysis.bias_generator import generate_full_market_report
from data.macro_fetcher import get_macro_news, get_retail_sentiment, get_cot_data
from analysis.smc_engine import detect_current_session
from datetime import datetime
import config

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎯 *E11 Sniper Alpha Operational Core Ready.*\nUse `/bias` to pull institutional matrix.", parse_mode="Markdown")

async def bias_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 _Executing SMC scanning matrices and compiling order flows..._")
    report = generate_full_market_report()
    await update.message.reply_text(report, parse_mode="Markdown")

async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    news_list = get_macro_news()
    msg = "📅 *HIGH IMPACT MACRO CALENDAR*:\n\n"
    for item in news_list:
        msg += f"🔥 *{item['event']}* ({item['time']})\n• Forecast: {item['forecast']} | Prev: {item['previous']}\n\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def sentiment_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sent = get_retail_sentiment()
    msg = f"📊 *RETAIL SENTIMENT REPORT*:\n\n• Buyers: {sent['buyers']}%\n• Sellers: {sent['sellers']}%\n• Matrix: _{sent['interpretation']}_"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def cot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cot = get_cot_data()
    msg = f"🏛 *CFTC INSTITUTIONAL COT DATA*:\n\n• Commercials: {cot['commercial_net']}\n• Non-Commercials: {cot['non_commercial_net']}\n• Bias: *{cot['institutional_bias']}*"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def session_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now_kh = datetime.now(config.KH_TZ)
    sess = detect_current_session(now_kh)
    await update.message.reply_text(f"🕐 *CURRENT MARKET WINDOW*:\n\n• `{sess}`", parse_mode="Markdown")
  
