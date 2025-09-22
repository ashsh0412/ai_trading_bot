from filters.main_filter import run_filters, fetch_ohlcv
from utils.bot import ask_ai_investment
import json

# 필터 실행
final_candidates = run_filters(
    fetch_ohlcv=fetch_ohlcv,
    timeframe="15m",
    limit=1000,
    mode="both",
    lookback_cross=3,
    direction="long",
)

# AI에게 투자 조언 요청
advice_text = ask_ai_investment(final_candidates)

print("=== AI Investment Advice (raw text) ===")
print(advice_text)

# JSON 파싱
try:
    advice_json = json.loads(advice_text)
    print("\n=== Parsed JSON ===")
    print(advice_json)
except Exception as e:
    print("\n⚠️ JSON parsing failed. Raw response shown above.")
    print("Error:", e)
