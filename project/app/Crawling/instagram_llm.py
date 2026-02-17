# 수정할 상단 Import 부분
import os
import json
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv

# ---------------------------------------------------------
# 1. 환경변수 및 API 설정
# ---------------------------------------------------------
load_dotenv()
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("⚠️ .env 파일에 GOOGLE_API_KEY가 설정되지 않았습니다.")
genai.configure(api_key=api_key)

# ---------------------------------------------------------
# 3. Gemini 1.5 Flash 분석 엔진 (유저 작성 코드 통합)
# ---------------------------------------------------------
def extract_fact_and_vibe(image_path: str, caption: str, hashtags: list):
    print(f"\n⚡ [Gemini 1.5 Flash] '{image_path}'와 텍스트를 통합 분석 중입니다...")

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

    [JSON 스키마 규격]
    {
      "fact_conditions": {
        "category": "맛집, 카페, 패션, 전시, 꿀팁 중 택 1",
        "location": "가게 이름이나 지역 명칭 (모르면 null)",
        "price_info": "가격대나 가성비 관련 정보 (모르면 null)",
        "key_items": ["주요 메뉴, 아이템, 사물 등 핵심 명사 2~3개"]
      },
      "vibe_text": "사진의 시각적 느낌, OCR로 읽은 의미 있는 글귀, 장소의 무드, 방문하기 좋은 상황(맥락) 등을 모두 자연스럽게 녹여낸 2~3문장의 줄글. (나중에 임베딩 벡터로 변환될 핵심 데이터임)"
    }
    """

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config={"response_mime_type": "application/json", "temperature": 0.3}
    )
    
    response = model.generate_content([prompt, img, text_input])
    return json.loads(response.text)
