import time
import json
import ccxt
import os
from dotenv import load_dotenv

from filters.main_filter import run_filters, fetch_ohlcv
from utils.bot import ask_ai_investment
from utils.place_trade import place_trade
from utils.discord_msg import notify_trade, notify_error, send_portfolio_message

# Binance 객체 (잔고 확인용)
load_dotenv()
api_key = os.getenv("BINANCE_API_KEY")
secret_key = os.getenv("BINANCE_SECRET_KEY")
binance = ccxt.binance(
    {
        "apiKey": api_key,
        "secret": secret_key,
        "enableRateLimit": True,
        "options": {"defaultType": "spot"},
    }
)
binance.load_markets()


def get_usdt_free():
    try:
        bal = binance.fetch_balance()
        return float(bal["free"].get("USDT", 0.0))
    except:
        return 0.0


# 루프 실행
while True:
    try:
        # 1) 잔고 확인 (5 USDT 미만이면 스킵)
        usdt_free = get_usdt_free()
        if usdt_free < 5.0:
            print(f"스킵: USDT 가용 {usdt_free:.4f} < 5.0")
            time.sleep(600)
            continue

        # 2) 후보 스캔
        final_candidates = run_filters(
            fetch_ohlcv=fetch_ohlcv,
            timeframe="5m",
            limit=1500,
            mode="both",
            lookback_cross=3,
            direction="long",
        )

        # 후보 없으면 패스
        if not final_candidates:
            time.sleep(600)
            continue

        # 3) AI 조언 요청
        advice_text = ask_ai_investment(final_candidates)

        # 4) JSON 파싱
        advice_json = json.loads(advice_text)

        # 5) 매매 실행
        place_trade(advice_json)
        send_portfolio_message()

    except Exception as e:
        notify_error(str(e))

    # 3분마다 반복
    time.sleep(600)
