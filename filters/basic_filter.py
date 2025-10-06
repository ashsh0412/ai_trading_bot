import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    trend_up = (last["close"] > last["SMA20"]) or (last["EMA20"] > prev_ema20)
    trend_down = (last["close"] < last["SMA20"]) or (last["EMA20"] < prev_ema20)

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
    rsi_bull = (last["RSI14"] >= 45) and (last["RSI14"] < 75)
    rsi_bear = (last["RSI14"] <= 55) and (last["RSI14"] > 25)

    # 4) OBV 판단
    obv_trend = df_valid["OBV"].diff().tail(obv_lookback).sum()
    obv_up = obv_trend >= 0
    obv_down = obv_trend <= 0

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


def evaluate_basic(fetch_func, symbol, timeframe, limit, lookback_cross):
    """
    단일 심볼에 대해 기본 필터(롱/숏/없음) 의사결정.
    반환: (symbol, decision, detail)
      - decision: "long" | "short" | "none"
      - detail: basic_filter_df()의 결과(explain 포함)
    """
    df = fetch_func(symbol, timeframe, limit)
    if df is None:
        return (symbol, "none", {"error": "fetch_failed"})
    result = basic_filter_df(df, lookback_cross=lookback_cross)

    decision = "none"
    if result["long_basic"]:
        decision = "long"
    elif result["short_basic"]:
        decision = "short"

    return (symbol, decision, result["explain"])


def filter_by_basic(markets, fetch_func, timeframe, limit, mode, lookback_cross):
    results = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {}
        for item in markets:
            s, v = item[0], item[1]
            fut = executor.submit(
                evaluate_basic, fetch_func, s, timeframe, limit, lookback_cross
            )
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
