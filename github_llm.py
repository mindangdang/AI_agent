import os
from openai import OpenAI

token = os.environ.get("GITHUB_TOKEN") 

client = OpenAI(
    base_url="https://models.inference.ai.azure.com", # GitHub Models 엔드포인트
    api_key=token,
)

response = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Vibe Search 프로젝트 테스트 중입니다. 모델 응답 확인!",
        }
    ],
    model="gpt-4o", # 쓰고 싶은 모델명 (gpt-4o, Llama-3.3-70b-Instruct 등)
    temperature=1,
    max_tokens=2048,
    top_p=1
)

print(response.choices[0].message.content)