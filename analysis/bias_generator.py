from datetime import datetime
import config
from data.market_data import get_multi_tf_data, fetch_market_correlations
from data.macro_fetcher import get_macro_news, get_retail_sentiment, get_cot_data
from analysis.smc_engine import analyze_smc, detect_current_session
from utils.logger import log_signal

def generate_full_market_report():
    """ មុខងារកណ្តាលសម្រាប់ចងក្រងទិន្នន័យដើម្បីបង្កើតជា Report ផ្លូវការ """
    df_pool = get_multi_tf_data()
    correlations = fetch_market_correlations()
    news = get_macro_news()
    sentiment = get_retail_sentiment()
    cot = get_cot_data()
    smc = analyze_smc(df_pool)
    
    now_kh = datetime.now(config.KH_TZ)
    session = detect_current_session(now_kh)
    
    current_price = round(df_pool["15m"]["close"].iloc[-1], 2) if "15m" in df_pool else 0.0
    
    # Logic សម្រាប់កំណត់ Directional Bias
    bullish_score = 0
    bearish_score = 0
    
    if "Bullish" in smc["m15_structure"]: bullish_score += 2
    if "Bearish" in smc["m15_structure"]: bearish_score += 2
    if sentiment["buyers"] < 45: bullish_score += 1  # Contrarian Logic
    if "Bullish" in cot["institutional_bias"]: bullish_score += 2
    
    bias = "NEUTRAL ⚖️"
    if bullish_score > bearish_score: bias = "BULLISH 🚀"
    elif bearish_score > bullish_score: bias = "BEARISH 📉"
    
    # បង្កើត Trade Setup Ideas គំរូ
    entry_price = current_price
    sl = round(entry_price - 12, 2) if "BULLISH" in bias else round(entry_price + 12, 2)
    tp1 = round(entry_price + 15, 2) if "BULLISH" in bias else round(entry_price - 15, 2)
    tp2 = round(entry_price + 35, 2) if "BULLISH" in bias else round(entry_price - 35, 2)
    
    # រក្សាទុកក្នុង Database Journal
    log_signal("XAUUSD", bias, entry_price, sl, tp1)
    
    # ស្ទីល Report បែប Institutional
    report = (
        f"🏛 *XAU/USD INSTITUTIONAL MARKET ANALYSIS*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 *Current Price:* `${current_price}`\n"
        f"🎯 *Directional Bias:* **{bias}**\n\n"
        f"🌐 *MACRO & CORRELATIONS*\n"
        f"• DXY Index: `{correlations.get('DXY', 'N/A')}`\n"
        f"• US10Y Bond Yield: `{correlations.get('US10Y', 'N/A')}%`\n"
        f"• Retail Sentiment: `{sentiment['positioning']} ({sentiment['buyers']}% Long)`\n"
        f"• COT Institutional Insight: `{cot['institutional_bias']}`\n\n"
        f"📈 *SMC MARKET STRUCTURE*\n"
        f"• HTF Daily Trend: `{smc['daily_structure']}`\n"
        f"• LTF M15 Structure: `{smc['m15_structure']}`\n"
        f"• Liquidity Pools: 🟢 BSL: `${smc['buyside_liq']}` | 🔴 SSL: `${smc['sellside_liq']}`\n"
        f"• Key ICT Matrix: `{smc['fvg_status']}`\n"
        f"• Order Block Zone: _{smc['order_block']}_\n\n"
        f"🕐 *SESSION INTELLIGENCE*\n"
        f"• Active Window: `{session}`\n"
        f"• Report Time: `{now_kh.strftime('%Y-%m-%d %H:%M')}` KH\n\n"
        f"⚡ *E11 ALGO TRADE IDEA*\n"
        f"• ACTION: *{'BUY LIMIT' if 'BULLISH' in bias else 'SELL LIMIT'}*\n"
        f"• ENTRY: `${entry_price}`\n"
        f"• SL: `${sl}`\n"
        f"• TP1: `${tp1}` | TP2: `${tp2}`\n"
        f"• Risk/Reward Ratio: `1:2.5`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ _Powered by E11 Lab Quant Analytics Core_"
    )
    return report
  
