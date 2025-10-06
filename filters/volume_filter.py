import os
import ccxt
from dotenv import load_dotenv
from utils.place_trade import fetch_balance
from utils.discord_msg import notify_error

load_dotenv()

api_key = os.getenv("BINANCE_API_KEY")
secret_key = os.getenv("BINANCE_SECRET_KEY")

binance = ccxt.binance(
    config={
        "apiKey": api_key,
        "secret": secret_key,
        "enableRateLimit": True,
        "options": {"defaultType": "spot"},
    }
)


def top100_markets(fee_rate=0.001):
    """
    상위 100 USDT 마켓 중 내 잔고로 최소 주문 가능(수수료 고려)한 심볼만 반환
    """
    tickers = binance.fetch_tickers()
    markets = []
    usdt_balance = fetch_balance()

    for symbol, data in tickers.items():
        if not symbol.endswith("/USDT"):
            continue

        volume = data.get("quoteVolume")
        if not volume:
            continue

        try:
            market_info = binance.market(symbol)
            min_notional = market_info["limits"]["cost"]["min"]

            if min_notional is None:
                continue

            # 수수료 반영 후 잔고
            effective_balance = usdt_balance * (1 - fee_rate)

            # 최소 주문 가능 여부 체크
            if effective_balance >= min_notional:
                markets.append((symbol, volume))
        except Exception as e:
            notify_error(f"Error checking {symbol}: {e}")

    # 거래대금 기준 내림차순 정렬
    sorted_markets = sorted(markets, key=lambda x: x[1], reverse=True)

    # 상위 100개만 추출 --> 50개로 변경 (배포환경에서 너무 오래걸림)
    return sorted_markets[:50]
