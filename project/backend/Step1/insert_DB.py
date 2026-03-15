import os
import json
import psycopg2
from pgvector.psycopg2 import register_vector  
from google import genai
from dotenv import load_dotenv
from google.genai import types

# 환경변수 세팅 (중복 호출 정리)
load_dotenv()
neon_url = os.environ.get("NEON_DB_URL") 
api_key = os.environ.get("GOOGLE_API_KEY")

if not api_key:
    raise ValueError(".env 파일에 GOOGLE_API_KEY가 설정되지 않았습니다.")

# 구글 API 클라이언트 초기화
my_proxy_url = "https://lucky-bush-20ba.dear-m1njn.workers.dev" 
client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(
        base_url=my_proxy_url
    )
)

# 2026년 최신 임베딩 모델명 적용
MODEL_NAME = "gemini-embedding-2-preview" 

# ==========================================
# 1. Vibe 텍스트 -> 벡터 변환 함수
# ==========================================
def get_vibe_vector(text: str):
    if not text or text.strip() == "":
        return None

    try:
        response = client.models.embed_content(
            model=MODEL_NAME,
            contents=text, 
            config=types.EmbedContentConfig(
                output_dimensionality=768  
            )
        )
        # response 구조에 맞게 수정
        return response.embeddings[0].values
    except Exception as e:
        print(f" 임베딩 생성 실패: {e}")
        return None

# ==========================================
# 2. JSON 데이터 DB Insert 함수
# ==========================================
def insert_items_to_db(user_id: str, source_url: str, extracted_items: list):
    conn = None
    cursor = None 
    
    try:
        conn = psycopg2.connect(neon_url)
        register_vector(conn)  
        cursor = conn.cursor()

        # [수정 1] INSERT 컬럼에 'title' 추가
        # [수정 2] ON CONFLICT 기준을 (source_url, title)로 변경
        insert_query = """
            INSERT INTO saved_posts 
            (user_id, source_url, title, category, summary_text, vibe_text, vibe_vector, facts)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (source_url, title) DO NOTHING; 
        """

        for item in extracted_items:
            # Pydantic 객체일 경우 .get() 대신 속성 접근이 필요할 수 있으나 
            # 일반 dict일 경우를 가정하여 안전하게 처리합니다.
            category = item.get("category")
            summary_text = item.get("summary_text")
            vibe_text = item.get("vibe_text", "")
            
            # [수정 3] facts 내부의 title 추출 (중복 체크의 핵심)
            facts_data = item.get("facts", {})
            title = facts_data.get("title", "Unknown Item")
            
            facts_json = json.dumps(facts_data, ensure_ascii=False)
            
            # 벡터 변환
            vibe_vector = get_vibe_vector(vibe_text)

            # [수정 4] 파라미터 개수 맞춤 (title 포함 8개)
            cursor.execute(insert_query, (
                user_id, 
                source_url, 
                title,          # 추가됨
                category, 
                summary_text, 
                vibe_text, 
                vibe_vector, 
                facts_json
            ))

        conn.commit()
        print(f"DB 저장 완료: {len(extracted_items)}개의 아이템 처리됨")
        
    except Exception as e:
        print(f" DB 저장 중 에러 발생: {e}")
        if conn:
            conn.rollback() 
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()