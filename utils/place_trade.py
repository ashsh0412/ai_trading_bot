import os
import ccxt
from dotenv import load_dotenv
from utils.discord_msg import notify_error, notify_trade

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


# 잔고 조회 (USDT만 추출)
def fetch_balance():
    balance = binance.fetch_balance()
    return balance["USDT"]["free"]  # 사용 가능한 USDT 잔고만 리턴


def place_trade(signal):
    """
    AI 추천 signal(dict)을 받아 USDT 전량 매수/매도 실행
    - 최소 주문 금액(min_notional) 체크
    - 심볼별 정밀도(precision) 보정
    - 수수료 고려 (실제 free balance 기준)
    """
    symbol = signal["symbol"]
    action = signal["action"].upper()
    entry = float(signal["entry_price"])
    tp = float(signal["take_profit"])
    sl = float(signal["stop_loss"])

    # 현재 잔고
    usdt_balance = fetch_balance()

    # 심볼별 마켓 정보
    market = binance.market(symbol)
    min_notional = market["limits"]["cost"]["min"]

    if action == "BUY":
        # 수수료 반영 후 매수 가능 금액
        effective_balance = usdt_balance * 0.999

        # 매수 수량 (예상치)
        amount = effective_balance / entry
        amount = float(binance.amount_to_precision(symbol, amount))

        # 잔고 및 최소 주문 가능 수량 체크
        min_amount = market["limits"]["amount"]["min"]
        if amount < min_amount:
            notify_error(
                f"⚠️ {symbol} 주문 불가: 최소 수량 {min_amount}보다 작음 (현재 {amount})"
            )
            return

        # 가격 정밀도 보정
        entry = float(binance.price_to_precision(symbol, entry))
        tp = float(binance.price_to_precision(symbol, tp))
        sl = float(binance.price_to_precision(symbol, sl))
        stop_limit_price = float(binance.price_to_precision(symbol, sl * 0.995))

        # 주문 금액 검증
        order_value = amount * entry
        if order_value < min_notional:
            notify_error(
                f"⚠️ 주문 불가: 최소 {min_notional} USDT 필요 (현재 {order_value:.2f})"
            )
            return

        # 지정가 매수
        binance.create_limit_buy_order(symbol, amount, entry)

        # 체결 확인 후 실제 보유 잔고 확인 (수수료 반영)
        coin = symbol.split("/")[0]
        coin_balance = binance.fetch_balance()[coin]["free"]
        filled_amount = float(binance.amount_to_precision(symbol, coin_balance))

        if filled_amount <= 0:
            notify_error("⚠️ 매수 후 코인 잔고가 없습니다. OCO 예약 생략")
            return

        notify_trade(signal)

        # OCO 예약 매도
        binance.private_post_order_oco(
            {
                "symbol": symbol.replace("/", ""),
                "side": "SELL",
                "quantity": str(filled_amount),
                "price": str(tp),  # 익절 가격
                "stopPrice": str(sl),  # 손절 트리거
                "stopLimitPrice": str(stop_limit_price),
                "stopLimitTimeInForce": "GTC",
            }
        )

    elif action == "SELL":
        # 보유 코인 잔고 확인
        coin = symbol.split("/")[0]
        coin_balance = balances[coin]["free"]

        if coin_balance <= 0:
            notify_error(f"⚠️ No {coin} balance to sell")
            return

        # 수량 정밀도 보정
        amount = float(binance.amount_to_precision(symbol, coin_balance))

        # 잔고 및 최소 주문 가능 수량 체크
        min_amount = market["limits"]["amount"]["min"]
        if amount < min_amount:
            notify_error(
                f"⚠️ {symbol} 주문 불가: 최소 수량 {min_amount}보다 작음 (현재 {amount})"
            )
            return

        # 가격 정밀도 보정
        entry = float(binance.price_to_precision(symbol, entry))
        tp = float(binance.price_to_precision(symbol, tp))
        sl = float(binance.price_to_precision(symbol, sl))
        stop_limit_price = float(binance.price_to_precision(symbol, tp * 1.005))

        # 주문 금액 검증
        order_value = amount * entry
        if order_value < min_notional:
            notify_error(
                f"⚠️ 주문 불가: 최소 {min_notional} USDT 필요 (현재 {order_value:.2f})"
            )
            return

        # 지정가 매도
        binance.create_limit_sell_order(symbol, amount, entry)

        # 체결 후 실제 USDT 잔고 확인
        balances = binance.fetch_balance()
        coin_balance = balances[coin]["free"]
        filled_amount = float(binance.amount_to_precision(symbol, coin_balance))

        if filled_amount <= 0:
            notify_error("⚠️ 매도 후 코인 잔고가 없습니다. OCO 예약 생략")
            return

        notify_trade(signal)

        # OCO 예약 매수
        binance.private_post_order_oco(
            {
                "symbol": symbol.replace("/", ""),
                "side": "BUY",
                "quantity": str(filled_amount),
                "price": str(sl),  # 재매수 가격
                "stopPrice": str(tp),  # 손절 트리거
                "stopLimitPrice": str(stop_limit_price),
                "stopLimitTimeInForce": "GTC",
            }
        )
