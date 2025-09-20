from indicators import get_indicators
from binance import top100_markets
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

# 전역 캐시: (심볼, 타임프레임, 캔들개수) 단위로 저장; 나중에 While 추가시 초기화 필요
ohlcv_cache = {}


def fetch_ohlcv(symbol, timeframe, limit):
    key = (symbol, timeframe, limit)
    if key not in ohlcv_cache:
        try:
            df = get_indicators(symbol, timeframe, limit)
            ohlcv_cache[key] = df
        except Exception as e:
            print(f"{symbol} OHLCV 가져오기 실패: {e}")
            return None
    return ohlcv_cache[key]


# 변동성 필터링 (ATR + 볼린저 밴드 폭)
def get_vol_metrics(symbol, timeframe="15m", limit=200):
    """
    변동성 필터 전용: ATR + 밴드폭 + 점수 (정규화된 버전)
    - ATR14: 이미 현재가 대비 백분율(%)로 계산됨
    - BB_width: 이미 SMA 대비 백분율(%)로 계산됨
    - score: 두 백분율을 합산하여 동일 스케일로 비교
    """
    df = fetch_ohlcv(symbol, timeframe, limit)
    if df is None:
        return None

    # 최근 20개 캔들의 평균으로 안정적인 측정
    recent = df.tail(20)

    # ATR과 볼린저밴드 폭 평균 계산
    atr_mean = recent["ATR14"].mean()
    band_width_mean = (recent["BB_upper"] - recent["BB_lower"]).mean()

    # NaN 체크
    if pd.isna(atr_mean) or pd.isna(band_width_mean):
        return None

    # 정규화된 변동성 점수 계산
    # - ATR14: 이미 현재가 대비 백분율 (예: 2.5%)
    # - band_width: 이미 SMA 대비 백분율 (예: 4.0%)
    # - 둘 다 백분율이므로 직접 합산 가능
    score = atr_mean + abs(band_width_mean)

    return atr_mean, band_width_mean, score


def filter_by_volatility(markets):
    scored = []
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {
            executor.submit(get_vol_metrics, s, "15m", 200): (s, v)
            for (s, v) in markets
        }
        for fut in as_completed(futures):
            res = fut.result()
            if res:
                atr, band_width, score = res
                s, v = futures[fut]
                scored.append((s, v, atr, band_width, score))

    scored.sort(key=lambda x: x[4], reverse=True)
    half = max(1, len(scored) // 2)
    return scored[:half]


# 기본 필터링 (SMA/EMA, MACD, RSI)
#  - 의도:
#    1) SMA/EMA로 추세 방향 확인
#    2) MACD로 모멘텀/전환 확인
#    3) RSI로 과열/침체 및 50선 기준 확인


def _crossed_up(a: pd.Series, b: pd.Series) -> pd.Series:
    """a가 b를 상향 돌파했는지 (골든크로스) 여부의 시계열"""
    return (a.shift(1) <= b.shift(1)) & (a > b)


def _crossed_down(a: pd.Series, b: pd.Series) -> pd.Series:
    """a가 b를 하향 돌파했는지 (데드크로스) 여부의 시계열"""
    return (a.shift(1) >= b.shift(1)) & (a < b)


def basic_filter_df(df: pd.DataFrame, lookback_cross: int = 5, obv_lookback: int = 5):
    need_cols = [
        "close",
        "SMA20",
        "EMA20",
        "RSI14",
        "MACD",
        "MACD_signal",
        "MACD_hist",
        "OBV",
    ]
    df_valid = df.iloc[-50:].dropna(subset=need_cols)
    if df_valid.empty or len(df_valid) < 3:
        return {
            "long_basic": False,
            "short_basic": False,
            "explain": {"reason": "insufficient data"},
        }

    df_valid = df_valid.copy()
    df_valid["macd_cross_up"] = _crossed_up(df_valid["MACD"], df_valid["MACD_signal"])
    df_valid["macd_cross_down"] = _crossed_down(
        df_valid["MACD"], df_valid["MACD_signal"]
    )

    last = df_valid.iloc[-1]
    prev_ema20 = df_valid["EMA20"].iloc[-2]

    # 1) 추세 판단 (SMA/EMA)
    trend_up = (last["close"] > last["SMA20"]) and (last["EMA20"] > prev_ema20)
    trend_down = (last["close"] < last["SMA20"]) and (last["EMA20"] < prev_ema20)

    # 2) MACD 판단
    recent_gc = df_valid["macd_cross_up"].tail(lookback_cross).any()
    recent_dc = df_valid["macd_cross_down"].tail(lookback_cross).any()
    macd_bull = (last["MACD"] > last["MACD_signal"]) or recent_gc
    macd_bear = (last["MACD"] < last["MACD_signal"]) or recent_dc

    # 2-보정) MACD_hist 확인
    hist_recent = df_valid["MACD_hist"].tail(3)  # 최근 3봉
    hist_up = (last["MACD_hist"] > 0) or (hist_recent.diff().iloc[-1] > 0)
    hist_down = (last["MACD_hist"] < 0) or (hist_recent.diff().iloc[-1] < 0)

    # 3) RSI 판단
    rsi_bull = (last["RSI14"] >= 50) and (last["RSI14"] < 70)
    rsi_bear = (last["RSI14"] <= 50) and (last["RSI14"] > 30)

    # 4) OBV 판단
    obv_trend = df_valid["OBV"].diff().tail(obv_lookback).sum()
    obv_up = obv_trend > 0
    obv_down = obv_trend < 0

    # 최종 신호
    long_basic = trend_up and macd_bull and rsi_bull and hist_up and obv_up
    short_basic = trend_down and macd_bear and rsi_bear and hist_down and obv_down

    return {
        "long_basic": bool(long_basic),
        "short_basic": bool(short_basic),
        "explain": {
            "trend_up": trend_up,
            "trend_down": trend_down,
            "macd_bull": macd_bull,
            "macd_bear": macd_bear,
            "hist_up": hist_up,
            "hist_down": hist_down,
            "obv_up": obv_up,
            "obv_down": obv_down,
            "rsi_bull(50-70)": rsi_bull,
            "rsi_bear(30-50)": rsi_bear,
            "last_close": float(last["close"]),
            "last_SMA20": float(last["SMA20"]),
            "last_EMA20": float(last["EMA20"]),
            "prev_EMA20": float(prev_ema20),
            "last_RSI14": float(last["RSI14"]),
            "last_MACD": float(last["MACD"]),
            "last_MACD_signal": float(last["MACD_signal"]),
            "last_MACD_hist": float(last["MACD_hist"]),
            "last_OBV": float(last["OBV"]),
        },
    }


def evaluate_basic(symbol, timeframe="15m", limit=200, lookback_cross=5):
    """
    단일 심볼에 대해 기본 필터(롱/숏/없음) 의사결정.
    반환: (symbol, decision, detail)
      - decision: "long" | "short" | "none"
      - detail: basic_filter_df()의 결과(explain 포함)
    """
    df = fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    if df is None:
        return (symbol, "none", {"error": "fetch_failed"})
    result = basic_filter_df(df, lookback_cross=lookback_cross)

    decision = "none"
    if result["long_basic"]:
        decision = "long"
    elif result["short_basic"]:
        decision = "short"

    return (symbol, decision, result["explain"])


def filter_by_basic(
    markets, timeframe="15m", limit=200, mode="both", max_workers=12, lookback_cross=5
):
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for item in markets:
            s, v = item[0], item[1]
            fut = executor.submit(evaluate_basic, s, timeframe, limit, lookback_cross)
            futures[fut] = (s, v)

        for fut in as_completed(futures):
            (s, v) = futures[fut]
            try:
                sym, decision, explain = fut.result()
                if mode == "both" and decision in ("long", "short"):
                    results.append((sym, v, decision, explain))
                elif mode == decision:
                    results.append((sym, v, decision, explain))
            except Exception as e:
                print(f"[기본필터 오류] {s}: {e}")
                continue

    results.sort(key=lambda x: x[1], reverse=True)
    return results


if __name__ == "__main__":
    # 1) 거래량 상위 100
    markets = top100_markets()  # [(symbol, volume), ...] 가정

    # 2) 변동성 좋은 절반
    vol_top_half = filter_by_volatility(markets)
    print(f"\n[변동성 좋은 절반 종목] (총 {len(vol_top_half)}개)")
    for s, v, atr, band, score in vol_top_half:
        print(
            f"{s} | 거래대금: {v:.2f} | ATR: {atr:.4f} | 밴드폭: {band:.4f} | 점수: {score:.4f}"
        )

    # 3) 기본 필터 적용 (롱/숏 동시 스캔).
    basic_pass = filter_by_basic(
        vol_top_half, timeframe="15m", limit=200, mode="both", lookback_cross=5
    )
    print(f"\n[기본 필터 통과 종목] (총 {len(basic_pass)}개)")
    for s, v, decision, info in basic_pass:
        rsi = info.get("last_RSI14", float("nan"))
        macd = info.get("last_MACD", float("nan"))
        macd_sig = info.get("last_MACD_signal", float("nan"))
        print(
            f"{s} | 거래대금: {v:.2f} | 신호: {decision.upper()} | "
            f"RSI14: {rsi:.2f} | MACD: {macd:.5f} / 시그널: {macd_sig:.5f} | "
            f"추세상승:{info['trend_up']} 추세하락:{info['trend_down']} "
            f"MACD(강세/약세):{info['macd_bull']}/{info['macd_bear']}"
        )
