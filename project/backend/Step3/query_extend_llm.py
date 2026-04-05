import json
from google import genai
import os
from google.genai import types
from project.backend.app.core.settings import load_backend_env


load_backend_env()
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

async def optimize_query_with_llm(user_query: str):

    prompt = f"""
    너는 이커머스 검색 최적화(SEO) 전문가이자 무신사, 크림,후르츠 패밀리의 상품 데이터베이스 분석가야. 
    유저의 검색어를 입력받으면, 실제 디자이너/스트릿 브랜드들이 '상품명(Title)'에 자주 사용하는 패션 키워드와 영문 혼용 명칭으로 쿼리를 확장해줘.

    [변환 및 확장 규칙]
    1. 이커머스 실전 명칭 사용: 유저가 친숙한 단어(예: 숏패딩)를 쓰면, 브랜드들이 실제 제목에 적는 단어(예: 다운 점퍼, 푸퍼 자켓)로 변환해.
    2. 넓은 그물망(범용 단어) 필수 포함: 힙한 브랜드일수록 상품명이 매우 평범한 경우가 많아. 따라서 후보군을 최대한 넓게 가져오기 위해 카테고리를 뜻하는 
    '가장 일반적인 단어'(예: 자켓, 팬츠, 점퍼)를 무조건 1개 이상 포함시켜.
    3. 구글 연산자 적용: 도출된 단어들을 반드시 괄호 안에서 ' OR ' 연산자로 묶어줘.
    4. 금지 사항: 쓸데없는 말, 설명은 절대 금지. 오직 완성된 쿼리 문자열 하나만 뱉어.

    [예시]
    user_query: 숏패딩
    응답: (다운 점퍼 OR 패딩 자켓 OR 라이트웨이트 자켓 OR 푸퍼 자켓 OR 다운 파카)

    user_query: 워싱 데님
    응답: (워시드 데님 팬츠 OR 빈티지 워시드 데님 OR 가먼트 워시드 데님팬츠 OR 엠보스드 워싱 데님 OR 데님 팬츠)

    user_query: 스트릿 자켓
    응답: (아플리케 후드 집업 OR 파이어버드 트랙탑 OR 크롭 자켓 OR 자켓)

    [Input]
    - 현재 검색어: {user_query}

    [Output Format (반드시 유효한 JSON 형식으로만 응답할 것)]
    {{
        "extended_query": "확장된 검색어 (예: 고프코어 테크웨어 바람막이 자켓)",
    }}
    """

    """
    너는 무신사, 크림, 29CM의 상위권 디자이너 브랜드들이 사용하는 상품명(Title) 패턴을 완벽히 학습한 이커머스 검색 엔진 마스터야.
    유저의 일상적인 검색어를 입력받으면, 실제 브랜드 MD들이 상품명에 기입하는 '실전 키워드'와 '전문 용어'로 번역해서 구글 검색용 쿼리를 만들어야 해.

    [실제 브랜드 상품명 패턴 학습 (Few-Shot Examples)]
    - 패턴 1 (영문 혼용): 청자켓 -> 데님 자켓, 트러커 자켓 / 츄리닝 -> 스웨트 팬츠, 조거 팬츠, 트랙 팬츠
    - 패턴 2 (소재 명시): 나일론 립스탑, 비건 레더, 에코 레더, 피그먼트, 가먼트 다잉, 워시드, 헤어리 알파카
    - 패턴 3 (핏/디테일 명시): 투턱, 핀턱, 투웨이 지퍼, 파라슈트, 카고, 와이드, 릴렉스드, 벌룬 핏, 크롭

    [변환 규칙]
    1. core_items (핵심 상품명): 유저가 찾는 아이템의 범용적인 단어부터 트렌디한 영문 동의어까지 묶어라.
    2. detail_tags (디테일 태그): 유저의 검색어에 포함된 특징(예: 찢어진, 펑퍼짐한)을 판매자 용어(예: 디스트로이드, 데미지드, 와이드 핏)로 변환하라. (검색어에 특징이 없다면 생략 가능)
    3. 구글 연산자 적용: 괄호 안에서 ' OR ' 연산자로 묶고, 그룹 간에는 공백(AND)으로 연결하라.
    
    [학습된 패턴 적용 예시]
    입력: "찢어진 펑퍼짐한 흑청 바지"
    출력: {"final_query": "((데님 팬츠 OR 청바지 OR 데님) (블랙 워시드 OR 흑청 OR 다크 그레이) (디스트로이드 OR 데미지드 OR 컷아웃 OR 찢청) (와이드 핏 OR 릴렉스 핏 OR 벌룬 핏))"}
    
    입력: "바스락 거리는 봄 점퍼"
    출력: {"final_query": "((윈드브레이커 OR 바람막이 OR 나일론 자켓 OR 후드 집업 OR 블루종) (나일론 OR 립스탑 OR 라이트웨이트))"}
    
    반드시 순수 JSON 객체로 반환해:
    {
        "final_query": "((생성된 쿼리 문자열))"
    }
    """

    try:
        response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1 
        )
    )

        extended_query = response.parsed
        return extended_query.model_dump()

    except Exception as e:
        print(f"LLM 최적화 실패: {e}")
        # 실패할 경우를 대비한 기본값(Fallback)
        return {
            "optimized_query": user_query,
        }
