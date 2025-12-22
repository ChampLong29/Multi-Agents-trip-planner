"""Unsplash图片服务"""

import requests
from typing import List, Optional
from ..config import get_settings

class UnsplashService:
    """Unsplash图片服务类"""
    
    def __init__(self):
        """初始化服务"""
        settings = get_settings()
        self.access_key = settings.unsplash_access_key
        self.base_url = "https://api.unsplash.com"
        
        # 检查并输出配置状态
        if self.access_key and self.access_key.strip():
            print(f"✅ Unsplash API key 已配置，图片搜索功能已启用")
        else:
            print(f"⚠️  Unsplash API key 未配置，图片搜索将使用占位符")
    
    def search_photos(self, query: str, per_page: int = 5) -> List[dict]:
        """
        搜索图片
        
        Args:
            query: 搜索关键词
            per_page: 每页数量
            
        Returns:
            图片列表
        """
        # 如果 API key 未配置，返回空列表
        if not self.access_key or self.access_key.strip() == "":
            print("⚠️  Unsplash API key 未配置，跳过图片搜索")
            return []
        
        try:
            print(f"🔍 正在从 Unsplash 搜索图片: {query}")
            url = f"{self.base_url}/search/photos"
            params = {
                "query": query,
                "per_page": per_page,
                "client_id": self.access_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            # 提取图片URL
            photos = []
            for photo in results:
                photos.append({
                    "id": photo.get("id"),
                    "url": photo.get("urls", {}).get("regular"),
                    "thumb": photo.get("urls", {}).get("thumb"),
                    "description": photo.get("description") or photo.get("alt_description"),
                    "photographer": photo.get("user", {}).get("name")
                })
            
            if photos:
                print(f"✅ Unsplash 搜索成功，找到 {len(photos)} 张图片")
            else:
                print(f"⚠️  Unsplash 搜索未找到图片: {query}")
            
            return photos
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                print(f"⚠️  Unsplash API key 无效或已过期，请检查配置")
            elif e.response.status_code == 403:
                print(f"⚠️  Unsplash API 访问被拒绝，请检查 API key 权限")
            else:
                print(f"❌ Unsplash 搜索失败 (HTTP {e.response.status_code}): {str(e)}")
            return []
        except Exception as e:
            print(f"❌ Unsplash 搜索失败: {str(e)}")
            return []
    
    def get_photo_url(self, query: str) -> Optional[str]:
        """
        获取单张图片URL

        Args:
            query: 搜索关键词

        Returns:
            图片URL
        """
        photos = self.search_photos(query, per_page=1)
        if photos:
            return photos[0].get("url")
        return None


# 全局服务实例
_unsplash_service = None


def get_unsplash_service() -> UnsplashService:
    """获取Unsplash服务实例(单例模式)"""
    global _unsplash_service
    
    if _unsplash_service is None:
        _unsplash_service = UnsplashService()
    
    return _unsplash_service

