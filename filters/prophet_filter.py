import random
from utils.price_forecast import run_prophet_analysis
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.discord_msg import notify_error


def analyze_with_prophet(filtered, fetch_func, timeframe, limit, direction):
    prophet_results = []

    def worker(item):
        s = item["symbol"]
        v = item["volume"]
        decision = item["signal"].upper()
        info = item["info"]

        # LONG/SHORT 사전 필터링
        if direction == "long" and decision != "LONG":
            return None
        if direction == "short" and decision != "SHORT":
            return None

        try:
            # ohlcv 캐시 우선
            df = item.get("ohlcv")
            if df is None:
                df = fetch_func(s, timeframe, limit)

            if df is None or "close" not in df.columns:
                return None

            df_for_prophet = df.rename(columns={"close": "y"})[["ds", "y"]]
            results = run_prophet_analysis(
                df_for_prophet, forecast_hours=24, freq="15min"
            )

            forecast_summary = results["forecast_summary"]
            last_price = info.get("last_close")

            future_part = forecast_summary.tail(24)

            last_yhat = future_part["예측가격(중앙값, USDT)"].iloc[-1]
            lower = future_part["예상최저가(USDT)"].iloc[-1]
            upper = future_part["예상최고가(USDT)"].iloc[-1]
            avg_yhat = future_part["예측가격(중앙값, USDT)"].mean()
            max_yhat = future_part["예측가격(중앙값, USDT)"].max()
            min_yhat = future_part["예측가격(중앙값, USDT)"].min()

            start_yhat = future_part["예측가격(중앙값, USDT)"].iloc[0]
            trend_dir = "상승" if last_yhat > start_yhat else "하락"

            trend = results["trend_summary"].iloc[-1]["추세선(USDT)"]
            mape = results["performance_summary"].iloc[0]["평균절대백분율오차(MAPE)"]

            record = {
                "symbol": s,
                "volume": v,
                "signal": decision,
                "last_price": last_price,
                "forecast_yhat": last_yhat,
                "forecast_lower": lower,
                "forecast_upper": upper,
                "forecast_avg": avg_yhat,
                "forecast_max": max_yhat,
                "forecast_min": min_yhat,
                "forecast_trend_dir": trend_dir,
                "trend": trend,
                "mape": mape,
                "raw": results,
            }
            record.update(info)
            return record

        except Exception as e:
            notify_error(f"{s} Prophet 분석 실패: {e}")
            return None

    # 병렬 실행
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(worker, item) for item in filtered]
        for fut in as_completed(futures):
            res = fut.result()
            if res:
                prophet_results.append(res)

    return prophet_results


# 후보 선정 함수
def select_trading_candidates(results):
    final_candidates = []

    for r in results:
        try:
            base_score = 0
            bonus_score = 0
            signal = r.get("signal")
            price = r.get("last_price")
            yhat = r.get("forecast_yhat")
            lower = r.get("forecast_lower")
            upper = r.get("forecast_upper")
            trend = r.get("trend")
            mape = r.get("mape", 1.0)

            # 핵심 점수 계산 (기존 로직 강화)
            if signal == "LONG" and r.get("trend_up", False):
                base_score += 3  # 기본 추세 일치 중요도 증가
            if signal == "SHORT" and r.get("trend_down", False):
                base_score += 3

            if signal == "LONG" and r.get("macd_bull", False):
                base_score += 1
            if signal == "SHORT" and r.get("macd_bear", False):
                base_score += 1

            # 리스크 구간 평가 개선
            if lower and upper and price:
                range_position = (
                    (price - lower) / (upper - lower) if upper != lower else 0.5
                )
                if signal == "LONG" and 0.1 <= range_position <= 0.5:  # 하단 진입 유리
                    base_score += 1
                    bonus_score += 0.5
                elif (
                    signal == "SHORT" and 0.5 <= range_position <= 0.9
                ):  # 상단 진입 유리
                    base_score += 1
                    bonus_score += 0.5
                elif lower <= price <= upper:  # 기본 구간 내
                    base_score += 1

            # 예측 방향성 일치
            if signal == "LONG" and r.get("forecast_trend_dir") == "상승":
                base_score += 3
            if signal == "SHORT" and r.get("forecast_trend_dir") == "하락":
                base_score += 3

            # RSI 과매수/과매도 활용
            rsi = r.get("last_RSI14", 50)
            if signal == "LONG" and rsi < 35:  # 과매도에서 매수
                bonus_score += 1
            elif signal == "SHORT" and rsi > 65:  # 과매수에서 매도
                bonus_score += 1

            # 최종 점수
            final_score = round(base_score + bonus_score, 1)

            candidate = {
                "종목": r.get("symbol"),
                "신호": "매수(LONG)" if signal == "LONG" else "매도(SHORT)",
                "현재가": price,
                "예측가": {
                    "중앙값": yhat,
                    "최저": lower,
                    "최고": upper,
                    "평균": r.get("forecast_avg"),
                    "최댓값": r.get("forecast_max"),
                    "최솟값": r.get("forecast_min"),
                    "예측범위폭": (
                        round((upper - lower), 2) if upper and lower else None
                    ),
                    "진입위치": (
                        f"{round(range_position*100, 1)}%"
                        if "range_position" in locals()
                        else None
                    ),
                },
                "추천전략": {
                    "매수권장가": (
                        (min(lower, price), min(yhat, price))
                        if lower and yhat and price
                        else None
                    ),
                    "매도권장가": (
                        (max(yhat, price), upper) if yhat and upper and price else None
                    ),
                    "예측수익률": (
                        f"{round((upper - price)/price*100, 1)}%"
                        if upper and price
                        else None
                    ),
                },
                "추세": {
                    "기본필터_추세상승": r.get("trend_up"),
                    "기본필터_추세하락": r.get("trend_down"),
                    "Prophet_추세선": trend,
                    "예측구간_방향성": r.get("forecast_trend_dir"),
                },
                "보조지표": {
                    "RSI14": rsi,
                    "RSI상태": (
                        "과매도" if rsi < 30 else "과매수" if rsi > 70 else "중립"
                    ),
                    "MACD": r.get("last_MACD"),
                    "MACD_시그널": r.get("last_MACD_signal"),
                    "OBV": r.get("last_OBV"),
                },
                "예측성능": {
                    "MAPE": round(mape, 3),
                },
                "_점수": final_score,
            }
            final_candidates.append(candidate)

        except Exception as e:
            notify_error(f"Candidate filter error on {r.get('symbol')}: {e}")

    final_candidates = sorted(final_candidates, key=lambda x: x["_점수"], reverse=True)
    top_candidates = final_candidates[:5]

    # 점수 제거 (AI에게 점수 기반 판단 내리지 않게)
    for c in top_candidates:
        c.pop("_점수", None)

    random.shuffle(top_candidates)

    return top_candidates
