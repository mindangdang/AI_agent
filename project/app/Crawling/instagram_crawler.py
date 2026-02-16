import logging
import re
from typing import Dict
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

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
        page.goto(post_url, wait_until="domcontentloaded")
        
        try:
            # 로딩 대기: article이나 main 태그가 화면에 나타날 때까지 기다림
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

        # 🎯 핵심 수정 포인트: 탐색 구역을 엄격하게 제한!
        # 1순위: article 태그가 있으면 무조건 그것만 게시물 박스로 잡음
        if page.locator("article").count() > 0:
            post_container = page.locator("article").first
        # 2순위: article이 진짜 없다면, main 아래의 첫 번째 구역만 잡음 (추천 게시물 방어)
        else:
            post_container = page.locator("main > div").first

        # 1. 본문(Caption) 추출
        for selector in CAPTION_CANDIDATES:
            elements = post_container.locator(selector).all()
            for element in elements:
                if element.is_visible():
                    text = element.inner_text().strip()
                    # 본문 검증 (15자 이상)
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
            page.wait_for_timeout(500)
            
            if post_container.locator(VIDEO_SELECTOR).count() > 0:
                is_video = True
            
            # 좁혀진 게시물 박스 안에서만 이미지를 찾음
            images = post_container.locator("img").evaluate_all(
                "elements => elements.map(e => e.src)"
            )
            
            for src in images:
                if not src: continue
                is_cdn = "cdninstagram.com" in src or "fbcdn.net" in src
                # 프로필 사진 필터링
                is_profile = "150x150" in src or "profile_pic" in src
                
                if is_cdn and not is_profile:
                    all_images.append(src)

            # 다음 버튼 클릭 (마찬가지로 게시물 박스 안에서만 찾음)
            next_btn = post_container.locator(NEXT_BUTTON_SELECTOR).first
            if next_btn.is_visible():
                next_btn.click()
                page.wait_for_timeout(1000)
            else:
                break

        # 중복 제거 후 순서 유지
        result["image_urls"] = list(dict.fromkeys(all_images))

        if is_video:
            result["post_type"] = "video"
        elif len(result["image_urls"]) > 1:
            result["post_type"] = "carousel"

    except Exception as e:
        logger.exception(f"크롤링 중 예외 발생: {e}")
        result["error"] = str(e)

    return result