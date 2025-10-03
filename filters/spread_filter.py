import os
import ccxt
from dotenv import load_dotenv
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


# 스프레드 계산
# 스프레드 = 매도 1호가(ask)와 매수 1호가(bid)의 가격 차이를 퍼센트로 나타낸 값 (거래 효율성 지표)
# 스프레드가 작을수록 유동성이 높고, 진입/청산 시 불필요한 손실(슬리피지)이 적다
# 지금 상황에서는 굳이 필요가 없고 연산 속도를 느리게 하므로 사용하지 않음.
def get_spread(symbol):
    try:
        orderbook = binance.fetch_order_book(symbol, limit=5)
        bid = orderbook["bids"][0][0] if orderbook["bids"] else None
        ask = orderbook["asks"][0][0] if orderbook["asks"] else None
        if bid and ask:
            spread = (ask - bid) / ((ask + bid) / 2) * 100
            return spread
    except Exception as e:
        notify_error(f"Error fetching orderbook for {symbol}: {e}")
    return None


# 스프레드 좋은 상위 종목 추리기
def filter_by_spread(markets):
    """
    인자로 받은 마켓 리스트에서 스프레드 기준으로 상위 절반 추리기
    """
    spreads = []
    for symbol, volume in markets:
        spread = get_spread(symbol)
        if spread is not None:
            spreads.append((symbol, volume, spread))

    # 스프레드 기준 오름차순 정렬
    sorted_spreads = sorted(spreads, key=lambda x: x[2])

    # 리스트 절반만 반환
    half = len(sorted_spreads) // 2
    return sorted_spreads[:half]
