from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import numpy as np


def get_vol_metrics(fetch_func, symbol, timeframe, limit):
    """
    변동성 필터 전용: ATR + 밴드폭 + 점수 (정규화된 버전)
    - ATR14: 이미 현재가 대비 백분율(%)로 계산됨
    - BB_width: 이미 SMA 대비 백분율(%)로 계산됨
    - score: 두 백분율을 합산하여 동일 스케일로 비교
    """
    df = fetch_func(symbol, timeframe, limit)
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


# 변동성 점수와 거래대금 점수를 합하여 좋은 절반 필터링
def filter_by_volatility(markets, fetch_func, timeframe, limit):
    scored = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {
            executor.submit(get_vol_metrics, fetch_func, s, timeframe, limit): (s, v)
            for (s, v) in markets
        }
        for fut in as_completed(futures):
            res = fut.result()
            if res:
                atr, band_width, vol_score = res
                s, v = futures[fut]

                # 최종 점수 = (ATR + 밴드폭) × log(1 + 거래대금)
                liquidity = np.log1p(v)  # log(1+거래대금)
                final_score = vol_score * liquidity

                scored.append((s, v, atr, band_width, final_score))

    # 최종 점수 기준 정렬
    scored.sort(key=lambda x: x[4], reverse=True)
    half = max(1, len(scored) // 2)
    return scored[:half]
