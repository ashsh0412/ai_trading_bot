import ccxt
import pandas as pd
import numpy as np

# SMA (Simple Moving Average) → 단순 이동평균
# 최근 N일(캔들)의 가격 평균. 추세 방향을 부드럽게 보여줌.
def SMA(series, window=14):
    return series.rolling(window=window).mean()


# EMA (Exponential Moving Average) → 지수 이동평균
# 최근 데이터에 더 큰 가중치를 주어 변화에 빠르게 반응.
def EMA(series, window=14):
    return series.ewm(span=window, adjust=False).mean()


# RSI (Relative Strength Index)
# 0~100 값으로 현재 가격이 "과매수(70 이상)" 또는 "과매도(30 이하)" 상태인지 알려줌.
# 70 이상 → 너무 많이 올랐으니 매도 위험
# 30 이하 → 너무 많이 떨어졌으니 반등 가능성 (매수 기회)
def RSI(series, window=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


# MACD (Moving Average Convergence Divergence)
# 단기 EMA와 장기 EMA 차이를 이용해 추세 전환을 탐지.
# MACD > Signal → 매수 신호 (골든크로스)
# MACD < Signal → 매도 신호 (데드크로스)
def MACD(series, short=12, long=26, signal=9):
    ema_short = EMA(series, short)
    ema_long = EMA(series, long)
    macd = ema_short - ema_long
    signal_line = EMA(macd, signal)
    hist = macd - signal_line
    return macd, signal_line, hist


# Bollinger Bands (볼린저 밴드)
# 가격이 평균(SMA) 대비 위·아래로 얼마나 벗어났는지 확인.
# 상단선 터치 → 과열 (매도 가능성)
# 하단선 터치 → 저평가 (매수 가능성)
def Bollinger_Bands(series, window=20, num_std=2):
    sma = SMA(series, window)
    rolling_std = series.rolling(window=window).std()
    upper = sma + (rolling_std * num_std)
    lower = sma - (rolling_std * num_std)
    return upper, sma, lower


# ATR (Average True Range)
# 변동성 지표. 값이 크면 변동성 ↑ (위험 크고 수익도 클 수 있음)
# 값이 작으면 변동성 ↓ (안정적)
def ATR(df, window=14):
    high_low = df["high"] - df["low"]
    high_close = np.abs(df["high"] - df["close"].shift())
    low_close = np.abs(df["low"] - df["close"].shift())

    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)

    atr = true_range.rolling(window=window).mean()
    return atr


# OBV (On-Balance Volume)
# 거래량 기반 추세 확인 지표.
# 가격이 오르면 거래량을 더하고, 내리면 빼서 누적.
# 가격과 OBV가 같은 방향 → 추세 신뢰 ↑
# 가격은 오르는데 OBV는 하락 → 추세 약화 (경고 신호)
def OBV(df):
    obv = [0]
    for i in range(1, len(df)):
        if df["close"][i] > df["close"][i - 1]:
            obv.append(obv[-1] + df["volume"][i])
        elif df["close"][i] < df["close"][i - 1]:
            obv.append(obv[-1] - df["volume"][i])
        else:
            obv.append(obv[-1])
    return pd.Series(obv, index=df.index)


# ADX (Average Directional Index)
# 추세의 강도만 보여주는 지표 (방향 X).
# 0~100 사이 값:
# 0~20 → 추세 약함
# 20~40 → 추세 보통
# 40 이상 → 강한 추세
def ADX(df, window=14):
    df["TR"] = np.maximum(
        df["high"] - df["low"],
        np.maximum(
            abs(df["high"] - df["close"].shift()), abs(df["low"] - df["close"].shift())
        ),
    )
    df["+DM"] = np.where(
        (df["high"] - df["high"].shift()) > (df["low"].shift() - df["low"]),
        np.maximum(df["high"] - df["high"].shift(), 0),
        0,
    )
    df["-DM"] = np.where(
        (df["low"].shift() - df["low"]) > (df["high"] - df["high"].shift()),
        np.maximum(df["low"].shift() - df["low"], 0),
        0,
    )

    tr_smooth = df["TR"].rolling(window=window).mean()
    plus_di = 100 * (df["+DM"].rolling(window=window).mean() / tr_smooth)
    minus_di = 100 * (df["-DM"].rolling(window=window).mean() / tr_smooth)
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.rolling(window=window).mean()
    return adx


# === 메인 함수 ===
def get_indicators(symbol, timeframe, limit):
    binance = ccxt.binance()
    ohlcv = binance.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(
        ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    df["ds"] = pd.to_datetime(df["timestamp"], unit="ms")

    # 지표 계산
    df["SMA20"] = SMA(df["close"], 20)               # 20기간 단순이동평균 (최근 20봉 종가 평균)
    df["EMA20"] = EMA(df["close"], 20)               # 20기간 지수이동평균 (최근 데이터에 가중치)
    df["RSI14"] = RSI(df["close"], 14)               # 14기간 RSI (과매수/과매도 지표, 70↑ 과열 / 30↓ 침체)

    df["MACD"], df["MACD_signal"], df["MACD_hist"] = MACD(df["close"])
    # MACD: 단기 EMA - 장기 EMA
    # MACD_signal: MACD의 9기간 EMA (시그널선)
    # MACD_hist: MACD - 시그널선 (히스토그램, 추세강도)

    df["BB_upper"], df["BB_mid"], df["BB_lower"] = Bollinger_Bands(df["close"])
    # BB_upper: 볼린저밴드 상단 (과열 구간)
    # BB_mid: 중심선 (20기간 SMA)
    # BB_lower: 볼린저밴드 하단 (저평가 구간)

    df["ATR14"] = ATR(df, 14)                        # 14기간 ATR (평균 변동성, 값 클수록 변동성 큼)
    df["OBV"] = OBV(df)                              # OBV (거래량 기반 누적 지표, 추세 신뢰 확인)
    df["ADX14"] = ADX(df)                            # 14기간 ADX (추세 강도, 20↑ 추세 존재, 40↑ 강한 추세)

    # 마지막 n개 요약
    summary = df[
        [
            "ds",
            "close",
            "SMA20",
            "EMA20",
            "RSI14",
            "MACD",
            "MACD_signal",
            "MACD_hist",
            "BB_upper",
            "BB_mid",
            "BB_lower",
            "ATR14",
            "OBV",
            "ADX14",
        ]
    ].tail(100)

    return summary

summary = get_indicators("BTC/USDT", "5m", 200)
print(summary.to_string(index=False, float_format="%.2f"))