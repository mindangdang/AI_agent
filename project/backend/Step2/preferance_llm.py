import os
import asyncio
import httpx
import psycopg 
from psycopg.rows import dict_row 
from pydantic import BaseModel, Field 
from google import genai
from google.genai import types
from pathlib import Path

from project.backend.app.core.settings import IMAGE_DIR, load_backend_env

# ==========================================
# 1. 환경 변수 및 설정
# ==========================================
load_backend_env()
NEON_DB_URL = os.environ.get("NEON_DB_URL")
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    raise ValueError(".env 파일에 GOOGLE_API_KEY가 설정되지 않았습니다.")

my_proxy_url = "https://lucky-bush-20ba.dear-m1njn.workers.dev" 
client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(base_url=my_proxy_url)
)

LOCAL_IMAGE_DIR = Path(IMAGE_DIR)

# ==========================================
# 2. Pydantic 스키마 
# ==========================================
class TasteProfileResult(BaseModel):
    persona: str = Field(description="유저의 취향과 페르소나를 한 문장으로 정의하는 타이틀")
    unconscious_taste: str = Field(description="유저의 무의식적인 취향을 날카롭게 분석하는 텍스트 (2~3문장)")
    recommendation: str = Field(description="유저의 취향에 정합하는 새로운 키워드 제시 및 실존하는 장소/물건 추천")

# ==========================================
# 3. 시스템 프롬프트 (토큰 다이어트 적용)
# ==========================================
SYSTEM_PROMPT = """
[System Persona]
주어진 데이터는 유저의 평소 취향(current_profile)과 최근 저장한 컨텐츠들이다. 표면적으로 보이지 않는 취향 패턴을 파악하여 페르소나를 업데이트하는 휴먼-데이터 분석가로서 행동하라.

[Core Analysis Rules]
- 1차원적 요약 절대 금지 ("카페를 좋아하고 옷에 관심이 많다" 등)
- 형태학적/시각적 분석: 조형 요소, Dominant Palette의 색채 심리, 질감(Texture) 분석
- 기호학적 분석: [외연: 객관적 기능], [내포: 상징 가치], [신화: 도달하려는 이상적 삶] 관점
- 심리적 동기: 자기 대상화(Self-Objectification), 수단적 vs 표현적 취향 구분

[Thinking Process]
- Taste Patterns: 시각적/감각적 공통점 추출
- Identity Interpretation: 공간과 사물들이 공유하는 ‘분위기’와 이면의 페르소나 추론

[Tone & Manner]
- 두괄식 문장 사용, 철학적/추상적 표현 배제
- '앤틱한', '키치한', '날카로운' 등 분위기를 나타내는 감각적 단어 사용
- 제공된 원본 데이터(장소명, 상품명 등)를 직접적으로 나열하지 말 것
"""

# ==========================================
# 4. 데이터 로드 및 포맷팅 (비동기화 및 통합)
# ==========================================
async def fetch_user_data_from_neon(user_id: int):
    try:
        async with await psycopg.AsyncConnection.connect(NEON_DB_URL) as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                query = """
                    SELECT facts, recommend, category, title, summary_text, image_url
                    FROM saved_posts
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT 10;
                """
                await cur.execute(query, (str(user_id),))
                return await cur.fetchall()
    except Exception as e:
        print(f"DB 조회 실패: {e}")
        return []

async def get_image_bytes(url_or_filename: str) -> bytes | None:
    if not url_or_filename:
        return None

    # Case 1: 외부 URL (다운로드 실패해서 원본 URL만 남은 경우 등)
    if url_or_filename.startswith(('http://', 'https://')):
        try:
            async with httpx.AsyncClient(http2=True) as client:
                resp = await client.get(url_or_filename, timeout=5.0)
                if resp.status_code == 200:
                    return resp.content
        except Exception as e:
            print(f"외부 이미지 로드 실패 ({url_or_filename}): {e}")
        return None
    
    # Case 2: 로컬 파일 (디스크 I/O를 논블로킹으로 처리)
    def read_local():
        try:
            candidate = Path(url_or_filename)
            if not candidate.is_absolute():
                candidate = LOCAL_IMAGE_DIR / candidate.name
            if candidate.exists() and candidate.is_file():
                return candidate.read_bytes()
        except Exception as e:
            print(f"로컬 이미지 로드 실패 ({url_or_filename}): {e}")
        return None

    return await asyncio.to_thread(read_local)

def format_data_for_prompt(item: dict) -> str:
    facts = item.get("facts") or {}
    title = facts.get("title", "알 수 없음")
    location = facts.get("location_text", "위치 정보 없음")
    key_details = facts.get("key_details", [])

    return f"""[Item {title}]
    - Category: {item.get('category', 'UNKNOWN')}
    - Location: {location}
    - Summary: {item.get('summary_text', '')}
    - Recommend: {item.get('recommend', '')}
    - Key Details: {key_details} """

# ==========================================
# 5. LLM 분석 실행 함수
# ==========================================
async def analyze_vibe(user_id: int, current_profile: dict):
    raw_items = await fetch_user_data_from_neon(user_id)
    if not raw_items:
        return None

    print(f"[User {user_id}] 이미지 데이터 병렬 로딩 중...")
    image_tasks = [get_image_bytes(item.get("image_url")) for item in raw_items]
    image_results = await asyncio.gather(*image_tasks)

    contents = []
    context = f"""
    [Current User Profile]
    - Persona: {current_profile.get('persona', '분석 전')}
    - Previous Analysis: {current_profile.get('unconscious_taste', '데이터 없음')}
    
    [New Activity]
    최근 유저가 다음 아이템들을 새롭게 저장했다. 기존 프로필과 새로운 데이터를 비교하여 취향의 '확장', '변화', 또는 '심화'를 발견하고 업데이트된 프로필을 생성하라.
    """
    contents.append(types.Part.from_text(text=context))
    
    for item, img_bytes in zip(raw_items, image_results):
        info = format_data_for_prompt(item)
        contents.append(types.Part.from_text(text=info))
        if img_bytes:
            contents.append(types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"))

    try:
        print(f"[User {user_id}] 취향 프로필 분석 중 (Gemini 2.5 Flash)...")
        response = await client.aio.models.generate_content(
            model='gemini-2.5-flash', 
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.4, 
                response_mime_type="application/json",
                response_schema=TasteProfileResult # 
            ),
        )

        return response.parsed.model_dump()
        
    except Exception as e:
        print(f"LLM 프로필 생성 중 오류 발생: {e}") 
        return None