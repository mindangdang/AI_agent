import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# 1. API 설정
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# =====================================================================
# [Step 1] 에이전트 주입용 Pydantic 스키마 (Structured Output)
# =====================================================================
class RewardMechanism(BaseModel):
    core_concept: str = Field(description="미학적 공통 구조를 관통하는 핵심 개념 (예: '통제된 자유', '구조적 긴장')")
    cognitive_reward: str = Field(description="유저의 뇌가 이 시각적 구조에서 왜 심리적 보상(통제감, 안정감 등)을 얻는지 분석한 3문장 가설")
    hidden_question: str = Field(description="이 취향이 유저의 삶에 던지고 있는 철학적 질문 1문장")

class QueryExpansionKeys(BaseModel):
    market_keywords: list[str] = Field(description="[가장 중요] 철학적 개념을 구글/인스타에서 실제로 쓰이는 대중적 단어로 번역한 검색용 키워드 5개 (예: '무채색 인테리어', '고프코어')")
    anti_keywords: list[str] = Field(description="에이전트가 검색에서 반드시 제외해야 할 회피 키워드 3개 (예: '네온', '맥시멀리즘')")
    exploration_keywords: list[str] = Field(description="필터 버블을 깨기 위해, 현재 취향과 인접하지만 약간의 변주를 주는 탐색용 키워드 2개")

class AestheticRewardProfile(BaseModel):
    reward_analysis: RewardMechanism
    search_weapons: QueryExpansionKeys

# =====================================================================
# [Step 2] 시스템 프롬프트: 미학적 보상 함수 추론기
# =====================================================================
REWARD_ENGINE_PROMPT = """
너는 Vibe Search의 '미학적 인지-정서 보상 역추론 엔진'이야.
사용자가 수집한 파편적 데이터들을 분석해, 이 사람의 뇌가 어떤 시각적 질서에서 편안함이나 각성을 느끼는지(보상 함수)를 추적하는 것이 너의 유일한 목표다.

[분석 알고리즘]
1. 보상 메커니즘 추론 (The "Why"):
- "미니멀을 좋아한다" 같은 1차원적 분석은 쓰레기통에 버려라.
- 정보 밀도, 대칭성, 대비 강도를 분석하고, 왜 여기서 보상을 얻는지(예: 감각 과부하 회피, 예측 가능성을 통한 통제감 획득 등)를 역추적해라.

2. 시장 언어로의 강제 번역 (Query Translation):
- 철학적 분석에만 머물면 검색 엔진은 죽는다. 
- 너의 그 깊이 있는 철학적 분석 결과를, 한국의 블로거와 쇼핑몰들이 실제로 사용하는 '대중적이고 상업적인 검색어(Market Keywords)'로 완벽하게 번역해내라.

[출력 규칙]
반드시 지정된 JSON 스키마를 엄격히 준수하며, 단정적이지 않은 '확률적 가설'의 톤을 유지해라.
"""

# =====================================================================
# [Step 3] DB 페칭 및 실시간 LLM 추론 로직
# =====================================================================
def fetch_recent_vibe_data(user_id: str, limit: int = 50) -> list[dict]:
    """Neon DB에서 유저의 최근 저장 데이터를 빠르게 긁어옵니다."""
    neon_conn_str = os.environ.get("NEON_DB_URL")
    
    if not neon_conn_str:
        print("⚠️ DB 연결 정보 없음. 시뮬레이션용 더미 데이터를 반환합니다.")
        return [
            {"category": "fashion", "item": "오버사이즈 블랙 수트", "vibe": "루즈하지만 핏이 잡힌, 무채색, 절제된 무드"},
            {"category": "space", "item": "빛이 차단된 다크룸 카페", "vibe": "노출 콘크리트, 무거운, 프레임이 강조된 공간"},
            {"category": "object", "item": "수조 속 상어 사진", "vibe": "통제된 카오스, 유리벽 안의 위협, 서늘함"}
        ]

    try:
        with psycopg2.connect(neon_conn_str) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT category, item_name, vibe_text 
                    FROM user_saved_items 
                    WHERE user_id = %s 
                    ORDER BY created_at DESC 
                    LIMIT %s
                """
                cur.execute(query, (user_id, limit))
                return cur.fetchall()
    except Exception as e:
        print(f"❌ Neon DB 조회 에러: {e}")
        return []

def calculate_aesthetic_reward(user_id: str) -> AestheticRewardProfile:
    print(f"\n🔍 [엔진 가동] 유저({user_id})의 Neon DB 데이터를 스캔합니다...")
    raw_data = fetch_recent_vibe_data(user_id)
    
    if not raw_data:
        raise ValueError("분석할 데이터가 부족합니다.")

    print(f"🧠 [LLM 추론] {len(raw_data)}개의 데이터에서 보상 함수를 역추적 중입니다... (gemini-2.5-flash)")
    
    # 데이터를 LLM이 읽기 좋게 문자열 화
    context_str = json.dumps(raw_data, ensure_ascii=False, indent=2)
    prompt = f"다음은 유저의 최근 수집 데이터야. 이 유저의 인지적 보상 함수를 추론하고 검색 키워드로 변환해줘:\n\n{context_str}"

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=REWARD_ENGINE_PROMPT,
            response_mime_type="application/json",
            response_schema=AestheticRewardProfile, 
            temperature=0.3 # 논리적 추론과 창의적 번역의 균형점
        )
    )
    
    return AestheticRewardProfile.model_validate_json(response.text)

# =====================================================================
# [실행 및 결과 검증]
# =====================================================================
if __name__ == "__main__":
    try:
        profile = calculate_aesthetic_reward("user_999")
        
        print("\n" + "="*60)
        print(f"🎯 [핵심 개념]: {profile.reward_analysis.core_concept}")
        print(f"🧠 [인지적 보상 메커니즘]:\n{profile.reward_analysis.cognitive_reward}")
        print(f"❓ [삶의 질문]: {profile.reward_analysis.hidden_question}")
        print("-" * 60)
        print("🛠️ [검색 에이전트 주입용 무기]")
        print(f" 🟢 Market Keywords : {profile.search_weapons.market_keywords}")
        print(f" 🔴 Anti Keywords   : {profile.search_weapons.anti_keywords}")
        print(f" 🔵 Explore Keywords: {profile.search_weapons.exploration_keywords}")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"오류: {e}")