import ccxt
import pandas as pd
import numpy as np

# 출력 옵션 설정
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)


# SMA (Simple Moving Average) → 단순 이동평균
# 최근 N일(캔들)의 가격 평균. 추세 방향을 부드럽게 보여줌.
def SMA(series, window=14):
    """SMA를 현재가 대비 백분율로 정규화"""
    sma = series.rolling(window=window).mean()
    return (sma - series) / series * 100  # 현재가 대비 차이 %


# EMA (Exponential Moving Average) → 지수 이동평균
# 최근 데이터에 더 큰 가중치를 주어 변화에 빠르게 반응.
def EMA(series, window=14):
    """EMA를 현재가 대비 백분율로 정규화"""
    ema = series.ewm(span=window, adjust=False).mean()
    return (ema - series) / series * 100  # 현재가 대비 차이 %


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
    # 실제 EMA 값을 구해서 사용
    ema_short_raw = series.ewm(span=short, adjust=False).mean()
    ema_long_raw = series.ewm(span=long, adjust=False).mean()

    # 정규화된 MACD 계산
    macd = (ema_short_raw - ema_long_raw) / ema_long_raw * 100
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    hist = macd - signal_line

    return macd, signal_line, hist


# Bollinger Bands (볼린저 밴드)
# 가격이 평균(SMA) 대비 위·아래로 얼마나 벗어났는지 확인.
# 상단선 터치 → 과열 (매도 가능성)
# 하단선 터치 → 저평가 (매수 가능성)
def Bollinger_Bands(series, window=20, num_std=2):
    # 실제 SMA 값 사용
    sma_raw = series.rolling(window=window).mean()
    rolling_std = series.rolling(window=window).std()

    upper_band = sma_raw + (rolling_std * num_std)
    lower_band = sma_raw - (rolling_std * num_std)

    # SMA 기준으로 정규화
    upper = (upper_band - sma_raw) / sma_raw * 100
    lower = (lower_band - sma_raw) / sma_raw * 100
    mid = pd.Series(0, index=sma_raw.index)  # 항상 0%

    return upper, mid, lower


# ATR (Average True Range)
# 변동성 지표. 값이 크면 변동성 ↑ (위험 크고 수익도 클 수 있음)
# 값이 작으면 변동성 ↓ (안정적)
def ATR(df, window=14):
    """
    ATR (Average True Range) - 가격 대비 변동성(%)
    - 항상 현재가 대비 백분율(%) 값으로 반환
    """
    high_low = df["high"] - df["low"]
    high_close = np.abs(df["high"] - df["close"].shift())
    low_close = np.abs(df["low"] - df["close"].shift())

    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)

    atr = true_range.rolling(window=window).mean()
    atr_pct = atr / df["close"] * 100

    return atr_pct


# OBV (On-Balance Volume)
# 거래량 기반 추세 확인 지표.
# 가격이 오르면 거래량을 더하고, 내리면 빼서 누적.
# 가격과 OBV가 같은 방향 → 추세 신뢰 ↑
# 가격은 오르는데 OBV는 하락 → 추세 약화 (경고 신호)
def OBV(df):
    """
    On-Balance Volume (OBV) - 항상 거래량 기준으로 정규화된 값 반환
    - 가격이 오르면 해당 캔들의 거래량을 더하고, 내리면 빼는 누적 방식
    - 결과값을 거래량 총합으로 나누어 종목 간 비교 가능
    """
    obv = [0]
    for i in range(1, len(df)):
        if df["close"].iloc[i] > df["close"].iloc[i - 1]:
            obv.append(obv[-1] + df["volume"].iloc[i])
        elif df["close"].iloc[i] < df["close"].iloc[i - 1]:
            obv.append(obv[-1] - df["volume"].iloc[i])
        else:
            obv.append(obv[-1])

    obv_series = pd.Series(obv, index=df.index)

    # 항상 정규화 (거래량 총합 대비 %)
    obv_series = obv_series / df["volume"].sum() * 100

    return obv_series


# === 메인 함수 ===
def get_indicators(symbol, timeframe, limit):
    binance = ccxt.binance()
    ohlcv = binance.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(
        ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    df["ds"] = pd.to_datetime(df["timestamp"], unit="ms")

    # 지표 계산 (SMA, EMA, MACD, RSI, BB, ATR, OBV)
    df["SMA20"] = SMA(df["close"], 20)
    df["EMA20"] = EMA(df["close"], 20)
    df["RSI14"] = RSI(df["close"], 14)
    df["MACD"], df["MACD_signal"], df["MACD_hist"] = MACD(df["close"])
    df["BB_upper"], df["BB_mid"], df["BB_lower"] = Bollinger_Bands(df["close"])
    df["ATR14"] = ATR(df, 14)
    df["OBV"] = OBV(df)

    return df  # 전체 DataFrame 반환
