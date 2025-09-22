from filters.main_filter import run_filters, fetch_ohlcv
from utils.price_forecast import run_prophet_analysis

# 기본 필터 실행
filtered = run_filters(
    fetch_ohlcv, timeframe="15m", limit=200, mode="both", lookback_cross=5
)


def analyze_with_prophet(filtered, fetch_func, timeframe="15m", limit=200):
    """
    기본 필터 통과 종목에 대해 Prophet 분석 실행
    """
    prophet_results = []

    for item in filtered:  # dict 기반 루프
        s = item["symbol"]
        v = item["volume"]
        decision = item["signal"]
        info = item["info"]

        try:
            # ohlcv는 캐시에서 우선 가져오기
            df = item.get("ohlcv")
            if df is None:
                df = fetch_func(s, timeframe, limit)

            if df is None or "close" not in df.columns:
                continue

            df_for_prophet = df.rename(columns={"close": "y"})[["ds", "y"]]
            results = run_prophet_analysis(df_for_prophet, forecast_hours=24, freq="h")

            # === 예측 요약값 추출 ===
            forecast_summary = results["forecast_summary"]
            last_price = info.get("last_close")

            # 미래 24시간 데이터만 추출
            future_part = forecast_summary.tail(24)

            # 📌 다양한 요약값
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

            # === record 구성 ===
            record = {
                "symbol": s,
                "volume": v,
                "signal": decision.upper(),
                "last_price": last_price,
                # Prophet 기반 예측 요약
                "forecast_yhat": last_yhat,
                "forecast_lower": lower,
                "forecast_upper": upper,
                "forecast_avg": avg_yhat,
                "forecast_max": max_yhat,
                "forecast_min": min_yhat,
                "forecast_trend_dir": trend_dir,
                # 추세/성능
                "trend": trend,
                "mape": mape,
                "raw": results,
            }
            record.update(info)  # 보조지표/추세 정보 추가

            prophet_results.append(record)

        except Exception as e:
            print(f"{s} Prophet 분석 실패: {e}")

    return prophet_results


# === Prophet 분석 실행 ===
prophet_pass = analyze_with_prophet(
    filtered, fetch_func=fetch_ohlcv, timeframe="15m", limit=200
)


# === 후보 선정 함수 ===
def select_trading_candidates(results):
    final_candidates = []

    for r in results:
        try:
            score = 0
            signal = r.get("signal")
            price = r.get("last_price")
            yhat = r.get("forecast_yhat")
            lower = r.get("forecast_lower")
            upper = r.get("forecast_upper")
            trend = r.get("trend")
            mape = r.get("mape", 1.0)

            # === 점수 계산 ===
            if signal == "LONG" and r.get("trend_up", False):
                score += 2
            if signal == "SHORT" and r.get("trend_down", False):
                score += 2
            if (
                signal == "LONG"
                and yhat
                and price
                and trend
                and yhat > price
                and trend > price
            ):
                score += 2
            if (
                signal == "SHORT"
                and yhat
                and price
                and trend
                and yhat < price
                and trend < price
            ):
                score += 2
            if signal == "LONG" and r.get("macd_bull", False):
                score += 1
            if signal == "SHORT" and r.get("macd_bear", False):
                score += 1
            if mape < 0.1:
                score += 1
            if lower and upper and price and lower <= price <= upper:
                score += 1

            # 추가 활용 가능: 구간 방향성 / 평균 / 최댓값 / 최솟값
            if signal == "LONG" and r.get("forecast_trend_dir") == "상승":
                score += 1
            if signal == "SHORT" and r.get("forecast_trend_dir") == "하락":
                score += 1
            
            candidate = {
                "종목": r.get("symbol"),
                "신호": "매수(LONG)" if signal == "LONG" else "매도(SHORT)",
                "점수": score,
                "현재가": price,
                "예측가": {
                    "중앙값": yhat,
                    "최저": lower,
                    "최고": upper,
                    "평균": r.get("forecast_avg"),
                    "최댓값": r.get("forecast_max"),
                    "최솟값": r.get("forecast_min"),
                    "예측범위폭": (upper - lower) if upper and lower else None,
                },
                "추천전략": {
                    "매수권장가": (
                        (lower, yhat)
                        if signal == "LONG" and lower and yhat
                        else None
                    ),
                    "매도권장가": (
                        (yhat, upper)
                        if signal == "SHORT" and yhat and upper
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
                    "RSI14": r.get("last_RSI14"),
                    "MACD": r.get("last_MACD"),
                    "MACD_시그널": r.get("last_MACD_signal"),
                    "OBV": r.get("last_OBV"),
                },
                "예측성능": {
                    "MAPE(평균절대백분율오차)": mape,
                    "신뢰도등급": (
                        "높음" if mape < 0.1 else "보통" if mape < 0.2 else "낮음"
                    ),
                },
            }
            final_candidates.append(candidate)

        except Exception as e:
            print(f"Candidate filter error on {r.get('symbol')}: {e}")

    # === 점수 순 정렬 ===
    final_candidates = sorted(final_candidates, key=lambda x: x["점수"], reverse=True)

    # === 후보 개수 제한 ===
    if len(final_candidates) > 5:
        return final_candidates[:5]
    else:
        return final_candidates


# === 최종 후보 출력 ===
final_candidates = select_trading_candidates(prophet_pass)

if not final_candidates:
    print("⚠️ 조건을 만족하는 후보가 없습니다.")
else:
    for c in final_candidates:
        print("=" * 60)
        print(f"📌 종목: {c['종목']}")
        print(f"🔔 신호: {c['신호']} | 점수: {c['점수']}")
        print(f"💰 현재가: {c['현재가']:.6f}")
        print()

        # 예측가
        예측가 = c["예측가"]
        print("📊 예측가")
        print(f"   ├─ 중앙값: {예측가['중앙값']:.6f}")
        print(f"   ├─ 최저: {예측가['최저']:.6f}")
        print(f"   ├─ 최고: {예측가['최고']:.6f}")
        print(f"   ├─ 평균: {예측가['평균']:.6f}")
        print(f"   ├─ 최댓값: {예측가['최댓값']:.6f}")
        print(f"   ├─ 최솟값: {예측가['최솟값']:.6f}")
        print(f"   └─ 예측범위폭: {예측가['예측범위폭']:.6f}")
        print()

        # 추천 전략
        전략 = c["추천전략"]
        print("📈 추천전략")
        if 전략["매수권장가"]:
            print(
                f"   └─ 매수 권장 구간: {전략['매수권장가'][0]:.6f} ~ {전략['매수권장가'][1]:.6f}"
            )
        if 전략["매도권장가"]:
            print(
                f"   └─ 매도 권장 구간: {전략['매도권장가'][0]:.6f} ~ {전략['매도권장가'][1]:.6f}"
            )
        if not any(전략.values()):
            print("   └─ 특별한 권장 전략 없음")
        print()

        # 추세
        추세 = c["추세"]
        print("📉 추세")
        print(f"   ├─ 기본필터 추세상승: {추세['기본필터_추세상승']}")
        print(f"   ├─ 기본필터 추세하락: {추세['기본필터_추세하락']}")
        print(f"   ├─ Prophet 추세선: {추세['Prophet_추세선']:.6f}")
        print(f"   └─ 예측구간 방향성: {추세['예측구간_방향성']}")
        print()

        # 보조지표
        보조 = c["보조지표"]
        print("📑 보조지표")
        print(f"   ├─ RSI14: {보조['RSI14']:.2f}")
        print(f"   ├─ MACD: {보조['MACD']:.6f}")
        print(f"   ├─ MACD 시그널: {보조['MACD_시그널']:.6f}")
        print(f"   └─ OBV: {보조['OBV']:.6f}")
        print()

        # 예측 성능
        성능 = c["예측성능"]
        print("🎯 예측 성능")
        print(f"   ├─ MAPE(평균절대백분율오차): {성능['MAPE(평균절대백분율오차)']:.4f}")
        print(f"   └─ 신뢰도 등급: {성능['신뢰도등급']}")
        print("=" * 60)
        print()
