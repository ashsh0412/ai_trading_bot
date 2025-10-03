import os
from dotenv import load_dotenv
import requests

load_dotenv()
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

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
        f"심볼: `{symbol}` | 액션: {action}\n"
        f"매수가: {entry} USDT\n"
        f" 목표가(TP): {tp} USDT\n"
        f" 손절가(SL): {sl} USDT\n\n"
        f" AI 기반 트레이드 근거:\n{reason}"
    )

    send_message(msg)


def notify_error(error_msg: str):
    msg = (
        f"트레이딩 봇 에러 발생\n"
        f"에러 내용: {error_msg}"
    )
    send_message(msg)