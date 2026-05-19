import yfinance as yf
import pandas as pd
from utils.logger import logger
import config

def get_multi_tf_data(symbol=config.GOLD_SYMBOL):
    """ ទាញយកទិន្នន័យពី Multi-Timeframe សម្រាប់វិភាគ HTF Structure """
    data_pool = {}
    try:
        # High Timeframes
        data_pool["D"] = yf.Ticker(symbol).history(period="3mo", interval="1d")
        data_pool["4H"] = yf.Ticker(symbol).history(period="1mo", interval="1h") # Proxy for HTF
        # Low Timeframes
        data_pool["15m"] = yf.Ticker(symbol).history(period="5d", interval="15m")
        
        # Clean column names to lowercase
        for tf in data_pool:
            if not data_pool[tf].empty:
                data_pool[tf].columns = [c.lower() for c in data_pool[tf].columns]
    except Exception as e:
        logger.error(f"Error gathering multi-tf data: {e}")
    return data_pool

def fetch_market_correlations():
    """ វិភាគទំនាក់ទំនងរវាងទ្រព្យសកម្មផ្សេងៗ (Correlations) """
    correlations = {}
    symbols = {
        "DXY": config.DXY_SYMBOL, "US10Y": config.US10Y_SYMBOL,
        "SPX500": config.SPX_SYMBOL, "NAS100": config.NAS_SYMBOL,
        "CrudeOil": config.OIL_SYMBOL
    }
    for name, sym in symbols.items():
        try:
            df = yf.Ticker(sym).history(period="2d")
            if not df.empty:
                correlations[name] = round(df["Close"].iloc[-1], 2)
            else:
                correlations[name] = "N/A"
        except:
            correlations[name] = "N/A"
    return correlations
  
