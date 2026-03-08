import logging
import re
from typing import Dict
import requests
import json
import os
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

# --- 정규식 및 선택자 ---
HASHTAG_PATTERN = re.compile(r"(?<!\w)#([^\s#.,!?;:]+)")
VIDEO_SELECTOR = "video"
NEXT_BUTTON_SELECTOR = "button[aria-label*='Next'], button[aria-label*='다음'], div[role='button'] svg[aria-label='다음']"
CAPTION_CANDIDATES = [
    "h1",
    "div._a9zs", 
    "span[dir='auto']",
    "span._ap3a",
]

def crawl_instagram_post(page, post_url: str, max_slides: int = 10) -> Dict[str, object]:
    result = {
        "post_url": post_url,
        "caption": "",
        "hashtags": [],
        "image_urls": [],
        "post_type": "image",
        "error": None,
        "blocked": False,
        "requires_login": False,
    }

    try:
        # 페이지 이동 및 로드 대기
        page.goto(post_url, wait_until="domcontentloaded")
        
        try:
            # article이나 main 태그가 뜰 때까지 대기
            page.wait_for_selector("article, main", timeout=15000)
        except PlaywrightTimeoutError:
            page_text = page.content().lower()
            if "login" in page.url or "로그인" in page_text:
                result["requires_login"] = True
                result["error"] = "로그인이 필요하거나 쿠키가 만료되었습니다."
            else:
                result["blocked"] = True
                result["error"] = "접근이 차단되었거나 페이지 구조가 변경되었습니다."
            return result

        # 컨테이너 설정: 화면 전체 탐색을 방지하기 위해 최소한의 기준점(main 또는 article)을 잡습니다.
        if page.locator("article").count() > 0:
            post_container = page.locator("article").first
        else:
            post_container = page.locator("main").first

        # 1. 본문(Caption) 및 해시태그 추출
        for selector in CAPTION_CANDIDATES:
            elements = post_container.locator(selector).all()
            for element in elements:
                if element.is_visible():
                    text = element.inner_text().strip()
                    # 아이디가 아닌 '진짜 본문(15자 이상)'인지 검증
                    if text and not text.startswith("#") and len(text) > 15:
                        result["caption"] = text
                        result["hashtags"] = HASHTAG_PATTERN.findall(text)
                        break
            if result["caption"]:
                break

        # 2. 미디어(이미지/비디오) 추출
        all_images = []
        is_video = False

        for _ in range(max_slides):
            # 화면이 로드되고 슬라이드가 넘어갈 시간을 잠깐 줌
            page.wait_for_timeout(500)
            
            # 비디오 여부 체크
            if post_container.locator(VIDEO_SELECTOR).count() > 0:
                is_video = True
            
            # 🎯 [핵심] 궁극의 DOM 구조 & 크기 필터링!
            images = post_container.locator("img").evaluate_all(
                """elements => elements
                    .filter(e => e.closest('a') === null)
                    .filter(e => e.clientWidth > 250)
                    .map(e => e.src)
                """
            )
            
            for src in images:
                if not src: continue
                # 인스타그램 실제 사진 서버(CDN) 도메인인지 최종 확인
                if "cdninstagram.com" in src or "fbcdn.net" in src:
                    all_images.append(src)

            # 다음 슬라이드 버튼 찾기 및 클릭
            next_btn = post_container.locator(NEXT_BUTTON_SELECTOR).first
            if next_btn.is_visible():
                next_btn.click()
                page.wait_for_timeout(1000) # 슬라이드 애니메이션 대기
            else:
                break

        # 중복된 이미지 URL 제거 (순서는 그대로 유지)
        result["image_urls"] = list(dict.fromkeys(all_images))

        # 게시물 타입(Carousel, Video, Image) 판별
        if is_video:
            result["post_type"] = "video"
        elif len(result["image_urls"]) > 1:
            result["post_type"] = "carousel"

    except Exception as e:
        logger.exception(f"크롤링 중 예외 발생: {e}")
        result["error"] = str(e)

    return result

def download_images(image_urls: list, save_dir: str = "insta_vibes"):
    if not image_urls:
        print("⚠️ 다운로드할 이미지가 없습니다.")
        return []

    # 폴더가 없으면 생성
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        print(f"📁 [{save_dir}] 폴더를 새로 생성했습니다.")

    downloaded_paths = []
    print(f"\n⬇️ 총 {len(image_urls)}장의 이미지 다운로드를 시작합니다...")

    for index, url in enumerate(image_urls):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status() 

            file_name = f"image_{index + 1:02d}.jpg"
            file_path = os.path.join(save_dir, file_name)

            with open(file_path, "wb") as f:
                f.write(response.content)
            
            downloaded_paths.append(file_path) 
            print(f"  ✅ {file_name} 저장 완료")

        except Exception as e:
            print(f"  ❌ {index + 1}번째 이미지 다운로드 실패: {e}")

    print("🎉 모든 이미지 다운로드가 완료되었습니다!\n")
    return downloaded_paths

def main(post_url: str):
    STATE_FILE = "instagram_state.json"

    with sync_playwright() as p:
        # 최초 로그인 및 크롤링 과정을 확인하기 위해 headless=False 설정
        # 나중에 완전히 자동화하려면 True로 변경하셔도 됩니다.
        browser = p.chromium.launch(headless=False)
        
        # 1. 로그인 상태 확인 및 적용
        if os.path.exists(STATE_FILE):
            print("저장된 로그인 상태(instagram_state.json)를 불러옵니다...")
            context = browser.new_context(storage_state=STATE_FILE)
            page = context.new_page()
        else:
            print("저장된 로그인 상태가 없습니다. 브라우저가 열리면 인스타그램 로그인을 진행해주세요.")
            context = browser.new_context()
            page = context.new_page()
            
            page.goto("https://www.instagram.com/accounts/login/")
            # 사용자가 콘솔에서 엔터를 칠 때까지 대기
            input("👉 브라우저에서 로그인을 완전히 마친 후, 이 콘솔 창에서 [Enter] 키를 눌러주세요...") 
            
            # 로그인 완료 후 상태 저장
            context.storage_state(path=STATE_FILE)
            print(f"✅ 로그인 상태가 '{STATE_FILE}'에 저장되었습니다. 다음부터는 자동 로그인됩니다.")

        # 2. 크롤링 및 다운로드 실행
        print(f"\n[{post_url}] 크롤링을 시작합니다...")
        result = crawl_instagram_post(page, post_url)
        
        if result.get("error"):
            print(f"❌ 크롤링 에러 발생: {result['error']}")
        else:
            print("✅ 크롤링 성공!")
            print(f"📝 본문: {result['caption'][:30]}..." if result['caption'] else "📝 본문: 없음")
            print(f"🏷️ 해시태그: {result['hashtags']}")
            
            # 이미지 다운로드 수행
            if result["image_urls"]:
                download_images(result["image_urls"])
            else:
                print("⚠️ 수집된 이미지가 없습니다.")

        browser.close()

if __name__ == "__main__":
    # 테스트할 인스타그램 게시물 URL을 입력하세요.
    TARGET_POST_URL = "https://www.instagram.com/p/여기에_게시물_ID/"
    main(TARGET_POST_URL)