import os
from dotenv import load_dotenv
import google.genai as genai
from google.genai import types

load_dotenv()

# 환경변수에서 API 키 읽기
api_key = os.getenv("GEMINI_API_KEY")

# 클라이언트 초기화
client = genai.Client(api_key=api_key)

# 요청 보내기
response = client.models.generate_content(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(
        system_instruction="You are an AI investment assistant.",
    ),
    contents=[
        {
            "role": "model",
            "parts": [
                {
                    "text": (
                        "You are an AI investment assistant. "
                        "Always answer concisely in 2 short sentences maximum."
                    )
                }
            ],
        },
        {
            "role": "user",
            "parts": [{"text": "As an AI investor, how would you invest?"}],
        },
    ],
)

print(response.text)
