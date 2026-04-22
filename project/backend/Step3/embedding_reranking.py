import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from rembg import remove, new_session

class FashionReRankingPipeline:
    def __init__(self, lambda_weight=0.6):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.lambda_weight = lambda_weight
        
        print("Fashion-CLIP 및 배경 제거 세션 로드 중...")
        self.model_id = "patrickjohncyh/fashion-clip"
        self.processor = CLIPProcessor.from_pretrained(self.model_id)
        self.model = CLIPModel.from_pretrained(self.model_id).to(self.device)
        self.model.eval()
        
        self.rembg_session = new_session("u2net_human_seg")
        print("시스템 초기화 완료.")

    def preprocess_image(self, image_path: str) -> Image:
        """배경을 물리적으로 제거하고 하얀 캔버스의 RGB로 정규화합니다."""
        raw_img = Image.open(image_path).convert("RGBA")
        bg_removed_img = remove(
            raw_img, 
            session=self.rembg_session, 
            alpha_matting=True,
            alpha_matting_foreground_threshold=240,
            alpha_matting_background_threshold=10,
            alpha_matting_erode_size=10
        )
        white_canvas = Image.new("RGBA", bg_removed_img.size, "WHITE")
        white_canvas.paste(bg_removed_img, (0, 0), bg_removed_img)
        return white_canvas.convert("RGB")

    @torch.no_grad()
    def get_pure_vibe_vector(self, image_path: str, category_text: str) -> torch.Tensor:
        """[도메인 지식 분리] 이미지 임베딩 - λ(카테고리 텍스트 임베딩)"""
        # 텍스트 벡터 추출
        text_inputs = self.processor(text=[category_text], return_tensors="pt", padding=True).to(self.device)
        text_features = self.model.get_text_features(**text_inputs)
        
        # 이미지 벡터 추출 (배경 제거 적용)
        clean_img = self.preprocess_image(image_path)
        img_inputs = self.processor(images=clean_img, return_tensors="pt").to(self.device)
        img_features = self.model.get_image_features(**img_inputs)
        
        # 카테고리 잔차 차감 및 정규화
        vibe_vector = img_features - (self.lambda_weight * text_features)
        return F.normalize(vibe_vector, p=2, dim=1)

    @torch.no_grad()
    def build_user_taste_vector(self, wishlist_items: list[dict]) -> torch.Tensor:
        """[PCA 연산] 위시리스트 벡터 행렬에서 SVD를 통해 가장 지배적인 미학적 축(1st PC)을 추출합니다."""
        vibe_vectors = []
        for item in wishlist_items:
            vec = self.get_pure_vibe_vector(item["image_path"], item["category"])
            vibe_vectors.append(vec)
            
        # 행렬 결합: Shape (N_items, 512)
        wishlist_tensor = torch.cat(vibe_vectors, dim=0)
        
        # 방어 로직: 위시리스트가 1개뿐이라면 PCA 연산이 불가하므로 원본 반환
        if wishlist_tensor.size(0) == 1:
            return wishlist_tensor
            
        # 1. 평균 중심화 (Mean Centering)
        mean_vec = torch.mean(wishlist_tensor, dim=0, keepdim=True)
        centered_vectors = wishlist_tensor - mean_vec
        
        # 2. SVD (특이값 분해) 
        # torch.linalg.svd는 V 대신 V의 켤레전치인 Vh를 반환함
        U, S, Vh = torch.linalg.svd(centered_vectors, full_matrices=False)
        
        # 3. 1st Principal Component (분산이 가장 큰 축 = 공통된 핵심 취향)
        first_pc = Vh[0, :].unsqueeze(0)
        
        # 중심 벡터(기본적인 베이스라인)에 1st PC(취향의 엣지)를 더해 벡터 합성
        taste_vector = mean_vec + (0.5 * first_pc)
        
        return F.normalize(taste_vector, p=2, dim=1)

    def calculate_cosine_similarity(self, vec1: torch.Tensor, vec2: torch.Tensor) -> float:
        return F.cosine_similarity(vec1, vec2, dim=1).item()

    def rerank_search_results(self, search_results: list[dict], user_taste_vector: torch.Tensor) -> list[dict]:
        """추출된 단일 취향 벡터를 기반으로 수집된 상품들을 리랭킹합니다."""
        print(f"{len(search_results)}개 상품 리랭킹(PCA 기반) 연산 시작...")
        
        for item in search_results:
            try:
                # 검색 매물도 평가 전 카테고리/배경 노이즈 소거 처리
                item_vibe_vector = self.get_pure_vibe_vector(item["image_path"], item["category"])
                score = self.calculate_cosine_similarity(user_taste_vector, item_vibe_vector)
                item["aesthetic_score"] = round(score, 4)
            except Exception as e:
                print(f"{item.get('title', 'Unknown')} 처리 에러: {e}")
                item["aesthetic_score"] = -1.0
                
        return sorted(search_results, key=lambda x: x["aesthetic_score"], reverse=True)

# =====================================================================
# 테스트 실행
# =====================================================================
if __name__ == "__main__":
    pipeline = FashionReRankingPipeline(lambda_weight=0.6)
    
    # User Tower 데이터
    wishlist_data = [
        {"image_path": "./images/wish1_jacket.jpg", "category": "a jacket"},
        {"image_path": "./images/wish2_pants.jpg", "category": "pants"},
        {"image_path": "./images/wish3_shoes.jpg", "category": "sneakers"}
    ]
    
    taste_vector = pipeline.build_user_taste_vector(wishlist_data)
    
    # Item Tower (SerpApi 등) 결과
    search_results_data = [
        {"title": "나이키 샥스 오렌지", "image_path": "./images/match1.jpg", "category": "sneakers"},
        {"title": "깔끔한 무지 반팔티", "image_path": "./images/mismatch3.jpg", "category": "t-shirt"},
        {"title": "거친 워싱 버뮤다 팬츠", "image_path": "./images/match2.jpg", "category": "pants"}
    ]
    
    final_ranked_items = pipeline.rerank_search_results(search_results_data, taste_vector)
    
    print("\n[최종 PCA 기반 리랭킹 결과]")
    for rank, item in enumerate(final_ranked_items, 1):
        print(f"{rank}위 | {item['aesthetic_score']} | {item['title']}")