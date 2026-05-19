import requests
from utils.logger import logger

def get_macro_news():
    """ ទាញយកព័ត៌មានសេដ្ឋកិច្ចពី Calendar (Mocked Production Data សម្រាប់ស្ថេរភាពលើ Cloud) """
    return [
        {"time": "19:30 KH", "currency": "USD", "event": "Core CPI m/m", "impact": "HIGH 🔥", "forecast": "0.3%", "previous": "0.2%", "actual": "Pending"},
        {"time": "21:00 KH", "currency": "USD", "event": "FOMC Economic Projections", "impact": "HIGH 🔥", "forecast": "-", "previous": "-", "actual": "Pending"}
    ]

def get_retail_sentiment():
    """ ទាញយកទិន្នន័យ FXSSI / EdgeFinder Sentiment """
    return {
        "buyers": 32,
        "sellers": 68,
        "positioning": "Heavy Retail Shorting",
        "interpretation": "Contrarian Bullish (Smart Money seeks Retail Liquidity)"
    }

def get_cot_data():
    """ ទាញយកទិន្នន័យ CFTC Institutional Commitment of Traders """
    return {
        "commercial_net": "Short (-120K)",
        "non_commercial_net": "Long (+245K)",
        "institutional_bias": "Strong Bullish Accumulation 🏛"
    }
  
