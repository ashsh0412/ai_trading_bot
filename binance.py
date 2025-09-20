import os
import ccxt
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("BINANCE_API_KEY")
secret_key = os.getenv("BINANCE_SECRET_KEY")

binance = ccxt.binance(config={"apiKey": api_key, "secret": secret_key})

# 잔고 조회
balance = binance.fetch_balance()
print(balance["USDT"])


# 상위 100개 마켓 조회
def top100_markets():
    tickers = binance.fetch_tickers()
    markets = []
    for symbol, data in tickers.items():
        if symbol.endswith("/USDT"):  # USDT 마켓만
            volume = data.get("quoteVolume")  # 거래대금 기준
            markets.append((symbol, volume))

    # 거래대금 기준 내림차순 정렬
    sorted_markets = sorted(markets, key=lambda x: x[1], reverse=True)

    # 상위 100개만 추출
    return sorted_markets[:100]

for s, v in top100_markets()[:100]:
    print(s, v)