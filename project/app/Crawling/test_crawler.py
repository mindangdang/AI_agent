import json
from playwright.sync_api import sync_playwright

# 방금 만든 모듈에서 함수를 불러옵니다!
from instagram_crawler import crawl_instagram_post

def main():
    test_url = "https://www.instagram.com/p/DNSF5jryTof/"
    
    SESSION_ID = "66800932735%3AkVPzTn1cdOCvwk%3A21%3AAYifS7X9eYVuTGD36Dxeoihm_bnJu2Npi8xzz1MIUw"

    with sync_playwright() as p:
        print("🚀 Playwright 브라우저 시작...")
        
        # 스텔스 모드의 핵심 옵션들
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-gpu", 
                "--no-sandbox", 
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled" # 자동화 도구 탐지 방지
            ]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="ko-KR",
            viewport={"width": 1280, "height": 1024}
        )

        # 🍪 정상적인 쿠키 주입 로직
        if SESSION_ID:
            context.add_cookies([{
                "name": "sessionid",
                "value": SESSION_ID,
                "domain": ".instagram.com",
                "path": "/",
                "httpOnly": True,
                "secure": True
            }])
            print("🍪 세션 쿠키가 성공적으로 주입되었습니다.")
        else:
            print("⚠️ 경고: sessionid가 설정되지 않았습니다.")

        page = context.new_page()
        
        # 🌟 말썽 피우는 playwright-stealth 대신, 가장 확실한 네이티브 스텔스 코드 주입!
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print(f"🔍 [{test_url}] 데이터 수집 중...")
        
        # 분리해둔 함수를 여기서 사용합니다.
        result = crawl_instagram_post(page, test_url)

        print("\n✅ 크롤링 결과:")
        print(json.dumps(result, indent=4, ensure_ascii=False))

        if not result["error"]:
            page.screenshot(path="success.png")
            print("📸 성공 화면을 'success.png'로 저장했습니다.")

        browser.close()
        print("\n🛑 브라우저를 안전하게 종료했습니다.")

if __name__ == "__main__":
    main()