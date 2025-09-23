import os
import ccxt
from dotenv import load_dotenv

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

balance = binance.fetch_balance()

# 1. 잔고가 0보다 큰 코인만 필터링 (USDT 제외)
held_coins = [
    coin for coin, info in balance["total"].items() if info > 0 and coin != "USDT"
]

print("보유 중인 종목:", held_coins)
print("-" * 40)

all_open_orders = []

# 2. 각 보유 종목에 대해 열린 주문 조회
for coin in held_coins:
    symbol = f"{coin}/USDT"
    print(f"📌 {symbol} 열린 주문 조회 중...")
    try:
        open_orders = binance.fetch_open_orders(symbol=symbol)

        if open_orders:
            print(f"✅ {symbol} 열린 주문 ({len(open_orders)}개)")
            print(f"{'주문ID':<12} {'타입':<15} {'상태':<8} {'수량':<10} {'가격':<12} {'트리거가':<12}")
            print("-" * 70)

            for order in open_orders:
                order_id = order["id"]
                order_type = order["type"]
                status = order["status"]
                amount = order["amount"]
                price = order.get("price", None)
                stop_price = order.get("stopPrice", None)

                print(f"{order_id:<12} {order_type:<15} {status:<8} {amount:<10} {price:<12} {stop_price or '-':<12}")

            print("-" * 70)
            all_open_orders.extend(open_orders)
        else:
            print(f"⚠️ {symbol} 에 열린 주문 없음.")

    except ccxt.ExchangeError as e:
        print(f"❌ 오류 발생 ({symbol}): {e}")

    print()

print("\n=== 전체 열린 주문 요약 ===")
if all_open_orders:
    for order in all_open_orders:
        print(
            f"[{order['symbol']}] {order['side'].upper()} {order['amount']} @ {order['price']} "
            f"(type={order['type']}, status={order['status']}, stop={order.get('stopPrice')})"
        )
else:
    print("현재 열린 주문 없음.")