import os
import psycopg2
from dotenv import load_dotenv

# 1. 환경변수에서 Neon DB 접속 주소 불러오기
load_dotenv()
neon_url = os.environ.get("NEON_DB_URL")

if not neon_url:
    raise ValueError("⚠️ .env 파일에 NEON_DB_URL이 설정되지 않았습니다.")

def initialize_database():
    print("🔌 Neon DB에 연결 중입니다...")
    
    try:
        # DB 연결 및 커서(명령어 실행기) 생성
        conn = psycopg2.connect(neon_url)
        cursor = conn.cursor()

        # 1. pgvector 확장 프로그램 설치 (Neon은 기본 지원하므로 활성화만 하면 됨)
        print("📦 pgvector 확장 프로그램 활성화 중...")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        # 2. 메인 테이블 생성 (구글 text-embedding-004 모델에 맞춰 768차원 설정)
        print("🏗️ saved_posts 테이블 생성 중...")
        create_table_query = """
        CREATE TABLE IF NOT EXISTS saved_posts (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(50) NOT NULL,
            source_url TEXT,
            
            category VARCHAR(20),
            summary_text TEXT,
            
            vibe_text TEXT,
            vibe_vector VECTOR(768), 
            
            facts JSONB,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute(create_table_query)

        # 3. JSONB 고속 검색을 위한 GIN 인덱스 생성
        print("⚡ facts 데이터 고속 검색 인덱스(GIN) 생성 중...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_facts_gin ON saved_posts USING GIN (facts);")

        # 모든 작업 확정(Commit)
        conn.commit()
        print("✅ 데이터베이스 초기화가 완벽하게 완료되었습니다!")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        
    finally:
        # 연결 종료 (안 닫아주면 DB 메모리를 갉아먹습니다)
        if conn:
            cursor.close()
            conn.close()
            print("🔒 DB 연결을 안전하게 종료했습니다.")

if __name__ == "__main__":
    initialize_database()