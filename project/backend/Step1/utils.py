import json
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    raise ValueError(".env 파일에 GOOGLE_API_KEY가 설정되지 않았습니다.")

my_proxy_url = "https://lucky-bush-20ba.dear-m1njn.workers.dev" 
client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(
        base_url=my_proxy_url
    )
)

model = genai.GenerativeModel('gemini-1.5-flash') #

async def analyze_description_with_gemini(description: str) -> dict:
    if not description or description == "No description available":
        return {"vibe_text": "No description available", "key_details": ""}

    prompt = f"""
    다음 상품 설명을 분석하여 'vibe_text'와 'key_details'로 분리하고, 반드시 아래 JSON 형식으로만 반환해. 마크다운 기호 없이 순수 JSON만 출력해.
    
    - vibe_text: 상품이 주는 감성, 무드, 분위기를 묘사하는 매력적인 1~2문장
    - key_details: 상품의 핵심 스펙, 소재, 핏 등 객관적인 특징 요약

    [상품 설명]
    {description}

    [출력 형식]
    {{
        "vibe_text": "무드 텍스트",
        "key_details": "핵심 특징"
    }}
    """
    
    try:
        response = model.generate_content(prompt)

        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        print(f"Gemini API 파싱 에러: {e}")
        # API 실패 시 원본 데이터를 적당히 쪼개서 반환하는 Fallback
        return {
            "vibe_text": description[:50] + "...", 
            "key_details": "세부 정보 없음"
        }