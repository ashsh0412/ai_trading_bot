import ccxt
import pandas as pd
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics

binance = ccxt.binance()

# 코인 심볼과 타임프레임 설정
symbol = "BTC/USDT"
timeframe = "1h"

# 최근 2000개 1시간 봉 데이터 가져오기 (약 83일치)
ohlcv = binance.fetch_ohlcv(symbol, timeframe=timeframe, limit=2000)

# DataFrame 변환
df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
df["ds"] = pd.to_datetime(df["timestamp"], unit="ms")
df["y"] = df["close"]

# Prophet 모델 학습
m = Prophet(
    interval_width=0.95,
    changepoint_prior_scale=0.1,
    weekly_seasonality=True,
    daily_seasonality=True
)
m.fit(df[["ds", "y"]])

# ① 향후 24시간 예측
future = m.make_future_dataframe(periods=24, freq="h")
forecast = m.predict(future)

# ② Cross Validation (성능 평가용)
df_cv = cross_validation(m, initial="480 hours", period="24 hours", horizon="72 hours")
df_p = performance_metrics(df_cv)

# === 결과 출력 ===
print("\n[1] Prophet 예측 결과 (최근 10개)")
print(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
      .tail(10)
      .rename(columns={
          'ds': '날짜',
          'yhat': '예측가격(중앙값, USDT)',
          'yhat_lower': '예상최저가(USDT)',
          'yhat_upper': '예상최고가(USDT)'
      }).to_string(index=False))

print("\n[2] 추세 (Trend) 구성 요소 (최근 10개)")
print(forecast[['ds', 'trend']]
      .tail(10)
      .rename(columns={
          'ds': '날짜',
          'trend': '추세선(USDT)'
      }).to_string(index=False))

print("\n[3] 감지된 변곡점 (Changepoints, 최근 10개)")
print(m.changepoints.tail(10).to_frame(name="변곡점 발생 시점").to_string(index=False))

print("\n[4] 불확실성 구간 (최근 5개)")
uncertainty = forecast[['ds', 'yhat_lower', 'yhat_upper']].tail(5)
uncertainty['예측범위폭(USDT)'] = uncertainty['yhat_upper'] - uncertainty['yhat_lower']
print(uncertainty.rename(columns={
    'ds': '날짜',
    'yhat_lower': '예상최저가(USDT)',
    'yhat_upper': '예상최고가(USDT)'
}).to_string(index=False))

print("\n[5] 교차 검증 성능 지표 (앞 5개)")
print(df_p[['horizon', 'mse', 'rmse', 'mae', 'mape', 'coverage']]
      .head()
      .rename(columns={
          'horizon': '예측기간',
          'mse': '평균제곱오차(MSE)',
          'rmse': '제곱근오차(RMSE)',
          'mae': '절대오차(MAE)',
          'mape': '평균절대백분율오차(MAPE)',
          'coverage': '신뢰구간포함비율'
      }).to_string(index=False))