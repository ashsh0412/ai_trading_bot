from filters.main_filter import run_filters, fetch_ohlcv
from utils.bot import ask_ai_investment
from utils.place_trade import place_trade
import json
from utils.discord_msg import notify_trade, notify_error

# direction : "long", "short", "both"
# limit : OHLCV 데이터 개수 (캔들 갯수)
# lookback_cross : 최근 n개 캔들 내에서 골든크로스/데드크로스 발생 여부 체크

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
    place_trade(advice_json)
    notify_trade(advice_json)
except Exception as e:
    notify_trade(e)