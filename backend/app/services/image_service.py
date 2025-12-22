"""多源图片服务 - 支持高德POI、必应、Unsplash等多种图片源"""

import requests
import urllib.parse
from typing import Optional, Dict, Any
from ..config import get_settings
from .amap_service import get_amap_service
from .unsplash_service import get_unsplash_service


class ImageService:
    """多源图片服务类 - 按优先级尝试多个图片源"""
    
    def __init__(self):
        """初始化服务"""
        self.settings = get_settings()
        self.amap_service = get_amap_service()
        self.unsplash_service = get_unsplash_service()
    
    def get_attraction_image(self, attraction_name: str, poi_id: Optional[str] = None) -> Optional[str]:
        """
        获取景点图片（多源回退策略）
        
        优先级：
        1. 高德地图POI详情（如果提供poi_id）
        2. 必应图片搜索（免费，无需API key）
        3. Unsplash（需要API key）
        4. 占位符图片
        
        Args:
            attraction_name: 景点名称
            poi_id: 高德地图POI ID（可选）
            
        Returns:
            图片URL
        """
        # 策略1: 尝试从高德POI详情获取图片
        if poi_id:
            image_url = self._get_amap_poi_image(poi_id)
            if image_url:
                print(f"✅ 从高德POI获取图片: {attraction_name}")
                return image_url
        
        # 策略2: 尝试必应图片搜索（免费，无需API key）
        image_url = self._get_bing_image(attraction_name)
        if image_url:
            print(f"✅ 从必应图片获取: {attraction_name}")
            return image_url
        
        # 策略3: 尝试Unsplash（需要API key，已配置）
        # 先尝试带 "China landmark" 的搜索
        image_url = self.unsplash_service.get_photo_url(f"{attraction_name} China landmark")
        if not image_url:
            # 如果没找到，尝试只用景点名称
            image_url = self.unsplash_service.get_photo_url(attraction_name)
        
        if image_url:
            print(f"✅ 从 Unsplash 获取图片: {attraction_name}")
            return image_url
        
        # 策略4: 返回占位符
        print(f"⚠️  使用占位符图片: {attraction_name}")
        return self._get_placeholder_image(attraction_name)
    
    def _get_amap_poi_image(self, poi_id: str) -> Optional[str]:
        """
        从高德地图POI详情获取图片
        
        Args:
            poi_id: POI ID
            
        Returns:
            图片URL
        """
        try:
            poi_detail = self.amap_service.get_poi_detail(poi_id)
            if not poi_detail:
                return None
            
            # 高德POI详情可能包含的图片字段
            # photos: 图片列表
            photos = poi_detail.get("photos", [])
            if photos and len(photos) > 0:
                # 取第一张图片
                photo_url = photos[0].get("url", "")
                if photo_url:
                    return photo_url
            
            # 尝试其他可能的图片字段
            image_url = poi_detail.get("image", "") or poi_detail.get("photo", "")
            if image_url:
                return image_url
            
            return None
            
        except Exception as e:
            print(f"⚠️  从高德POI获取图片失败: {str(e)}")
            return None
    
    def _get_bing_image(self, query: str) -> Optional[str]:
        """
        从必应图片搜索获取图片（免费，无需API key）
        
        注意：必应图片搜索API需要订阅，这里使用公开的图片搜索接口
        或者可以使用必应图片搜索的公开接口
        
        Args:
            query: 搜索关键词
            
        Returns:
            图片URL
        """
        try:
            # 方法1: 使用必应图片搜索的公开接口（需要API key，但免费层可用）
            # 如果没有API key，跳过
            
            # 方法2: 使用其他免费图片搜索服务
            # 这里使用一个简单的图片搜索代理（示例）
            # 实际项目中可以集成必应图片搜索API
            
            # 暂时返回None，让其他策略处理
            return None
            
        except Exception as e:
            print(f"⚠️  从必应图片获取失败: {str(e)}")
            return None
    
    def _get_placeholder_image(self, name: str) -> str:
        """
        获取占位符图片
        
        Args:
            name: 景点名称
            
        Returns:
            占位符图片URL
        """
        # 使用一个美观的占位符服务
        # 可以自定义颜色和文字
        encoded_name = urllib.parse.quote(name)
        return f"https://via.placeholder.com/400x300/667eea/ffffff?text={encoded_name}"
    
    def get_multiple_images(self, attraction_name: str, poi_id: Optional[str] = None, count: int = 3) -> list:
        """
        获取多张景点图片
        
        Args:
            attraction_name: 景点名称
            poi_id: POI ID
            count: 图片数量
            
        Returns:
            图片URL列表
        """
        images = []
        
        # 从高德POI获取多张图片
        if poi_id:
            try:
                poi_detail = self.amap_service.get_poi_detail(poi_id)
                if poi_detail:
                    photos = poi_detail.get("photos", [])
                    for photo in photos[:count]:
                        url = photo.get("url", "")
                        if url:
                            images.append(url)
            except:
                pass
        
        # 如果还不够，从Unsplash获取
        if len(images) < count:
            try:
                unsplash_photos = self.unsplash_service.search_photos(
                    f"{attraction_name} China landmark",
                    per_page=count - len(images)
                )
                for photo in unsplash_photos:
                    if photo.get("url"):
                        images.append(photo.get("url"))
            except:
                pass
        
        # 如果还不够，用占位符填充
        while len(images) < count:
            images.append(self._get_placeholder_image(attraction_name))
        
        return images[:count]


# 全局服务实例
_image_service = None


def get_image_service() -> ImageService:
    """获取图片服务实例(单例模式)"""
    global _image_service
    
    if _image_service is None:
        _image_service = ImageService()
    
    return _image_service

