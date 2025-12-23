"""高德地图 LangChain 工具"""

import json
import httpx
from typing import Optional, List, Dict, Any
from langchain_core.tools import BaseTool
from pydantic import Field
from ..config import get_settings
from ..models.schemas import POIInfo, WeatherInfo, Location


class AmapPOISearchTool(BaseTool):
    """高德地图POI搜索工具"""
    
    name: str = "amap_poi_search"
    description: str = """搜索指定城市的景点、餐厅、酒店等POI信息。
    
    输入应该是包含以下信息的JSON字符串：
    {
        "keywords": "搜索关键词，如'景点'、'餐厅'、'酒店'等",
        "city": "城市名称，如'北京'、'上海'等",
        "citylimit": true/false, 是否限制在城市范围内（可选，默认true）
    }
    
    返回POI信息列表，包括名称、地址、经纬度、类型等。
    """
    
    def _run(
        self,
        keywords: str,
        city: str,
        citylimit: bool = True,
        run_manager: Optional[Any] = None,
    ) -> str:
        """执行POI搜索"""
        try:
            settings = get_settings()
            if not settings.amap_api_key:
                return json.dumps({"error": "高德地图API Key未配置"})
            
            # 调用高德地图POI搜索API
            url = "https://restapi.amap.com/v3/place/text"
            params = {
                "key": settings.amap_api_key,
                "keywords": keywords,
                "city": city,
                "citylimit": "true" if citylimit else "false",
                "output": "json",
                "offset": 20,  # 返回结果数量
                "page": 1,
                "extensions": "all"  # 返回详细信息
            }
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            if data.get("status") != "1":
                error_msg = data.get("info", "未知错误")
                return json.dumps({"error": f"高德地图API错误: {error_msg}"})
            
            # 解析POI数据
            pois = data.get("pois", [])
            result = []
            
            for poi in pois:
                location_str = poi.get("location", "")
                longitude, latitude = 0.0, 0.0
                if location_str:
                    try:
                        lon, lat = location_str.split(",")
                        longitude = float(lon)
                        latitude = float(lat)
                    except:
                        pass
                
                poi_info = {
                    "id": poi.get("id", ""),
                    "name": poi.get("name", ""),
                    "address": poi.get("address", ""),
                    "location": {
                        "longitude": longitude,
                        "latitude": latitude
                    },
                    "type": poi.get("type", ""),
                    "tel": poi.get("tel", ""),
                    "distance": poi.get("distance", ""),
                    "rating": poi.get("rating", ""),
                    "cost": poi.get("cost", ""),
                    "business_area": poi.get("business_area", "")
                }
                result.append(poi_info)
            
            return json.dumps({
                "success": True,
                "count": len(result),
                "pois": result
            }, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({"error": f"POI搜索失败: {str(e)}"})
    
    async def _arun(
        self,
        keywords: str,
        city: str,
        citylimit: bool = True,
        run_manager: Optional[Any] = None,
    ) -> str:
        """异步执行POI搜索"""
        try:
            settings = get_settings()
            if not settings.amap_api_key:
                return json.dumps({"error": "高德地图API Key未配置"})
            
            url = "https://restapi.amap.com/v3/place/text"
            params = {
                "key": settings.amap_api_key,
                "keywords": keywords,
                "city": city,
                "citylimit": "true" if citylimit else "false",
                "output": "json",
                "offset": 20,
                "page": 1,
                "extensions": "all"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            if data.get("status") != "1":
                error_msg = data.get("info", "未知错误")
                return json.dumps({"error": f"高德地图API错误: {error_msg}"})
            
            pois = data.get("pois", [])
            result = []
            
            for poi in pois:
                location_str = poi.get("location", "")
                longitude, latitude = 0.0, 0.0
                if location_str:
                    try:
                        lon, lat = location_str.split(",")
                        longitude = float(lon)
                        latitude = float(lat)
                    except:
                        pass
                
                poi_info = {
                    "id": poi.get("id", ""),
                    "name": poi.get("name", ""),
                    "address": poi.get("address", ""),
                    "location": {
                        "longitude": longitude,
                        "latitude": latitude
                    },
                    "type": poi.get("type", ""),
                    "tel": poi.get("tel", ""),
                    "distance": poi.get("distance", ""),
                    "rating": poi.get("rating", ""),
                    "cost": poi.get("cost", ""),
                    "business_area": poi.get("business_area", "")
                }
                result.append(poi_info)
            
            return json.dumps({
                "success": True,
                "count": len(result),
                "pois": result
            }, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({"error": f"POI搜索失败: {str(e)}"})


class AmapWeatherTool(BaseTool):
    """高德地图天气查询工具"""
    
    name: str = "amap_weather"
    description: str = """查询指定城市的天气信息。
    
    输入应该是城市名称，如'北京'、'上海'等。
    
    返回未来几天的天气信息，包括日期、白天/夜间天气、温度、风向、风力等。
    """
    
    def _run(
        self,
        city: str,
        run_manager: Optional[Any] = None,
    ) -> str:
        """执行天气查询"""
        try:
            settings = get_settings()
            if not settings.amap_api_key:
                return json.dumps({"error": "高德地图API Key未配置"})
            
            # 先进行地理编码获取城市adcode
            geocode_url = "https://restapi.amap.com/v3/geocode/geo"
            geocode_params = {
                "key": settings.amap_api_key,
                "address": city,
                "output": "json"
            }
            
            with httpx.Client(timeout=10.0) as client:
                geocode_response = client.get(geocode_url, params=geocode_params)
                geocode_response.raise_for_status()
                geocode_data = geocode_response.json()
            
            if geocode_data.get("status") != "1" or not geocode_data.get("geocodes"):
                return json.dumps({"error": f"无法找到城市: {city}"})
            
            adcode = geocode_data["geocodes"][0].get("adcode", "")
            if not adcode:
                return json.dumps({"error": f"无法获取城市编码: {city}"})
            
            # 查询天气
            weather_url = "https://restapi.amap.com/v3/weather/weatherInfo"
            weather_params = {
                "key": settings.amap_api_key,
                "city": adcode,
                "extensions": "all",  # 获取预报天气
                "output": "json"
            }
            
            with httpx.Client(timeout=10.0) as client:
                weather_response = client.get(weather_url, params=weather_params)
                weather_response.raise_for_status()
                weather_data = weather_response.json()
            
            if weather_data.get("status") != "1":
                error_msg = weather_data.get("info", "未知错误")
                print(f"❌ 天气API返回错误: status={weather_data.get('status')}, info={error_msg}")
                print(f"完整响应: {weather_data}")
                return json.dumps({"error": f"天气查询失败: {error_msg}"})
            
            # 解析天气数据
            forecasts = weather_data.get("forecasts", [])
            print(f"🔍 天气API响应 - forecasts数量: {len(forecasts)}")
            if not forecasts:
                print(f"⚠️ 天气API返回成功但forecasts为空，完整响应: {weather_data}")
                return json.dumps({"error": "未找到天气数据"})
            
            forecast = forecasts[0]
            casts = forecast.get("casts", [])
            print(f"🔍 天气API响应 - casts数量: {len(casts)}")
            if not casts:
                print(f"⚠️ forecast存在但casts为空，forecast数据: {forecast}")
            
            result = []
            for cast in casts:
                weather_info = {
                    "date": cast.get("date", ""),
                    "week": cast.get("week", ""),
                    "dayweather": cast.get("dayweather", ""),
                    "nightweather": cast.get("nightweather", ""),
                    "daytemp": cast.get("daytemp", ""),
                    "nighttemp": cast.get("nighttemp", ""),
                    "daywind": cast.get("daywind", ""),
                    "nightwind": cast.get("nightwind", ""),
                    "daypower": cast.get("daypower", ""),
                    "nightpower": cast.get("nightpower", "")
                }
                result.append(weather_info)
            
            return json.dumps({
                "success": True,
                "city": forecast.get("city", city),
                "report_time": forecast.get("report_time", ""),
                "forecasts": result
            }, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({"error": f"天气查询失败: {str(e)}"})
    
    async def _arun(
        self,
        city: str,
        run_manager: Optional[Any] = None,
    ) -> str:
        """异步执行天气查询"""
        try:
            settings = get_settings()
            if not settings.amap_api_key:
                return json.dumps({"error": "高德地图API Key未配置"})
            
            # 地理编码
            geocode_url = "https://restapi.amap.com/v3/geocode/geo"
            geocode_params = {
                "key": settings.amap_api_key,
                "address": city,
                "output": "json"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                geocode_response = await client.get(geocode_url, params=geocode_params)
                geocode_response.raise_for_status()
                geocode_data = geocode_response.json()
            
            if geocode_data.get("status") != "1" or not geocode_data.get("geocodes"):
                return json.dumps({"error": f"无法找到城市: {city}"})
            
            adcode = geocode_data["geocodes"][0].get("adcode", "")
            if not adcode:
                return json.dumps({"error": f"无法获取城市编码: {city}"})
            
            # 查询天气
            weather_url = "https://restapi.amap.com/v3/weather/weatherInfo"
            weather_params = {
                "key": settings.amap_api_key,
                "city": adcode,
                "extensions": "all",
                "output": "json"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                weather_response = await client.get(weather_url, params=weather_params)
                weather_response.raise_for_status()
                weather_data = weather_response.json()
            
            if weather_data.get("status") != "1":
                error_msg = weather_data.get("info", "未知错误")
                print(f"❌ 天气API返回错误: status={weather_data.get('status')}, info={error_msg}")
                print(f"完整响应: {weather_data}")
                return json.dumps({"error": f"天气查询失败: {error_msg}"})
            
            forecasts = weather_data.get("forecasts", [])
            print(f"🔍 天气API响应(异步) - forecasts数量: {len(forecasts)}")
            if not forecasts:
                print(f"⚠️ 天气API返回成功但forecasts为空，完整响应: {weather_data}")
                return json.dumps({"error": "未找到天气数据"})
            
            forecast = forecasts[0]
            casts = forecast.get("casts", [])
            print(f"🔍 天气API响应(异步) - casts数量: {len(casts)}")
            if not casts:
                print(f"⚠️ forecast存在但casts为空，forecast数据: {forecast}")
            
            result = []
            for cast in casts:
                weather_info = {
                    "date": cast.get("date", ""),
                    "week": cast.get("week", ""),
                    "dayweather": cast.get("dayweather", ""),
                    "nightweather": cast.get("nightweather", ""),
                    "daytemp": cast.get("daytemp", ""),
                    "nighttemp": cast.get("nighttemp", ""),
                    "daywind": cast.get("daywind", ""),
                    "nightwind": cast.get("nightwind", ""),
                    "daypower": cast.get("daypower", ""),
                    "nightpower": cast.get("nightpower", "")
                }
                result.append(weather_info)
            
            return json.dumps({
                "success": True,
                "city": forecast.get("city", city),
                "report_time": forecast.get("report_time", ""),
                "forecasts": result
            }, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({"error": f"天气查询失败: {str(e)}"})


class AmapRouteTool(BaseTool):
    """高德地图路线规划工具"""
    
    name: str = "amap_route"
    description: str = """规划两点之间的路线。
    
    输入应该是包含以下信息的JSON字符串：
    {
        "origin": "起点地址或坐标（格式：经度,纬度 或 地址）",
        "destination": "终点地址或坐标（格式：经度,纬度 或 地址）",
        "strategy": "路线策略（可选，默认0）",
        "waypoints": "途经点（可选，多个点用|分隔）"
    }
    
    返回路线信息，包括距离、时间、路线坐标等。
    """
    
    def _run(
        self,
        origin: str,
        destination: str,
        strategy: int = 0,
        waypoints: Optional[str] = None,
        run_manager: Optional[Any] = None,
    ) -> str:
        """执行路线规划"""
        try:
            settings = get_settings()
            if not settings.amap_api_key:
                return json.dumps({"error": "高德地图API Key未配置"})
            
            url = "https://restapi.amap.com/v3/direction/driving"
            params = {
                "key": settings.amap_api_key,
                "origin": origin,
                "destination": destination,
                "strategy": str(strategy),
                "output": "json",
                "extensions": "all"
            }
            
            if waypoints:
                params["waypoints"] = waypoints
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            if data.get("status") != "1":
                error_msg = data.get("info", "未知错误")
                return json.dumps({"error": f"路线规划失败: {error_msg}"})
            
            route_data = data.get("route", {})
            paths = route_data.get("paths", [])
            
            if not paths:
                return json.dumps({"error": "未找到路线"})
            
            # 取第一条路线
            path = paths[0]
            result = {
                "distance": path.get("distance", ""),  # 米
                "duration": path.get("duration", ""),  # 秒
                "strategy": path.get("strategy", ""),
                "tolls": path.get("tolls", ""),
                "toll_distance": path.get("toll_distance", ""),
                "steps": []
            }
            
            # 解析步骤
            steps = path.get("steps", [])
            for step in steps[:10]:  # 只取前10步
                result["steps"].append({
                    "instruction": step.get("instruction", ""),
                    "road": step.get("road", ""),
                    "distance": step.get("distance", ""),
                    "duration": step.get("duration", ""),
                    "polyline": step.get("polyline", "")
                })
            
            return json.dumps({
                "success": True,
                "route": result
            }, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({"error": f"路线规划失败: {str(e)}"})
    
    async def _arun(
        self,
        origin: str,
        destination: str,
        strategy: int = 0,
        waypoints: Optional[str] = None,
        run_manager: Optional[Any] = None,
    ) -> str:
        """异步执行路线规划"""
        try:
            settings = get_settings()
            if not settings.amap_api_key:
                return json.dumps({"error": "高德地图API Key未配置"})
            
            url = "https://restapi.amap.com/v3/direction/driving"
            params = {
                "key": settings.amap_api_key,
                "origin": origin,
                "destination": destination,
                "strategy": str(strategy),
                "output": "json",
                "extensions": "all"
            }
            
            if waypoints:
                params["waypoints"] = waypoints
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            if data.get("status") != "1":
                error_msg = data.get("info", "未知错误")
                return json.dumps({"error": f"路线规划失败: {error_msg}"})
            
            route_data = data.get("route", {})
            paths = route_data.get("paths", [])
            
            if not paths:
                return json.dumps({"error": "未找到路线"})
            
            path = paths[0]
            result = {
                "distance": path.get("distance", ""),
                "duration": path.get("duration", ""),
                "strategy": path.get("strategy", ""),
                "tolls": path.get("tolls", ""),
                "toll_distance": path.get("toll_distance", ""),
                "steps": []
            }
            
            steps = path.get("steps", [])
            for step in steps[:10]:
                result["steps"].append({
                    "instruction": step.get("instruction", ""),
                    "road": step.get("road", ""),
                    "distance": step.get("distance", ""),
                    "duration": step.get("duration", ""),
                    "polyline": step.get("polyline", "")
                })
            
            return json.dumps({
                "success": True,
                "route": result
            }, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({"error": f"路线规划失败: {str(e)}"})


def get_amap_tools() -> List[BaseTool]:
    """获取所有高德地图工具"""
    settings = get_settings()
    if not settings.amap_api_key:
        raise ValueError("高德地图API Key未配置,请在.env文件中设置AMAP_API_KEY")
    
    return [
        AmapPOISearchTool(),
        AmapWeatherTool(),
        AmapRouteTool()
    ]

