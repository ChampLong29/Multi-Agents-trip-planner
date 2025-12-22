"""POI相关API路由"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from ...services.amap_service import get_amap_service
from ...services.image_service import get_image_service

router = APIRouter(prefix="/poi", tags=["POI"])


class POIDetailResponse(BaseModel):
    """POI详情响应"""
    success: bool
    message: str
    data: Optional[dict] = None


@router.get(
    "/detail/{poi_id}",
    response_model=POIDetailResponse,
    summary="获取POI详情",
    description="根据POI ID获取详细信息,包括图片"
)
async def get_poi_detail(poi_id: str):
    """
    获取POI详情
    
    Args:
        poi_id: POI ID
        
    Returns:
        POI详情响应
    """
    try:
        amap_service = get_amap_service()
        
        # 调用高德地图POI详情API
        result = amap_service.get_poi_detail(poi_id)
        
        return POIDetailResponse(
            success=True,
            message="获取POI详情成功",
            data=result
        )
        
    except Exception as e:
        print(f"❌ 获取POI详情失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取POI详情失败: {str(e)}"
        )


@router.get(
    "/search",
    summary="搜索POI",
    description="根据关键词搜索POI"
)
async def search_poi(keywords: str, city: str = "北京"):
    """
    搜索POI

    Args:
        keywords: 搜索关键词
        city: 城市名称

    Returns:
        搜索结果
    """
    try:
        amap_service = get_amap_service()
        result = amap_service.search_poi(keywords, city)

        return {
            "success": True,
            "message": "搜索成功",
            "data": result
        }

    except Exception as e:
        print(f"❌ 搜索POI失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"搜索POI失败: {str(e)}"
        )


@router.get(
    "/photo",
    summary="获取景点图片",
    description="根据景点名称获取图片（多源回退：高德POI > 必应 > Unsplash > 占位符）"
)
async def get_attraction_photo(name: str, poi_id: str = None):
    """
    获取景点图片（多源策略）

    Args:
        name: 景点名称
        poi_id: 高德地图POI ID（可选，如果提供会优先从POI详情获取）

    Returns:
        图片URL（如果无法获取则返回占位符）
    """
    try:
        image_service = get_image_service()
        
        # 使用多源图片服务
        photo_url = image_service.get_attraction_image(name, poi_id)

        return {
            "success": True,
            "message": "获取图片成功",
            "data": {
                "name": name,
                "photo_url": photo_url
            }
        }

    except Exception as e:
        print(f"❌ 获取景点图片失败: {str(e)}")
        # 即使出错也返回占位符，避免前端显示错误
        import urllib.parse
        encoded_name = urllib.parse.quote(name)
        placeholder_url = f"https://via.placeholder.com/400x300/667eea/ffffff?text={encoded_name}"
        return {
            "success": True,
            "message": "使用占位符图片",
            "data": {
                "name": name,
                "photo_url": placeholder_url
            }
        }

