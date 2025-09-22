import os
import json
import re
import numpy as np
from dotenv import load_dotenv
import google.genai as genai
from google.genai import types
from filters.main_filter import run_filters, fetch_ohlcv

# -------------------------
# 0. 환경 변수 로드
# -------------------------
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)


# -------------------------
# 1. NumPy 타입 변환 함수
# -------------------------
def clean_numpy(obj):
    """Convert NumPy types to native Python types (for JSON serialization)."""
    if isinstance(obj, dict):
        return {k: clean_numpy(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_numpy(v) for v in obj]
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    else:
        return obj


# -------------------------
# 2. Gemini 호출 함수
# -------------------------
def ask_ai_investment(final_candidates):
    # NumPy 타입 → Python 타입 변환
    final_candidates = clean_numpy(final_candidates)

    # JSON 문자열로 변환
    candidates_str = json.dumps(final_candidates, ensure_ascii=False, indent=2)

    # Gemini 호출
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=(
                "You are an advanced AI investment assistant for a short-term trading (scalping/day trading) program. "
                "Pick ONLY ONE most promising candidate from the list. "
                "Give entry price, take-profit, stop-loss, and reasoning. "
                "Focus on short-term opportunities and risk/reward. "
                "Return pure JSON only, no extra text."
            ),
        ),
        contents=[
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            "Here are the filtered trading candidates:\n\n"
                            f"{candidates_str}\n\n"
                            "Choose the single best candidate and output in pure JSON:\n"
                            "{\n"
                            "  'symbol': 'BTC/USDT',\n"
                            "  'action': 'BUY',\n"
                            "  'entry_price': 45000,\n"
                            "  'take_profit': 48000,\n"
                            "  'stop_loss': 43000,\n"
                            "  'reason': 'Clear uptrend with strong support levels.'\n"
                            "}"
                        )
                    }
                ],
            },
        ],
    )

    # 응답 텍스트
    advice_text = response.text.strip()

    # ```json ... ``` 같은 wrapper 제거
    if advice_text.startswith("```"):
        advice_text = re.sub(r"^```[a-zA-Z]*\n", "", advice_text)
        advice_text = advice_text.strip("`").strip()

    return advice_text


# -------------------------
# 3. 실행부
# -------------------------
if __name__ == "__main__":
    # 필터 실행
    final_candidates = run_filters(
        fetch_ohlcv=fetch_ohlcv,
        timeframe="15m",
        limit=1000,
        mode="both",
        lookback_cross=3,
        direction="long",
    )

    # AI에게 투자 조언 요청
    advice_text = ask_ai_investment(final_candidates)

    print("=== AI Investment Advice (raw text) ===")
    print(advice_text)

    # JSON 파싱
    try:
        advice_json = json.loads(advice_text)
        print("\n=== Parsed JSON ===")
        print(advice_json)
    except Exception as e:
        print("\n⚠️ JSON parsing failed. Raw response shown above.")
        print("Error:", e)
