import os
import ccxt
from dotenv import load_dotenv
import requests

load_dotenv()
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

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


def send_message(msg: str):
    payload = {"content": msg}
    r = requests.post(WEBHOOK_URL, json=payload)
    if r.status_code == 204:
        print("✅ 메시지 전송 성공")
    else:
        print(f"실패 {r.status_code} {r.text}")


def notify_trade(advice_json):
    symbol = advice_json.get("symbol")
    action = advice_json.get("action")
    entry = advice_json.get("entry_price")
    tp = advice_json.get("take_profit")
    sl = advice_json.get("stop_loss")
    reason = advice_json.get("reason")

    msg = (
        f"매매 실행 알림\n"
        f"심볼: {symbol} | 액션: {action}\n"
        f"매수가: {entry} USDT\n"
        f"목표가(TP): {tp} USDT\n"
        f"손절가(SL): {sl} USDT\n\n"
        f"AI 기반 트레이드 근거:\n{reason}"
    )

    send_message(msg)


def notify_error(error_msg: str):
    msg = f"트레이딩 봇 에러 발생\n" f"에러 내용: {error_msg}"
    send_message(msg)


def get_usdt_price(symbol: str):
    """심볼(예: 'BTC/USDT')의 현재가 가져오기"""
    try:
        ticker = binance.fetch_ticker(symbol)
        if ticker.get("last") is not None:
            return float(ticker["last"])
        bid, ask = ticker.get("bid"), ticker.get("ask")
        if bid is not None and ask is not None:
            return (float(bid) + float(ask)) / 2
    except ccxt.BaseError:
        return None
    return None


def send_portfolio_message():
    balance = binance.fetch_balance()

    # 보유 코인 (USDT 제외)
    total_value_usdt = 0.0
    for coin, qty in balance["total"].items():
        if coin == "USDT":
            continue
        if qty and qty > 0:
            symbol = f"{coin}/USDT"
            price = get_usdt_price(symbol) if symbol in binance.markets else None
            value = (qty * price) if price is not None else None
            if value is not None:
                total_value_usdt += value

    # USDT 잔고
    usdt_total = float(balance["total"].get("USDT", 0.0) or 0.0)

    # 총자산
    grand_total_usdt = total_value_usdt + usdt_total

    # 메시지 (딱 두 줄만)
    msg = (
        f"코인 평가금액 합계(USDT): {total_value_usdt:.4f}\n"
        f"총자산(USDT 기준): {grand_total_usdt:.4f}"
    )
    send_message(msg)
