import os
from dotenv import load_dotenv
import pytz

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")
TOPIC_ID = int(os.getenv("ALERT_TOPIC_ID", 0))

KH_TZ = pytz.timezone("Asia/Phnom_Penh")

# Symbols
GOLD_SYMBOL = "GC=F"       # Gold Futures (XAUUSD Proxy)
DXY_SYMBOL = "DX-Y.NYB"    # Dollar Index
US10Y_SYMBOL = "^TNX"     # 10-Year Bond Yield
US02Y_SYMBOL = "^IRX"     # 13-Week/2-Year Proxy
SPX_SYMBOL = "^GSPC"      # S&P 500
NAS_SYMBOL = "^IXIC"      # Nasdaq 100
US30_SYMBOL = "^DJI"      # Dow Jones
OIL_SYMBOL = "CL=F"       # Crude Oil
