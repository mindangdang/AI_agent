import logging
import re
from typing import Dict
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)

# --- 정규식 및 선택자 ---
HASHTAG_PATTERN = re.compile(r"(?<!\w)#([^\s#.,!?;:]+)")
ARTICLE_SELECTOR = "article"
MEDIA_IMAGE_SELECTOR = "article img[decoding='auto'], article img[crossorigin='anonymous']"
VIDEO_SELECTOR = "article video"
NEXT_BUTTON_SELECTOR = "button[aria-label*='Next'], button[aria-label*='다음']"
CAPTION_CANDIDATES = [
    "article h1",
    "article span[dir='auto']",
    "article span._ap3a",
    "div._a9zs span",
]

def crawl_instagram_post(page, post_url: str, max_slides: int = 10) -> Dict[str, object]:
    """
    Playwright의 Page 객체와 URL을 받아 인스타그램 게시물을 크롤링합니다.
    """
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
            page.wait_for_selector(ARTICLE_SELECTOR, timeout=10000)
        except PlaywrightTimeoutError:
            page_text = page.content().lower()
            if "login" in page.url or "로그인" in page_text:
                result["requires_login"] = True
                result["error"] = "로그인이 필요하거나 쿠키가 만료되었습니다."
            else:
                result["blocked"] = True
                result["error"] = "접근이 차단되었습니다. (캡차 또는 챌린지)"
            
            page.screenshot(path="error_screenshot.png")
            return result

        # 본문(Caption) 추출
        for selector in CAPTION_CANDIDATES:
            element = page.locator(selector).first
            if element.is_visible():
                text = element.inner_text().strip()
                if text and not text.startswith("#"):
                    result["caption"] = text
                    result["hashtags"] = HASHTAG_PATTERN.findall(text)
                    break

        # 미디어(이미지/비디오) 추출
        all_images = []
        is_video = False

        for _ in range(max_slides):
            if page.locator(VIDEO_SELECTOR).count() > 0:
                is_video = True
            
            images = page.locator(MEDIA_IMAGE_SELECTOR).evaluate_all(
                "elements => elements.map(e => e.src)"
            )
            valid_images = [src for src in images if "cdninstagram.com" in src or "fbcdn.net" in src]
            all_images.extend(valid_images)

            next_btn = page.locator(NEXT_BUTTON_SELECTOR).first
            if next_btn.is_visible():
                next_btn.click()
                page.wait_for_timeout(800)
            else:
                break

        result["image_urls"] = list(dict.fromkeys(all_images))

        if is_video:
            result["post_type"] = "video"
        elif len(result["image_urls"]) > 1:
            result["post_type"] = "carousel"

    except Exception as e:
        logger.exception(f"크롤링 중 예외 발생: {e}")
        result["error"] = str(e)
        page.screenshot(path="exception_screenshot.png")

    return result