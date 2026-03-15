import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# 1. API 키 가져오기
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    raise ValueError(".env 파일에 GOOGLE_API_KEY가 설정되지 않았습니다.")

# 2. Cloudflare Worker 주소 설정
# 주의: 끝에 /v1 같은 경로를 붙이지 마세요!
my_proxy_url = "https://lucky-bush-20ba.dear-m1njn.workers.dev"

# 3. 클라이언트 생성 (프록시 설정 포함)
client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(
        base_url=my_proxy_url
    )
)

# 4. 테스트 호출 (Vibe Search용 모델 설정)
response = client.models.generate_content(
    model="gemini-2.0-flash-lite", 
    contents="프록시 설정이 완료되었습니다. 응답이 잘 오나요?"
)

print(response.text)