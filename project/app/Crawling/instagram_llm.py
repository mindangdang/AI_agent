# 수정할 상단 Import 부분
import os
import json
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv
import requests
from io import BytesIO
from pydantic import BaseModel, Field
from typing import List, Optional

# ---------------------------------------------------------
# 1. 환경변수 및 API 설정
# ---------------------------------------------------------

load_dotenv()
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("⚠️ .env 파일에 GOOGLE_API_KEY가 설정되지 않았습니다.")
genai.configure(api_key=api_key)

# ---------------------------------------------------------
# 2.schema에 대한 Pydantic
# ---------------------------------------------------------

class Facts(BaseModel):
    title: Optional[str] = Field(description="상품명, 브랜드명, 작품명, 상호명 또는 주제, 제목")
    price_info: Optional[str] = Field(description="상품가격, 메뉴 가격대 등 비용 관련 텍스트")
    location_text: Optional[str] = Field(description="위치, 주소 텍스트")
    time_info: Optional[str] = Field(description="시간/기간 텍스트")
    key_details: Optional[List[str]] = Field(description="핵심 특징 1, 2, 3")

class ExtractedItem(BaseModel):
    category: str = Field(description="PLACE, PRODUCT, CONTENT, EVENT, TIP, INSPIRATION 중 택 1")
    summary_text: str = Field(description="이 게시물이 무엇을 말하는지 객관적이고 간략한 내용 요약 (앱 화면 노출용)")
    vibe_text: str = Field(description="감성, 분위기, 사용 맥락 요약. '느좋', '힙한' 등 추상적 키워드를 문장에 자연스럽게 포함할 것 (유사도 검색용)")
    facts: Facts

class InstaAnalysisResult(BaseModel):
    extracted_items: List[ExtractedItem]

# ---------------------------------------------------------
# 3. Gemini 2.5 Flash 분석 엔진 
# ---------------------------------------------------------

def extract_fact_and_vibe(image_path: str, caption: str, hashtags: list):
    print(f"\n⚡ [Gemini 2.5 Flash] '{image_path}'와 텍스트를 통합 분석 중입니다...")

    # 안전하게 다운로드된 로컬 이미지 열기
    img = Image.open(image_path)

    # 해시태그 통합
    tags_str = " ".join(hashtags) if hashtags else ""
    text_input = f"캡션: {caption}\n해시태그: {tags_str}"

    prompt = """
    너는 인스타그램 게시물을 분석하는 최고 수준의 데이터 추출 AI야.
    사용자가 제공한 '이미지'와 '캡션+해시태그'를 종합적으로 분석해줘.

    [작업 지시]
    1. 사진 속에 있는 글자(OCR: 브랜드 로고, 간판, 자막 등)를 빠짐없이 읽고, 조명, 인테리어, 색감 등 시각적인 분위기(Visual Vibe)를 파악해.
    2. 캡션과 해시태그의 맥락을 결합해.
    3. 아래의 JSON 스키마에 맞춰 '객관적 사실(fact_conditions)'과 '주관적 감성(vibe_text)'으로 완벽하게 분리해.
    """

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": InstaAnalysisResult, 
            "temperature": 0.2 
        }
    )
    
    response = model.generate_content([prompt, img, text_input])
    return json.loads(response.text)
