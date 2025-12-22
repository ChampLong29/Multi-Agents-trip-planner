"""高德地图服务封装"""

import json
from typing import List, Dict, Any, Optional
from ..config import get_settings
from ..models.schemas import Location, POIInfo, WeatherInfo
from ..tools import AmapPOISearchTool, AmapWeatherTool, AmapRouteTool

# 全局工具实例
_amap_tools = None


def get_amap_tools_list():
    """
    获取高德地图LangChain工具列表(单例模式)
    
    Returns:
        工具列表
    """
    global _amap_tools
    
    if _amap_tools is None:
        settings = get_settings()
        
        if not settings.amap_api_key:
            raise ValueError("高德地图API Key未配置,请在.env文件中设置AMAP_API_KEY")
        
        # 创建LangChain工具
        from ..tools import get_amap_tools
        _amap_tools = get_amap_tools()
        
        print(f"✅ 高德地图工具初始化成功")
        print(f"   工具数量: {len(_amap_tools)}")
        print("   可用工具:")
        for tool in _amap_tools:
            print(f"     - {tool.name}")
    
    return _amap_tools


class AmapService:
    """高德地图服务封装类"""
    
    def __init__(self):
        """初始化服务"""
        self.poi_tool = AmapPOISearchTool()
        self.weather_tool = AmapWeatherTool()
        self.route_tool = AmapRouteTool()
    
    def search_poi(self, keywords: str, city: str, citylimit: bool = True) -> List[POIInfo]:
        """
        搜索POI
        
        Args:
            keywords: 搜索关键词
            city: 城市
            citylimit: 是否限制在城市范围内
            
        Returns:
            POI信息列表
        """
        try:
            # 调用LangChain工具
            result_str = self.poi_tool._run(keywords=keywords, city=city, citylimit=citylimit)
            result = json.loads(result_str)
            
            if result.get("error"):
                print(f"❌ POI搜索失败: {result['error']}")
                return []
            
            # 解析POI数据
            pois_data = result.get("pois", [])
            poi_list = []
            
            for poi_data in pois_data:
                location = Location(
                    longitude=poi_data.get("location", {}).get("longitude", 0.0),
                    latitude=poi_data.get("location", {}).get("latitude", 0.0)
                )
                
                # 处理 tel 字段：可能是字符串、列表或 None
                tel_value = poi_data.get("tel", "")
                if isinstance(tel_value, list):
                    # 如果是列表，取第一个元素或转为字符串
                    tel_value = tel_value[0] if tel_value else None
                elif not tel_value or tel_value == "":
                    tel_value = None
                
                poi_info = POIInfo(
                    id=poi_data.get("id", ""),
                    name=poi_data.get("name", ""),
                    address=poi_data.get("address", ""),
                    location=location,
                    type=poi_data.get("type", ""),
                    tel=tel_value,
                    distance=poi_data.get("distance", ""),
                    rating=poi_data.get("rating", "")
                )
                poi_list.append(poi_info)
            
            print(f"✅ POI搜索成功，找到 {len(poi_list)} 个结果")
            return poi_list
            
        except Exception as e:
            print(f"❌ POI搜索失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_weather(self, city: str) -> List[WeatherInfo]:
        """
        查询天气
        
        Args:
            city: 城市名称
            
        Returns:
            天气信息列表
        """
        try:
            # 调用LangChain工具
            result_str = self.weather_tool._run(city=city)
            result = json.loads(result_str)
            
            if result.get("error"):
                print(f"❌ 天气查询失败: {result['error']}")
                return []
            
            # 解析天气数据
            forecasts = result.get("forecasts", [])
            weather_list = []
            
            for forecast in forecasts:
                weather_info = WeatherInfo(
                    date=forecast.get("date", ""),
                    day_weather=forecast.get("dayweather", ""),
                    night_weather=forecast.get("nightweather", ""),
                    day_temp=int(forecast.get("daytemp", 0)) if forecast.get("daytemp") else 0,
                    night_temp=int(forecast.get("nighttemp", 0)) if forecast.get("nighttemp") else 0,
                    wind_direction=forecast.get("daywind", ""),
                    wind_power=forecast.get("daypower", "")
                )
                weather_list.append(weather_info)
            
            print(f"✅ 天气查询成功，获取 {len(weather_list)} 天天气")
            return weather_list
            
        except Exception as e:
            print(f"❌ 天气查询失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def plan_route(
        self,
        origin_address: str,
        destination_address: str,
        origin_city: Optional[str] = None,
        destination_city: Optional[str] = None,
        route_type: str = "walking"
    ) -> Dict[str, Any]:
        """
        规划路线
        
        Args:
            origin_address: 起点地址
            destination_address: 终点地址
            origin_city: 起点城市
            destination_city: 终点城市
            route_type: 路线类型 (walking/driving/transit)
            
        Returns:
            路线信息
        """
        try:
            # 构建起点和终点
            origin = f"{origin_city}{origin_address}" if origin_city else origin_address
            destination = f"{destination_city}{destination_address}" if destination_city else destination_address
            
            # 调用LangChain工具
            result_str = self.route_tool._run(
                origin=origin,
                destination=destination,
                strategy=0
            )
            result = json.loads(result_str)
            
            if result.get("error"):
                print(f"❌ 路线规划失败: {result['error']}")
                return {}
            
            route_data = result.get("route", {})
            print(f"✅ 路线规划成功，距离: {route_data.get('distance', 'N/A')}米")
            return route_data
            
        except Exception as e:
            print(f"❌ 路线规划失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {}
    
    def geocode(self, address: str, city: Optional[str] = None) -> Optional[Location]:
        """
        地理编码(地址转坐标)

        Args:
            address: 地址
            city: 城市

        Returns:
            经纬度坐标
        """
        try:
            import httpx
            settings = get_settings()
            if not settings.amap_api_key:
                return None
            
            url = "https://restapi.amap.com/v3/geocode/geo"
            full_address = f"{city}{address}" if city else address
            params = {
                "key": settings.amap_api_key,
                "address": full_address,
                "output": "json"
            }
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            if data.get("status") != "1" or not data.get("geocodes"):
                return None
            
            location_str = data["geocodes"][0].get("location", "")
            if location_str:
                try:
                    lon, lat = location_str.split(",")
                    return Location(longitude=float(lon), latitude=float(lat))
                except:
                    pass
            
            return None

        except Exception as e:
            print(f"❌ 地理编码失败: {str(e)}")
            return None

    def get_poi_detail(self, poi_id: str) -> Dict[str, Any]:
        """
        获取POI详情

        Args:
            poi_id: POI ID

        Returns:
            POI详情信息
        """
        try:
            import httpx
            settings = get_settings()
            if not settings.amap_api_key:
                return {}
            
            url = "https://restapi.amap.com/v3/place/detail"
            params = {
                "key": settings.amap_api_key,
                "id": poi_id,
                "output": "json",
                "extensions": "all"
            }
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            if data.get("status") != "1":
                return {}
            
            pois = data.get("pois", [])
            if not pois:
                return {}
            
            return pois[0]

        except Exception as e:
            print(f"❌ 获取POI详情失败: {str(e)}")
            return {}


# 创建全局服务实例
_amap_service = None


def get_amap_service() -> AmapService:
    """获取高德地图服务实例(单例模式)"""
    global _amap_service
    
    if _amap_service is None:
        _amap_service = AmapService()
    
    return _amap_service

