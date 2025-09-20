import ccxt
import pandas as pd
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics

# 출력 옵션 설정
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)


# 데이터 준비
def prepare_data(symbol, timeframe, limit):

    binance = ccxt.binance()
    ohlcv = binance.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    df = pd.DataFrame(
        ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
    )

    df["ds"] = pd.to_datetime(df["timestamp"], unit="ms")
    df["y"] = df["close"]
    return df


# 모델 학습
def train_model(df):
    m = Prophet(
        interval_width=0.95,
        changepoint_prior_scale=0.1,
        weekly_seasonality=True,
        daily_seasonality=True,
    )
    m.fit(df[["ds", "y"]])
    return m


# 예측
def get_forecast(m, periods, freq):
    """
    학습된 모델을 바탕으로 미래 데이터 예측
    - periods: 예측할 구간 개수
    - freq: 예측 단위 ("h"=시간, "d"=일)
    """
    future = m.make_future_dataframe(periods=periods, freq=freq)
    forecast = m.predict(future)
    return forecast


# 예측 결과 요약
def get_forecast_summary(forecast, tail=10):
    """예측값 (중앙값/최저/최고) 최근 tail개"""
    return (
        forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]]
        .tail(tail)
        .rename(
            columns={
                "ds": "날짜",
                "yhat": "예측가격(중앙값, USDT)",
                "yhat_lower": "예상최저가(USDT)",
                "yhat_upper": "예상최고가(USDT)",
            }
        )
    )


# 추세 요약
def get_trend_summary(forecast, tail=10):
    """추세선(Trend) 최근 tail개"""
    return (
        forecast[["ds", "trend"]]
        .tail(tail)
        .rename(columns={"ds": "날짜", "trend": "추세선(USDT)"})
    )


# 불확실성 구간 요약
def get_uncertainty_summary(forecast, tail=10):
    """예측 불확실성 구간 (최저~최고 범위폭)"""
    uncertainty = forecast[["ds", "yhat_lower", "yhat_upper"]].tail(tail).copy()
    uncertainty["예측범위폭(USDT)"] = (
        uncertainty["yhat_upper"] - uncertainty["yhat_lower"]
    )
    return uncertainty.rename(
        columns={
            "ds": "날짜",
            "yhat_lower": "예상최저가(USDT)",
            "yhat_upper": "예상최고가(USDT)",
        }
    )


# 변곡점 요약
def get_changepoints_summary(model, tail=10):
    """모델이 감지한 추세 변곡점 최근 tail개"""
    return model.changepoints.tail(tail).to_frame(name="변곡점 발생 시점")


# 교차 검증 실행 및 요약
def get_cross_validation_results(
    m, initial="480 hours", period="24 hours", horizon="72 hours", head=10
):
    """
    Prophet 교차 검증 실행 + 요약
    - summary_type: "performance" (성능지표), "cv" (예측값 vs 실제), "both" (둘 다)
    """
    df_cv = cross_validation(m, initial=initial, period=period, horizon=horizon)
    df_p = performance_metrics(df_cv)

    results = {
        "cv_summary": df_cv.rename(
            columns={
                "ds": "예측시점",
                "yhat": "예측값",
                "yhat_lower": "예측 하한",
                "yhat_upper": "예측 상한",
                "y": "실제값",
                "cutoff": "학습종료시점",
            }
        ).head(head),
        "performance_summary": df_p.rename(
            columns={
                "horizon": "예측기간",
                "mse": "평균제곱오차(MSE)",
                "rmse": "제곱근오차(RMSE)",
                "mae": "절대오차(MAE)",
                "mape": "평균절대백분율오차(MAPE)",
                "coverage": "신뢰구간포함비율",
            }
        ).head(head),
    }

    return results


# [메인 실행 함수]
def run_prophet_analysis(symbol, timeframe, limit, forecast_hours):

    # 1. 데이터 준비
    df = prepare_data(symbol, timeframe, limit)

    # 2. 모델 학습
    model = train_model(df)

    # 3. 예측
    forecast = get_forecast(model, forecast_hours, "h")

    # 4. 교차 검증 (성능 + 예측 요약 한 번에)
    cv_results = get_cross_validation_results(model)

    # 5. 결과 요약 리턴
    results = {
        "forecast_summary": get_forecast_summary(forecast),  # [1] 예측 결과
        "trend_summary": get_trend_summary(forecast),  # [2] 추세
        "changepoints_summary": get_changepoints_summary(model),  # [3] 변곡점
        "uncertainty_summary": get_uncertainty_summary(forecast),  # [4] 불확실성
        "performance_summary": cv_results["performance_summary"],  # [5] 성능 지표
        "cross_validation_summary": cv_results["cv_summary"],  # [6] 교차 검증 요약
    }
    return results


# 실행 예시
"""
- symbol: 거래쌍 (BTC/USDT 등)
- timeframe: 캔들 간격 ("1h", "1d", "5m" 등)
- limit: 가져올 캔들 개수
- forecast_hours: 예측할 시간 구간 (예: 24=24시간 후까지 예측)
"""
results = run_prophet_analysis(
    symbol="BTC/USDT", timeframe="1h", limit=2000, forecast_hours=24
)

print("\n[1] 예측 결과")
print(results["forecast_summary"])

print("\n[2] 추세")
print(results["trend_summary"])

print("\n[3] 변곡점")
print(results["changepoints_summary"])

print("\n[4] 불확실성 구간")
print(results["uncertainty_summary"])

print("\n[5] 성능 지표")
print(results["performance_summary"])

print("\n[6] 교차 검증 요약")
print(results["cross_validation_summary"])
