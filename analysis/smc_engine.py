import pandas as pd
import numpy as np

def analyze_smc(df_pool):
    """ Engine សម្ងាត់សម្រាប់ស្កេនរក Market Structure, FVG, OB, Liquidity និង SMT """
    smc_metrics = {
        "daily_structure": "Neutral", "m15_structure": "Neutral",
        "fvg_status": "No Active FVG", "order_block": "None",
        "buyside_liq": 0.0, "sellside_liq": 0.0, "smt_divergence": "No SMT Detected"
    }
    
    if "D" in df_pool and not df_pool["D"].empty:
        df_d = df_pool["D"]
        if df_d['close'].iloc[-1] > df_d['close'].iloc[-5]:
            smc_metrics["daily_structure"] = "Bullish HH/HL"
        else:
            smc_metrics["daily_structure"] = "Bearish LH/LL"

    if "15m" in df_pool and not df_pool["15m"].empty:
        df = df_pool["15m"]
        current_close = df['close'].iloc[-1]
        
        # គណនា Liquidity Pools (High/Low ចុងក្រោយ)
        smc_metrics["buyside_liq"] = round(df['high'].max(), 2)
        smc_metrics["sellside_liq"] = round(df['low'].min(), 2)
        
        # គណនា FVG
        for i in range(len(df) - 3, len(df) - 1):
            if df['high'].iloc[i-1] < df['low'].iloc[i+1]:
                smc_metrics["fvg_status"] = f"Bullish FVG Layer at ${round(df['low'].iloc[i+1], 2)}"
                break
            elif df['low'].iloc[i-1] > df['high'].iloc[i+1]:
                smc_metrics["fvg_status"] = f"Bearish FVG Layer at ${round(df['high'].iloc[i+1], 2)}"
                break
                
        # គណនា Order Block & BOS/CHOCH
        recent_min = df['low'].iloc[-15:].min()
        smc_metrics["order_block"] = f"M15 Demand Block at ${round(recent_min, 2)}"
        
        if current_close > df['high'].iloc[-5]:
            smc_metrics["m15_structure"] = "BOS (Bullish Continuity) 📈"
        elif current_close < df['low'].iloc[-5]:
            smc_metrics["m15_structure"] = "CHOCH (Bearish Reversal) 📉"
            
    return smc_metrics

def detect_current_session(dt_now):
    """ កំណត់សម្គាល់ Session ជួញដូរ និង Killzones """
    hr = dt_now.hour
    if 7 <= hr < 11: return "Asia Session (No Killzone)"
    elif 14 <= hr < 17: return "London Killzone 🇬🇧"
    elif 19 <= hr < 22: return "New York Killzone 🇺🇸"
    elif 22 <= hr < 23: return "SMC Silver Bullet Timing ⚡"
    return "Late NY / Pre-Asia (Low Volatility)"
  
