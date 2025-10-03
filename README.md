# 🤖 AI Trading Bot | AI 자동 매매 봇

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![ccxt](https://img.shields.io/badge/ccxt-Exchange%20API-20232A?style=for-the-badge)](https://github.com/ccxt/ccxt)
[![Prophet](https://img.shields.io/badge/Prophet-Time%20Series-0E76A8?style=for-the-badge)](https://facebook.github.io/prophet/)
[![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![Discord](https://img.shields.io/badge/Discord-Webhook-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.com/)
[![Binance](https://img.shields.io/badge/Binance-Spot%20Trading-FCD535?style=for-the-badge&logo=binance&logoColor=000)](https://www.binance.com/)

**Cryptocurrency Auto-Trading System**

</div>

---

## 🌟 Overview

**Development Period:** September 2025 – Present

An **AI-powered algorithmic trading bot** designed for Binance spot markets. This system combines technical analysis, time-series forecasting, and AI-driven decision-making to execute automated trades with intelligent risk management.

### 🎯 What Makes This Bot Special?

- **Multi-Stage Filtering Pipeline**: Progressive filtering from 100+ symbols to high-probability candidates
- **AI-Powered Decision Making**: Gemini 2.5 Flash analyzes market data and generates structured trade plans
- **Prophet Forecasting**: Facebook Prophet model validates short-term trends with quality metrics
- **Automated Execution**: Complete order lifecycle management with OCO, TP/SL support
- **Real-Time Monitoring**: Instant Discord notifications for trades, errors, and portfolio updates

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        🔄 Main Loop (3min)                       │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│  Stage 1: Market Scanning                                     │
│  • Top 100 by 24h volume                                         │
│  • Volatility ranking (top 50%)                                  │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│  Stage 2: Technical Analysis                                  │
│  • MACD crossover detection                                      │
│  • RSI divergence analysis                                       │
│  • Support/Resistance levels                                     │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│  Stage 3: Prophet Forecasting                                 │
│  • Short-term trend prediction                                   │
│  • MAPE quality validation                                       │
│  • Confidence scoring                                            │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│  Stage 4: AI Decision Engine (Gemini 2.5)                     │
│  • Candidate evaluation                                          │
│  • Risk/Reward calculation                                       │
│  • JSON trade plan generation                                    │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│  Stage 5: Order Execution                                     │
│  • Balance verification (min $5 USDT)                            │
│  • Market compatibility check                                    │
│  • OCO/TP/SL order placement                                     │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│  Stage 6: Notification & Monitoring                           │
│  • Discord trade alerts                                          │
│  • Error reporting                                               │
│  • Portfolio snapshots                                           │
└──────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

### 🎯 Intelligent Filtering System

**Volume & Volatility Analysis**
- Scans top 100 symbols by 24-hour trading volume
- Filters for optimal volatility range to identify active markets
- Caches OHLCV data for efficient processing

**Technical Indicator Screening**
- MACD momentum and crossover detection
- RSI divergence identification
- Customizable lookback periods for signal validation

### 🔮 Prophet-Based Forecasting

**Time Series Analysis**
- Short-term trend prediction using Facebook Prophet
- Quality metrics (MAPE) to filter low-confidence forecasts
- Direction-aware candidate selection (long/short)

### 🤖 AI-Driven Trade Planning

**Gemini 2.5 Flash Integration**
- Analyzes filtered candidates with market context
- Generates structured JSON trade plans
- Includes entry price, take profit, stop loss, and reasoning

**Sample AI Output:**
```json
{
  "symbol": "BTC/USDT",
  "action": "BUY",
  "entry_price": 45000,
  "take_profit": 48000,
  "stop_loss": 43000,
  "reason": "Clear uptrend with strong support at 44k. MACD bullish crossover confirmed."
}
```

## 🛠️ Tech Stack

<table>
<tr>
<td>

**Core**
- Python 3.10+
- ccxt (Binance API)
- pandas & numpy

</td>
<td>

**Analysis**
- Prophet (forecasting)
- NumPy computations

</td>
<td>

**AI & Integration**
- Google Gemini 2.5
- Discord Webhooks

</td>
</tr>
</table>

---

### Filtering Pipeline Details

1. Fetches top 100 markets by volume
2. Applies volatility filter (top 50%)
3. Runs technical indicator screening (MACD + RSI)
4. Performs Prophet analysis on qualified candidates
5. Returns enriched data with signals and forecasts

### AI Decision Engine

- Converts NumPy types to JSON-serializable formats
- Sends enriched candidate data to Gemini 2.5 Flash
- Receives structured trade plan with risk parameters
- Validates JSON format and extracts clean output

---

## 📈 Performance Considerations

### Efficiency Optimizations
- **OHLCV caching** reduces redundant API calls
- **Progressive filtering** narrows candidates early
- **Batch processing** for technical indicators

### Risk Controls
- **Balance guards** prevent over-leveraging
- **MAPE thresholds** filter unreliable forecasts
- **OCO orders** ensure automatic risk management
- Error notifications via Discord

---

## 🇰🇷 프로젝트 소개

**개발 기간:** 2025년 9월 – 현재

Python 기반 **바이낸스 암호화폐 거래용 AI 자동매매 시스템**입니다. 기술적 분석, 시계열 예측, AI 의사결정을 결합하여 지능적인 리스크 관리와 함께 자동화된 트레이딩을 수행합니다.

### 🎯 특별한 이유

- **다단계 필터링 파이프라인**: 100개 이상 종목에서 고확률 후보군 선별
- **AI 기반 의사결정**: Gemini 2.5가 시장 데이터를 분석하고 구조화된 매매 계획 생성
- **Prophet 예측 모델**: Facebook Prophet으로 단기 추세를 검증하고 품질 지표 적용
- **자동 주문 실행**: OCO, TP/SL을 포함한 완전한 주문 생애주기 관리
- **실시간 모니터링**: 매매, 오류, 포트폴리오 업데이트에 대한 즉각적인 Discord 알림

---

## 🔑 핵심 기능

### 지능형 필터링 시스템

**거래량 & 변동성 분석**
- 24시간 거래량 기준 상위 100개 종목 스캔
- 최적 변동성 범위 필터링으로 활성 시장 식별
- 효율적 처리를 위한 OHLCV 데이터 캐싱

**기술적 지표 스크리닝**
- MACD 모멘텀 및 크로스오버 감지
- RSI 다이버전스 식별
- 신호 검증을 위한 커스터마이징 가능한 룩백 기간

### Prophet 기반 예측

**시계열 분석**
- Facebook Prophet을 이용한 단기 추세 예측
- 낮은 신뢰도 예측 필터링을 위한 품질 지표(MAPE)
- 방향 인식 후보 선택(상승/하락)

### AI 주도 거래 계획

**Gemini 2.5 Flash 통합**
- 시장 맥락과 함께 필터링된 후보 분석
- 구조화된 JSON 거래 계획 생성
- 진입가, 익절가, 손절가, 근거 포함

### 리스크 관리

**잔고 관리**
- 최소 잔고 임계값 ($5 USDT)
- 자동 포지션 사이징
- 동시 TP/SL 실행을 위한 OCO 주문

### 모니터링 & 알림

**Discord 통합**
- 진입/청산 세부 정보가 포함된 실시간 거래 알림
- 실패한 작업에 대한 오류 알림
- 총 평가액이 포함된 포트폴리오 요약

---

## ⚠️ Disclaimer

This bot is for **educational and personal project purposes only**. Cryptocurrency trading carries substantial risk. Always test thoroughly with paper trading before using real funds. The developers assume no responsibility for financial losses.

---
