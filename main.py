from filters.main_filter import run_filters, fetch_ohlcv
from utils.bot import ask_ai_investment
from utils.place_trade import place_trade
import json

# === 메인 ===
final_candidates = run_filters(
    fetch_ohlcv=fetch_ohlcv,
    timeframe="5m",
    limit=3000,
    mode="both",
    lookback_cross=3,
    direction="long",
)

advice_text = ask_ai_investment(final_candidates)

try:
    advice_json = json.loads(advice_text)
    print("\nAI Investment Advice (parsed):")
    print(advice_json)
    place_trade(advice_json)
except Exception as e:
    print("\n⚠️ JSON parsing failed. Raw response shown above.")
    print("Error:", e)