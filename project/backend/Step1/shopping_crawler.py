import os
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from google import genai
from google.genai import types
import re
import httpx
from playwright.async_api import async_playwright



# ---  Gemini 폴백 함수 ---
def fallback_with_gemini(url: str):
    try:
        client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
        
        prompt = f"""Extract accurate product information from this URL: ${url}. 
      
      CRITICAL INSTRUCTIONS:
      1. IMAGE URL: You MUST find the ACTUAL, ORIGINAL image URL of the product from the page's source code or metadata. Look specifically for 'og:image', 'twitter:image', or the primary <img> tag associated with the product. 
      2. NO PLACEHOLDERS: Do NOT use placeholder services (like picsum.photos) or generate a fake image URL. 
      3. ABSOLUTE URLS: If the image URL found is relative (e.g., starts with /), you MUST convert it to an absolute URL using the base domain of ${url}.
      4. ACCURACY: Ensure the product name, price, and brand match exactly what is shown on the page."""

        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "title": {"type": "STRING"},
                        "price": {"type": "STRING"},
                        "currency": {"type": "STRING"},
                        "image_url": {"type": "STRING"},
                        "brand": {"type": "STRING"},
                        "description": {"type": "STRING"},
                    },
                    "required": ["title", "price", "image_url"]
                }
            )
        )
        data = json.loads(response.text)

        llm_image_url = data.get("image_url", "")
        real_image_url = llm_image_url # 혹시 실패하면 LLM이 찾은 걸 쓰도록 기본값 세팅
        
        try:
            print(f"[{url}] 원본 웹페이지에서 이미지 직접 추출 중...")
            # httpx로 해당 URL의 웹페이지 HTML을 가져옵니다.
            # 웹사이트들이 봇을 차단하지 않도록 브라우저인 척(User-Agent) 합니다.
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response_html = httpx.get(url, headers=headers, timeout=10.0, follow_redirects=True)
            soup = BeautifulSoup(response_html.text, 'html.parser')
            
            # 1순위: 메타 데이터의 og:image (쇼핑몰들이 공유용으로 지정해둔 가장 고화질/정확한 사진)
            og_img = soup.find("meta", property="og:image")
            if og_img and og_img.get("content"):
                real_image_url = og_img["content"]
                print("원본 웹페이지 og:image 추출 성공!")
            else:
                # 2순위: twitter:image
                tw_img = soup.find("meta", attrs={"name": "twitter:image"})
                if tw_img and tw_img.get("content"):
                    real_image_url = tw_img["content"]
                    print("원본 웹페이지 twitter:image 추출 성공!")
                    
            # URL이 '/images/...' 처럼 상대 경로로 되어 있다면 절대 경로로 변환
            if real_image_url.startswith("/"):
                real_image_url = urljoin(url, real_image_url)
                
        except Exception as img_e:
            print(f"웹페이지 이미지 직접 추출 실패 (LLM 추출값 유지): {img_e}")
        
        return {
            "url": url,
            "title": data.get("title", ""),
            "brand": data.get("brand", ""),
            "price": data.get("price", ""),
            "currency": data.get("currency", ""),
            "image_url": real_image_url,
            "description": data.get("description", ""),
            "source": "gemini-url-context-backend" 
        }
    except Exception as e:
        print(f"Gemini 폴백 추출 실패: {e}")
        return None
# -----------------------------------


def _clean_text(value: str | None) -> str:
    """문자열의 앞뒤 공백을 제거하고 연속된 공백을 하나로 줄입니다."""
    if not value:
        return ""
    return re.sub(r'\s+', ' ', str(value)).strip()

def _extract_json_ld_products(html: str) -> list[dict]:
    """HTML에서 JSON-LD 형식의 상품(Product) 정보를 추출합니다."""
    soup = BeautifulSoup(html, 'html.parser')
    products = []
    
    scripts = soup.find_all('script', type='application/ld+json')
    for script in scripts:
        try:
            raw = script.string
            if not raw:
                continue
                
            raw = raw.strip()
            payload = json.loads(raw)
            candidates = payload if isinstance(payload, list) else [payload]
            
            for candidate in candidates:
                if not isinstance(candidate, dict):
                    continue
                    
                if candidate.get("@type") == "Product":
                    products.append(candidate)
                elif candidate.get("@graph") and isinstance(candidate["@graph"], list):
                    for item in candidate["@graph"]:
                        if isinstance(item, dict) and item.get("@type") == "Product":
                            products.append(item)
        except (json.JSONDecodeError, TypeError, AttributeError):
            # 파싱 에러 무시
            continue
            
    return products

def _extract_meta_content(html: str, property_name: str) -> str:
    """메타 태그에서 특정 속성값의 콘텐츠를 추출합니다."""
    soup = BeautifulSoup(html, 'html.parser')
    content = ""
    
    # Try property attribute
    meta = soup.find('meta', attrs={'property': property_name})
    if meta and meta.get('content'):
        content = meta['content']
        
    if not content:
        # Try name attribute
        meta = soup.find('meta', attrs={'name': property_name})
        if meta and meta.get('content'):
            content = meta['content']
            
    if not content:
        # Try itemprop attribute
        meta = soup.find('meta', attrs={'itemprop': property_name})
        if meta and meta.get('content'):
            content = meta['content']
            
    return _clean_text(content)

async def _load_product_page(url: str) -> dict:
    """상품 페이지의 HTML을 로드하며 필요시 Playwright로 폴백합니다."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            html = response.text
            final_url = str(response.url)

            # Playwright가 필요한지 확인 (자바스크립트 렌더링 필수 사이트거나 메타/json-ld 태그 누락 시)
            is_js_heavy = any(domain in url for domain in ["musinsa.com", "kream.co.kr", "zara.com"])
            if is_js_heavy or "<script" not in html or ("og:title" not in html and "application/ld+json" not in html):
                raise ValueError("Need JS rendering")

            return {"html": html, "finalUrl": final_url}
            
    except Exception:
        # Fallback to Playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
            context = await browser.new_context(user_agent=headers["User-Agent"])
            page = await context.new_page()
            
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000) # 이미지 로딩을 위해 잠시 대기
            
            html = await page.content()
            final_url = page.url
            await browser.close()
            
            return {"html": html, "finalUrl": final_url}

async def scrape_product_metadata(url: str) -> dict:
    print(f"[{url}] 메타데이터 추출 시작...")
    
    # 변수 사전 초기화 (에러가 나도 안전하게 리턴하기 위해)
    final_url = url
    title = ""
    brand = ""
    price = ""
    currency = ""
    availability = ""
    description = ""
    normalized_image_url = ""

    try:
        # 속도 개선: Playwright(30초) 대신 httpx(빠름) 사용
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        
        # httpx 비동기 클라이언트로 5초 안에 안 주면 바로 포기하고 Gemini로 넘어가도록 세팅
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=5.0, follow_redirects=True)
            html = response.text
            final_url = str(response.url)
        
        soup = BeautifulSoup(html, 'html.parser')
        
        products = _extract_json_ld_products(html)
        product = products[0] if products else {}

        offers = product.get("offers", {})
        if isinstance(offers, list):
            offers = offers[0] if offers else {}

        images = product.get("image", [])
        if isinstance(images, str):
            images = [images]

        if isinstance(offers, dict) and offers:
            price = _clean_text(str(offers.get("price") or ""))
            currency = _clean_text(str(offers.get("priceCurrency") or ""))
            avail_raw = _clean_text(str(offers.get("availability") or ""))
            availability = avail_raw.split("/")[-1] if avail_raw else ""

        # Title 추출
        title_text = ""
        title_tag = soup.find("title")
        if title_tag:
            title_text = title_tag.get_text(strip=True)
            
        title = (_clean_text(product.get("name") or "") or 
                _extract_meta_content(html, "og:title") or 
                title_text)
        
        # Enhanced image 추출
        image_url = (_clean_text(images[0] if images else "") or 
                    _extract_meta_content(html, "og:image") or 
                    _extract_meta_content(html, "twitter:image") or
                    _extract_meta_content(html, "image"))

        # 일반적인 상품 이미지 CSS 선택자로 시도
        if not image_url:
            common_selectors = [
                "img[id*='product']", "img[class*='product']", 
                "img[id*='main']", "img[class*='main']",
                "img[id*='goods']", "img[class*='goods']",
                ".product-image img", "#product-image img"
            ]
            for selector in common_selectors:
                img_tag = soup.select_one(selector)
                if img_tag and img_tag.get("src"):
                    image_url = img_tag["src"]
                    break

        # Description 및 Brand 추출
        description = (_clean_text(product.get("description") or "") or 
                    _extract_meta_content(html, "og:description") or 
                    _extract_meta_content(html, "description"))
        
        if product.get("brand"):
            if isinstance(product["brand"], dict):
                brand = _clean_text(product["brand"].get("name") or "")
            else:
                brand = _clean_text(str(product["brand"]))

        # 메타 태그에서 가격 정보 2차 시도
        if not price:
            price = _extract_meta_content(html, "product:price:amount") or _extract_meta_content(html, "og:price:amount")
        if not currency:
            currency = _extract_meta_content(html, "product:price:currency") or _extract_meta_content(html, "og:price:currency")

        normalized_image_url = urljoin(final_url, image_url) if image_url else ""

        # --- 1차 방어막: 크롤링 결과가 부실할 때 Gemini 폴백 실행 ---
        if not title or not normalized_image_url:
            print(f"[{url}] 파싱 정보 부족. Gemini 폴백 실행...")
            gemini_result = fallback_with_gemini(url)
            if gemini_result and gemini_result.get("title") and gemini_result.get("image_url"):
                return gemini_result

        return {
            "url": final_url,
            "title": title,
            "brand": brand,
            "price": price,
            "currency": currency,
            "availability": availability,
            "image_url": normalized_image_url,
            "description": description,
            "source": "json-ld/meta-tags",
        }

    except Exception as e:
        # --- 2차 방어막: 타임아웃이나 차단 에러 시 Gemini 폴백 실행 ---
        print(f"[{url}] 접근 차단 또는 에러 발생({e}). Gemini 폴백 실행...")
        gemini_result = fallback_with_gemini(url) # 여기서 final_url 대신 원본 url 사용
        if gemini_result and gemini_result.get("title") and gemini_result.get("image_url"):
            return gemini_result

        # 최악의 경우에도 앱이 터지지 않도록 기본값 반환
        return {
            "url": url,
            "title": "추출 실패",
            "brand": "",
            "price": "",
            "currency": "",
            "availability": "",
            "image_url": "",
            "description": "데이터를 불러올 수 없습니다.",
            "source": "error-fallback",
        }