from filters.main_filter import run_filters, fetch_ohlcv

final_candidates = run_filters(
    fetch_ohlcv=fetch_ohlcv,
    timeframe="15m",
    limit=1000,
    mode="both",
    lookback_cross=3,
    direction="long",
)

print(f"\n최종 후보 종목 수: {len(final_candidates)}\n")
for c in final_candidates:
    print("=" * 70)
    print(f"종목: {c['종목']}")
    print(
        f"신호: {c['신호']} | 총점수: {c['점수']} (기본: {c['기본점수']}, 보너스: {c['보너스점수']})"
    )
    print(f"현재가: {c['현재가']:.6f}")
    print()

    # 예측가
    예측가 = c["예측가"]
    print("예측가")
    print(f"   ├─ 중앙값: {예측가['중앙값']:.6f}")
    print(f"   ├─ 최저: {예측가['최저']:.6f}")
    print(f"   ├─ 최고: {예측가['최고']:.6f}")
    print(f"   ├─ 평균: {예측가['평균']:.6f}")
    print(f"   ├─ 최댓값: {예측가['최댓값']:.6f}")
    print(f"   ├─ 최솟값: {예측가['최솟값']:.6f}")
    print(f"   ├─ 예측범위폭: {예측가['예측범위폭']}")
    if 예측가["진입위치"]:
        print(f"   └─ 현재 진입위치: {예측가['진입위치']} (구간 내)")
    else:
        print(f"   └─ 현재 진입위치: 구간 외")
    print()

    # 추천 전략
    전략 = c["추천전략"]
    print("추천전략")
    if 전략["매수권장가"]:
        print(
            f"   ├─ 매수 권장 구간: {전략['매수권장가'][0]:.6f} ~ {전략['매수권장가'][1]:.6f}"
        )
    if 전략["매도권장가"]:
        print(
            f"   ├─ 매도 권장 구간: {전략['매도권장가'][0]:.6f} ~ {전략['매도권장가'][1]:.6f}"
        )
    if 전략["예측수익률"]:
        print(f"   └─ 예측 수익률: {전략['예측수익률']}")
    else:
        print("   └─ 예측 수익률: 계산 불가")
    print()

    # 추세
    추세 = c["추세"]
    print("추세 분석")
    print(f"   ├─ 기본필터 추세상승: {추세['기본필터_추세상승']}")
    print(f"   ├─ 기본필터 추세하락: {추세['기본필터_추세하락']}")
    print(f"   ├─ Prophet 추세선: {추세['Prophet_추세선']:.6f}")
    print(f"   └─ 예측구간 방향성: {추세['예측구간_방향성']}")
    print()

    # 보조지표
    보조 = c["보조지표"]
    print("보조지표")
    print(f"   ├─ RSI14: {보조['RSI14']:.2f} ({보조['RSI상태']})")
    print(f"   ├─ MACD: {보조['MACD']:.6f}")
    print(f"   ├─ MACD 시그널: {보조['MACD_시그널']:.6f}")
    print(f"   ├─ OBV: {보조['OBV']:.6f}")
    print()

    # 예측 성능
    성능 = c["예측성능"]
    print("예측 성능")
    print(f"   ├─ MAPE: {성능['MAPE']:.4f}")

    print("=" * 70)
    print()
