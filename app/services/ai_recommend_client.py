"""AI 백엔드 추천 서비스 클라이언트"""

import httpx
import logging
from typing import Dict, Any

from ..core.config import get_settings

logger = logging.getLogger(__name__)


class AIRecommendClient:
    """AI 백엔드 추천 서비스와 통신하는 클라이언트"""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.ai_backend_url
        self.ai_backend_recommendations_path = self.settings.ai_backend_recommendations_path
        self.timeout = self.settings.ai_backend_timeout_seconds
    
    async def get_user_recommendations(self, user_id: str) -> Dict[str, Any]:
        """
        AI 백엔드에서 사용자 추천 정보를 조회
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            추천 결과 딕셔너리 {"user_id": str, "rec_people": List[str], "rec_travel": List[str], "status": str}
            
        Raises:
            httpx.HTTPStatusError: HTTP 에러 발생 시
            httpx.TimeoutException: 타임아웃 발생 시
        """
        url = f"{self.base_url}{self.ai_backend_recommendations_path}"
        
        payload = {"user_id": user_id}
        
        logger.info(f"AI 백엔드 추천 요청: {url}, user_id: {user_id}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.debug(f"HTTP 요청 시작: {url}")
                logger.debug(f"Payload: {payload}")
                
                response = await client.post(url, json=payload)
                
                logger.debug(f"HTTP 응답 상태: {response.status_code}")
                logger.debug(f"HTTP 응답 헤더: {dict(response.headers)}")
                
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"AI 백엔드 응답 성공: user_id={user_id}, "
                          f"rec_people={len(result.get('rec_people', []))}, "
                          f"rec_travel={len(result.get('rec_travel', []))}")
                
                return result
                
        except httpx.TimeoutException as e:
            logger.error(f"AI 백엔드 요청 타임아웃: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"AI 백엔드 HTTP 에러: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.ConnectError as e:
            logger.error(f"AI 백엔드 연결 실패: {e}")
            logger.error(f"연결 시도 URL: {url}")
            raise
        except Exception as e:
            logger.error(f"AI 백엔드 요청 실패: {type(e).__name__}: {e}")
            logger.error(f"연결 시도 URL: {url}")
            raise


# 전역 인스턴스
ai_recommend_client = AIRecommendClient()


def get_ai_recommend_client() -> AIRecommendClient:
    """AI 추천 클라이언트 인스턴스 반환"""
    return ai_recommend_client
