from filters.volume_filter import top100_markets
from utils.indicators import get_indicators
from filters.basic_filter import filter_by_basic
from filters.volatility_filter import filter_by_volatility
from filters.prophet_filter import analyze_with_prophet, select_trading_candidates
from utils.discord_msg import notify_error

# 전역 캐시: (심볼, 타임프레임, 캔들개수) 단위로 저장
ohlcv_cache = {}


def fetch_ohlcv(symbol, timeframe, limit):
    key = (symbol, timeframe, limit)
    if key not in ohlcv_cache:
        try:
            df = get_indicators(symbol, timeframe, limit)
            ohlcv_cache[key] = df
        except Exception as e:
            notify_error(f"{symbol} OHLCV 가져오기 실패: {e}")
            return None
    return ohlcv_cache[key]


def run_filters(fetch_ohlcv, timeframe, limit, mode, lookback_cross, direction):
    global ohlcv_cache

    # 1) 거래량 상위 100
    markets = top100_markets()

    # 2) 변동성 좋은 절반 필터링
    vol_top_half = filter_by_volatility(
        markets, fetch_func=fetch_ohlcv, timeframe=timeframe, limit=limit
    )

    # 3) 기본 필터 적용 (롱/숏 동시 스캔).
    filtered_by_basic = filter_by_basic(
        vol_top_half,
        fetch_func=fetch_ohlcv,
        timeframe=timeframe,
        limit=limit,
        mode=mode,
        lookback_cross=lookback_cross,
    )

    # 기본 필터 통과 종목에 OHLCV 데이터와 보조지표 정보를 합쳐서 dict 형태로 정리
    enriched = []
    for s, v, decision, info in filtered_by_basic:
        df = ohlcv_cache.get((s, timeframe, limit))
        enriched.append(
            {"symbol": s, "volume": v, "signal": decision, "info": info, "ohlcv": df}
        )

    # 4) Prophet 분석 적용하여 종목 5개 이상 시 추가 필터링 (이하는 전부 통과)
    prophet_pass = analyze_with_prophet(
        enriched,
        fetch_func=fetch_ohlcv,
        timeframe=timeframe,
        limit=limit,
        direction=direction,
    )
    final_candidates = select_trading_candidates(prophet_pass)

    ohlcv_cache.clear()  # 캐시 초기화

    return final_candidates
