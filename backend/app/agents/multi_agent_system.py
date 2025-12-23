"""基于 LangChain 的多智能体旅行规划系统"""

import json
import asyncio
from typing import TypedDict, List, Optional, Dict, Any, AsyncIterator
from datetime import datetime, timedelta
from langchain_core.messages import HumanMessage, SystemMessage
from ..services.llm_service import get_llm
from ..services.amap_service import get_amap_service
from ..tools import AmapPOISearchTool, AmapWeatherTool, AmapRouteTool
from ..models.schemas import (
    TripRequest, TripPlan, DayPlan, Attraction, Meal, WeatherInfo, 
    Location, Hotel, Budget, POIInfo
)


class TripPlanningState(TypedDict):
    """旅行规划状态"""
    request: TripRequest
    attractions: List[POIInfo]
    weather: List[WeatherInfo]
    hotels: List[Dict[str, Any]]
    plan: Optional[TripPlan]
    errors: List[str]
    progress: Dict[str, Any]  # 进度信息
    messages: List[Any]  # 消息历史
    memory_context: Optional[str]  # 用户记忆上下文


class MultiAgentTripPlanner:
    """多智能体旅行规划系统"""
    
    def __init__(self):
        """初始化多智能体系统"""
        print("🔄 开始初始化多智能体旅行规划系统...")
        
        self.llm = get_llm()
        self.amap_service = get_amap_service()
        
        # 创建工具
        self.poi_tool = AmapPOISearchTool()
        self.weather_tool = AmapWeatherTool()
        self.route_tool = AmapRouteTool()
        
        print("✅ 多智能体系统初始化成功")
    
    async def _search_attractions_node(self, state: TripPlanningState) -> TripPlanningState:
        """景点搜索节点"""
        print("📍 景点搜索智能体：开始搜索景点...")
        
        try:
            state["progress"]["attractions"]["status"] = "running"
            state["progress"]["attractions"]["progress"] = 50
            
            request = state["request"]
            
            # 构建搜索关键词
            keywords = "景点"
            if request.preferences:
                # 使用第一个偏好作为关键词
                keywords = request.preferences[0]
            
            # 调用工具搜索景点
            result_str = await self.poi_tool._arun(
                keywords=keywords,
                city=request.city,
                citylimit=True
            )
            
            result = json.loads(result_str)
            
            if result.get("error"):
                state["errors"].append(f"景点搜索失败: {result['error']}")
                state["progress"]["attractions"]["status"] = "failed"
                return state
            
            # 解析POI数据
            pois_data = result.get("pois", [])
            attractions = []
            
            for poi_data in pois_data[:15]:  # 限制数量
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
                
                # 处理 address 字段：可能是字符串、列表或 None
                address_value = poi_data.get("address", "")
                if isinstance(address_value, list):
                    # 如果是列表，取第一个元素或转为字符串
                    address_value = address_value[0] if address_value else ""
                elif not address_value:
                    address_value = ""
                
                poi_info = POIInfo(
                    id=poi_data.get("id", ""),
                    name=poi_data.get("name", ""),
                    address=address_value,
                    location=location,
                    type=poi_data.get("type", ""),
                    tel=tel_value
                )
                attractions.append(poi_info)
            
            state["attractions"] = attractions
            state["progress"]["attractions"]["status"] = "completed"
            state["progress"]["attractions"]["progress"] = 100
            
            print(f"✅ 景点搜索完成，找到 {len(attractions)} 个景点")
            
        except Exception as e:
            error_msg = f"景点搜索失败: {str(e)}"
            print(f"❌ {error_msg}")
            state["errors"].append(error_msg)
            state["progress"]["attractions"]["status"] = "failed"
        
        return state
    
    async def _search_weather_node(self, state: TripPlanningState) -> TripPlanningState:
        """天气查询节点"""
        print("🌤️ 天气查询智能体：开始查询天气...")
        
        try:
            state["progress"]["weather"]["status"] = "running"
            state["progress"]["weather"]["progress"] = 50
            
            request = state["request"]
            print(f"🔍 查询城市: {request.city}")
            
            # 调用工具查询天气
            result_str = await self.weather_tool._arun(city=request.city)
            print(f"🔍 天气API原始响应: {result_str[:500]}...")  # 只打印前500字符
            result = json.loads(result_str)
            
            if result.get("error"):
                print(f"❌ 天气API返回错误: {result['error']}")
                state["errors"].append(f"天气查询失败: {result['error']}")
                state["progress"]["weather"]["status"] = "failed"
                return state
            
            # 解析天气数据
            forecasts = result.get("forecasts", [])
            print(f"🔍 解析到的forecasts数量: {len(forecasts)}")
            if forecasts:
                print(f"🔍 第一个forecast示例: {forecasts[0]}")
            weather_list = []
            
            # 计算日期范围
            start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
            end_date = datetime.strptime(request.end_date, "%Y-%m-%d")
            
            for i in range(request.travel_days):
                current_date = start_date + timedelta(days=i)
                date_str = current_date.strftime("%Y-%m-%d")
                print(f"🔍 查找日期 {date_str} 的天气数据...")
                
                # 查找匹配的天气数据
                weather_data = None
                for forecast in forecasts:
                    forecast_date = forecast.get("date", "")
                    print(f"  - 对比: API日期={forecast_date}, 需要日期={date_str}")
                    if forecast_date == date_str:
                        weather_data = forecast
                        print(f"  ✅ 找到匹配的天气数据")
                        break
                
                if weather_data:
                    # 生成穿着建议和活动建议
                    day_weather = weather_data.get("dayweather", "")
                    day_temp = weather_data.get("daytemp", 0)
                    night_temp = weather_data.get("nighttemp", 0)
                    
                    # 解析温度（可能是字符串）
                    try:
                        if isinstance(day_temp, str):
                            day_temp = int(day_temp.replace("°C", "").replace("℃", "").strip())
                        if isinstance(night_temp, str):
                            night_temp = int(night_temp.replace("°C", "").replace("℃", "").strip())
                    except:
                        day_temp = 20
                        night_temp = 15
                    
                    avg_temp = (day_temp + night_temp) / 2
                    
                    # 生成穿着建议
                    clothing_suggestion = self._generate_clothing_suggestion(day_weather, avg_temp, day_temp, night_temp)
                    
                    # 生成活动建议
                    activity_suggestion = self._generate_activity_suggestion(day_weather, avg_temp)
                    
                    weather_info = WeatherInfo(
                        date=date_str,
                        day_weather=day_weather,
                        night_weather=weather_data.get("nightweather", ""),
                        day_temp=day_temp,
                        night_temp=night_temp,
                        wind_direction=weather_data.get("daywind", ""),
                        wind_power=weather_data.get("daypower", ""),
                        clothing_suggestion=clothing_suggestion,
                        activity_suggestion=activity_suggestion
                    )
                    weather_list.append(weather_info)
            
            state["weather"] = weather_list
            state["progress"]["weather"]["status"] = "completed"
            state["progress"]["weather"]["progress"] = 100
            
            print(f"✅ 天气查询完成，获取 {len(weather_list)} 天天气")
            
        except Exception as e:
            error_msg = f"天气查询失败: {str(e)}"
            print(f"❌ {error_msg}")
            state["errors"].append(error_msg)
            state["progress"]["weather"]["status"] = "failed"
        
        return state
    
    def _generate_clothing_suggestion(self, weather: str, avg_temp: float, day_temp: float, night_temp: float) -> str:
        """根据天气生成穿着建议"""
        suggestions = []
        
        # 根据温度建议
        if avg_temp >= 30:
            suggestions.append("建议穿着轻薄透气的短袖、短裤或短裙")
            suggestions.append("必备遮阳帽、太阳镜和防晒霜")
            suggestions.append("选择浅色、宽松的衣物")
        elif avg_temp >= 25:
            suggestions.append("建议穿着短袖T恤、薄长裤或短裤")
            suggestions.append("可携带薄外套或防晒衣")
        elif avg_temp >= 20:
            suggestions.append("建议穿着长袖T恤或薄衬衫")
            suggestions.append("可携带薄外套或风衣")
        elif avg_temp >= 15:
            suggestions.append("建议穿着长袖衬衫或薄毛衣")
            suggestions.append("建议携带外套或夹克")
        elif avg_temp >= 10:
            suggestions.append("建议穿着毛衣或薄羽绒服")
            suggestions.append("建议穿着长裤，可携带围巾")
        elif avg_temp >= 5:
            suggestions.append("建议穿着厚毛衣或薄羽绒服")
            suggestions.append("建议穿着厚外套，注意保暖")
        else:
            suggestions.append("建议穿着厚羽绒服或大衣")
            suggestions.append("建议穿着保暖内衣，注意防寒")
        
        # 根据天气状况建议
        weather_lower = weather.lower()
        if "雨" in weather_lower or "雨" in weather:
            suggestions.append("⚠️ 必须携带雨具（雨伞或雨衣）")
            suggestions.append("建议穿着防滑鞋，避免湿滑路面")
            suggestions.append("可携带防水包或塑料袋保护电子设备")
        elif "雪" in weather_lower or "雪" in weather:
            suggestions.append("⚠️ 必须穿着防滑鞋或雪地靴")
            suggestions.append("建议穿着防水外套")
            suggestions.append("建议携带手套和帽子")
        elif "风" in weather_lower or "风" in weather or int(avg_temp) < 15:
            suggestions.append("建议穿着防风外套")
            suggestions.append("可携带围巾或口罩防风")
        elif "晴" in weather_lower or "晴" in weather or "多云" in weather_lower:
            if avg_temp >= 20:
                suggestions.append("适合户外活动，注意防晒")
        
        # 温差建议
        temp_diff = abs(day_temp - night_temp)
        if temp_diff > 8:
            suggestions.append("⚠️ 昼夜温差较大，建议采用分层穿着，方便增减衣物")
        
        return "；".join(suggestions) if suggestions else "根据天气情况选择合适的衣物"
    
    def _generate_activity_suggestion(self, weather: str, avg_temp: float) -> str:
        """根据天气生成活动建议"""
        suggestions = []
        
        weather_lower = weather.lower()
        
        # 雨天建议
        if "雨" in weather_lower or "雨" in weather:
            suggestions.append("⚠️ 不适合户外游玩，建议选择室内景点（博物馆、美术馆、购物中心、室内娱乐场所等）")
            suggestions.append("⚠️ 不适合步行游览，建议使用公共交通或打车")
            suggestions.append("建议安排室内活动，如参观展览、看电影、购物等")
            suggestions.append("如必须外出，请携带雨具并注意安全")
        # 雪天建议
        elif "雪" in weather_lower or "雪" in weather:
            suggestions.append("⚠️ 不适合户外长时间活动，建议选择室内景点")
            suggestions.append("⚠️ 不适合步行，建议使用公共交通或打车")
            suggestions.append("如要户外活动，请穿着防滑鞋，注意安全")
        # 高温建议
        elif avg_temp >= 30:
            suggestions.append("⚠️ 高温天气，建议避免正午时段户外活动（11:00-15:00）")
            suggestions.append("建议选择有遮阴的景点或室内景点")
            suggestions.append("建议多安排室内活动，注意防暑降温")
            suggestions.append("适合早出晚归，避开高温时段")
        # 低温建议
        elif avg_temp <= 5:
            suggestions.append("⚠️ 低温天气，建议减少户外活动时间")
            suggestions.append("建议选择室内景点或短时间户外活动")
            suggestions.append("注意保暖，避免长时间在户外停留")
        # 大风建议
        elif "风" in weather_lower or "风" in weather:
            suggestions.append("⚠️ 大风天气，不适合户外长时间活动")
            suggestions.append("建议选择室内景点或避风场所")
            suggestions.append("如要户外活动，请注意安全，避免高空或危险区域")
        # 良好天气建议
        else:
            if avg_temp >= 20 and avg_temp < 30:
                suggestions.append("✅ 天气良好，适合户外游玩")
                suggestions.append("✅ 适合步行游览，可安排较多户外景点")
                suggestions.append("建议安排公园、景区等户外活动")
            elif avg_temp >= 15:
                suggestions.append("✅ 天气适宜，适合户外活动")
                suggestions.append("✅ 适合步行，可安排户外景点")
        
        return "；".join(suggestions) if suggestions else "根据天气情况合理安排活动"
    
    async def _search_hotels_node(self, state: TripPlanningState) -> TripPlanningState:
        """酒店搜索节点"""
        print("🏨 酒店推荐智能体：开始搜索酒店...")
        
        try:
            state["progress"]["hotels"]["status"] = "running"
            state["progress"]["hotels"]["progress"] = 50
            
            request = state["request"]
            
            # 构建搜索关键词
            keywords = request.accommodation or "酒店"
            
            # 调用工具搜索酒店
            result_str = await self.poi_tool._arun(
                keywords=keywords,
                city=request.city,
                citylimit=True
            )
            
            result = json.loads(result_str)
            
            if result.get("error"):
                state["errors"].append(f"酒店搜索失败: {result['error']}")
                state["progress"]["hotels"]["status"] = "failed"
                return state
            
            # 解析酒店数据
            pois_data = result.get("pois", [])
            hotels = []
            
            for poi_data in pois_data[:10]:  # 限制数量
                location = Location(
                    longitude=poi_data.get("location", {}).get("longitude", 0.0),
                    latitude=poi_data.get("location", {}).get("latitude", 0.0)
                )
                
                hotel_info = {
                    "name": poi_data.get("name", ""),
                    "address": poi_data.get("address", ""),
                    "location": location,
                    "type": poi_data.get("type", ""),
                    "tel": poi_data.get("tel", ""),
                    "rating": poi_data.get("rating", ""),
                    "cost": poi_data.get("cost", "")
                }
                hotels.append(hotel_info)
            
            state["hotels"] = hotels
            state["progress"]["hotels"]["status"] = "completed"
            state["progress"]["hotels"]["progress"] = 100
            
            print(f"✅ 酒店搜索完成，找到 {len(hotels)} 个酒店")
            
        except Exception as e:
            error_msg = f"酒店搜索失败: {str(e)}"
            print(f"❌ {error_msg}")
            state["errors"].append(error_msg)
            state["progress"]["hotels"]["status"] = "failed"
        
        return state
    
    async def _plan_trip_node(self, state: TripPlanningState) -> TripPlanningState:
        """行程规划节点：整合所有信息生成计划"""
        print("📋 行程规划智能体：开始生成行程计划...")
        
        try:
            state["progress"]["planning"]["status"] = "running"
            state["progress"]["planning"]["progress"] = 50
            
            request = state["request"]
            
            # 等待所有并行任务完成
            # 注意：在 LangGraph 中，节点会自动等待前置节点完成
            # 但我们需要确保数据已准备好
            
            # 构建规划提示词
            memory_context = state.get("memory_context") or ""
            planner_prompt = self._build_planner_prompt(
                request, 
                state["attractions"], 
                state["weather"], 
                state["hotels"],
                memory_context
            )
            
            # 调用 LLM 生成计划
            messages = [
                SystemMessage(content="你是一个专业的旅行规划助手。请根据提供的信息生成详细的旅行计划，返回JSON格式。"),
                HumanMessage(content=planner_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            plan_text = response.content
            
            # 解析响应
            trip_plan = self._parse_plan_response(plan_text, request)
            
            state["plan"] = trip_plan
            state["progress"]["planning"]["status"] = "completed"
            state["progress"]["planning"]["progress"] = 100
            
            print("✅ 行程规划完成")
            
        except Exception as e:
            error_msg = f"行程规划失败: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            state["errors"].append(error_msg)
            state["progress"]["planning"]["status"] = "failed"
            # 创建备用计划
            state["plan"] = self._create_fallback_plan(request)
        
        return state
    
    def _build_planner_prompt(
        self, 
        request: TripRequest, 
        attractions: List[POIInfo], 
        weather: List[WeatherInfo], 
        hotels: List[Dict[str, Any]],
        memory_context: str = ""
    ) -> str:
        """构建规划提示词"""
        attractions_text = "\n".join([
            f"- {attr.name} ({attr.address})"
            for attr in attractions[:20]
        ])
        
        weather_text = "\n".join([
            f"- {w.date}: 白天{w.day_weather} {w.day_temp}°C, 夜间{w.night_weather} {w.night_temp}°C\n"
            f"  穿着建议: {w.clothing_suggestion}\n"
            f"  活动建议: {w.activity_suggestion}"
            for w in weather
        ])
        
        hotels_text = "\n".join([
            f"- {h['name']} ({h['address']})"
            for h in hotels[:10]
        ])
        
        prompt = f"""请根据以下信息生成{request.city}的{request.travel_days}天旅行计划:

**基本信息:**
- 城市: {request.city}
- 日期: {request.start_date} 至 {request.end_date}
- 天数: {request.travel_days}天
- 交通方式: {request.transportation}
- 住宿: {request.accommodation}
- 偏好: {', '.join(request.preferences) if request.preferences else '无'}

"""
        # 添加用户记忆上下文
        if memory_context:
            prompt += f"**用户历史偏好和对话记忆:**\n{memory_context}\n\n"
        
        prompt += f"""**可用景点:**
{attractions_text}

**天气信息:**
{weather_text}

**可用酒店:**
{hotels_text}

**重要要求（必须严格遵守）:**
1. **根据天气调整行程安排**:
   - 如果某天是雨天、雪天或恶劣天气，必须优先安排室内景点（博物馆、美术馆、购物中心、室内娱乐场所等），避免安排户外景点
   - 如果某天是雨天或雪天，必须调整交通方式，避免步行，建议使用公共交通或打车
   - 如果某天是高温天气（≥30°C），避免在正午时段（11:00-15:00）安排户外活动
   - 如果某天是低温天气（≤5°C），减少户外活动时间，多安排室内景点
   - 如果某天是大风天气，避免安排高空或危险区域的户外活动
   - 在每天的行程描述中，必须说明为什么这样安排（考虑天气因素）

2. 每天安排2-3个景点（根据天气情况灵活调整）
3. 每天必须包含早中晚三餐
4. 每天推荐一个具体的酒店(从可用酒店中选择)
5. 考虑景点之间的距离和交通方式（雨天/雪天避免步行）
6. 返回完整的JSON格式数据
7. 景点的经纬度坐标要真实准确

请严格按照以下JSON格式返回:
{{
  "city": "{request.city}",
  "start_date": "{request.start_date}",
  "end_date": "{request.end_date}",
  "days": [
    {{
      "date": "YYYY-MM-DD",
      "day_index": 0,
      "description": "第1天行程概述",
      "transportation": "{request.transportation}",
      "accommodation": "{request.accommodation}",
      "hotel": {{
        "name": "酒店名称",
        "address": "酒店地址",
        "location": {{"longitude": 116.397128, "latitude": 39.916527}},
        "price_range": "300-500元",
        "rating": "4.5",
        "distance": "距离景点2公里",
        "type": "{request.accommodation}",
        "estimated_cost": 400
      }},
      "attractions": [
        {{
          "name": "景点名称",
          "address": "详细地址",
          "location": {{"longitude": 116.397128, "latitude": 39.916527}},
          "visit_duration": 120,
          "description": "景点详细描述",
          "category": "景点类别",
          "ticket_price": 60
        }}
      ],
      "meals": [
        {{"type": "breakfast", "name": "早餐推荐", "description": "早餐描述", "estimated_cost": 30}},
        {{"type": "lunch", "name": "午餐推荐", "description": "午餐描述", "estimated_cost": 50}},
        {{"type": "dinner", "name": "晚餐推荐", "description": "晚餐描述", "estimated_cost": 80}}
      ]
    }}
  ],
  "weather_info": {json.dumps([w.dict() for w in weather], ensure_ascii=False)},
  "overall_suggestions": "总体建议",
  "budget": {{
    "total_attractions": 180,
    "total_hotels": 1200,
    "total_meals": 480,
    "total_transportation": 200,
    "total": 2060
  }}
}}
"""
        
        if request.free_text_input:
            prompt += f"\n**额外要求:** {request.free_text_input}"
        
        return prompt
    
    def _parse_plan_response(self, response: str, request: TripRequest) -> TripPlan:
        """解析规划响应"""
        try:
            # 尝试从响应中提取JSON
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
            else:
                raise ValueError("响应中未找到JSON数据")
            
            # 先尝试直接解析，如果失败再修复
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError:
                # 只有在解析失败时才尝试修复
                print(f"⚠️  首次JSON解析失败，尝试修复...")
                json_str = self._fix_json_string(json_str)
                data = json.loads(json_str)
            
            # 确保 day_index 从 0 开始
            if "days" in data and isinstance(data["days"], list):
                for i, day in enumerate(data["days"]):
                    if isinstance(day, dict):
                        day["day_index"] = i
            
            # 转换为TripPlan对象
            trip_plan = TripPlan(**data)
            
            return trip_plan
            
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON解析失败: {str(e)}")
            print(f"   错误位置: line {e.lineno}, column {e.colno}")
            print(f"   尝试修复JSON...")
            try:
                # 尝试修复并重新解析
                fixed_json = self._fix_json_string(response[json_start:json_end] if 'json_str' in locals() else response)
                data = json.loads(fixed_json)
                if "days" in data and isinstance(data["days"], list):
                    for i, day in enumerate(data["days"]):
                        if isinstance(day, dict):
                            day["day_index"] = i
                trip_plan = TripPlan(**data)
                print(f"   ✅ JSON修复成功")
                return trip_plan
            except Exception as e2:
                print(f"   ❌ JSON修复失败: {str(e2)}")
                print(f"   将使用备用方案生成计划")
                return self._create_fallback_plan(request)
        except Exception as e:
            print(f"⚠️  解析响应失败: {str(e)}")
            import traceback
            traceback.print_exc()
            print(f"   将使用备用方案生成计划")
            return self._create_fallback_plan(request)
    
    def _fix_json_string(self, json_str: str) -> str:
        """尝试修复常见的 JSON 格式问题（保守策略）"""
        import re
        
        fixed_json = json_str
        
        # 1. 移除 JSON 中的注释（如果 LLM 添加了注释）
        # 只在字符串外移除注释
        fixed_json = re.sub(r'//.*?$', '', fixed_json, flags=re.MULTILINE)
        fixed_json = re.sub(r'/\*.*?\*/', '', fixed_json, flags=re.DOTALL)
        
        # 2. 修复末尾的逗号（在对象和数组末尾）
        fixed_json = re.sub(r',(\s*[}\]])', r'\1', fixed_json)
        
        # 3. 尝试修复未终止的字符串（保守策略）
        # 只在确实有问题时才修复
        try:
            # 先测试是否能解析
            json.loads(fixed_json)
            return fixed_json
        except json.JSONDecodeError as e:
            # 如果是字符串相关的错误，尝试修复
            if 'Unterminated string' in str(e) or 'Expecting' in str(e):
                # 尝试在错误位置附近修复
                lines = fixed_json.split('\n')
                if e.lineno <= len(lines):
                    error_line = lines[e.lineno - 1]
                    # 如果行尾有未闭合的引号，尝试闭合
                    if error_line.count('"') % 2 == 1:
                        # 检查是否在字符串中
                        quote_count = 0
                        escape = False
                        for char in error_line:
                            if escape:
                                escape = False
                                continue
                            if char == '\\':
                                escape = True
                                continue
                            if char == '"':
                                quote_count += 1
                        
                        # 如果引号数为奇数，可能是未闭合
                        if quote_count % 2 == 1:
                            # 在行尾添加闭合引号（如果还没有）
                            if not error_line.rstrip().endswith('"'):
                                lines[e.lineno - 1] = error_line.rstrip() + '"'
                                fixed_json = '\n'.join(lines)
                
                # 再次尝试解析
                try:
                    json.loads(fixed_json)
                    return fixed_json
                except:
                    pass
        
        return fixed_json
    
    def _create_fallback_plan(self, request: TripRequest) -> TripPlan:
        """创建备用计划"""
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
        
        days = []
        for i in range(request.travel_days):
            current_date = start_date + timedelta(days=i)
            
            day_plan = DayPlan(
                date=current_date.strftime("%Y-%m-%d"),
                day_index=i,
                description=f"第{i+1}天行程",
                transportation=request.transportation,
                accommodation=request.accommodation,
                attractions=[
                    Attraction(
                        name=f"{request.city}景点{j+1}",
                        address=f"{request.city}市",
                        location=Location(longitude=116.4 + i*0.01 + j*0.005, latitude=39.9 + i*0.01 + j*0.005),
                        visit_duration=120,
                        description=f"这是{request.city}的著名景点",
                        category="景点"
                    )
                    for j in range(2)
                ],
                meals=[
                    Meal(type="breakfast", name=f"第{i+1}天早餐", description="当地特色早餐"),
                    Meal(type="lunch", name=f"第{i+1}天午餐", description="午餐推荐"),
                    Meal(type="dinner", name=f"第{i+1}天晚餐", description="晚餐推荐")
                ]
            )
            days.append(day_plan)
        
        return TripPlan(
            city=request.city,
            start_date=request.start_date,
            end_date=request.end_date,
            days=days,
            weather_info=[],
            overall_suggestions=f"这是为您规划的{request.city}{request.travel_days}日游行程,建议提前查看各景点的开放时间。"
        )
    
    async def plan_trip(self, request: TripRequest, user_id: Optional[int] = None, session_id: Optional[str] = None) -> TripPlan:
        """生成旅行计划"""
        # 加载用户记忆上下文（如果提供了user_id）
        memory_context = ""
        if user_id:
            from sqlalchemy.orm import Session
            from ..models.database import SessionLocal
            from ..services.memory_service import build_memory_context
            
            # 获取数据库会话
            db = SessionLocal()
            try:
                memory_context = build_memory_context(db, user_id, request)
                if memory_context:
                    print(f"📝 加载用户记忆上下文...")
            finally:
                db.close()
        
        print(f"\n{'='*60}")
        print(f"🚀 开始多智能体协作规划旅行...")
        print(f"目的地: {request.city}")
        print(f"日期: {request.start_date} 至 {request.end_date}")
        print(f"天数: {request.travel_days}天")
        print(f"{'='*60}\n")
        
        # 初始化状态
        state: TripPlanningState = {
            "request": request,
            "attractions": [],
            "weather": [],
            "hotels": [],
            "plan": None,
            "errors": [],
            "progress": {
                "attractions": {"status": "pending", "progress": 0},
                "weather": {"status": "pending", "progress": 0},
                "hotels": {"status": "pending", "progress": 0},
                "planning": {"status": "pending", "progress": 0}
            },
            "messages": [],
            "memory_context": memory_context
        }
        
        # 并行执行三个搜索任务
        print("🔄 并行执行搜索任务...")
        attractions_task = self._search_attractions_node(state)
        weather_task = self._search_weather_node(state)
        hotels_task = self._search_hotels_node(state)
        
        # 等待所有并行任务完成
        await asyncio.gather(attractions_task, weather_task, hotels_task, return_exceptions=True)
        
        # 生成最终计划
        state = await self._plan_trip_node(state)
        
        if state.get("plan"):
            print(f"{'='*60}")
            print(f"✅ 旅行计划生成完成!")
            print(f"{'='*60}\n")
            return state["plan"]
        else:
            print(f"❌ 旅行计划生成失败")
            return self._create_fallback_plan(request)
    
    async def plan_trip_stream(
        self, 
        request: TripRequest,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """流式生成旅行计划"""
        # 发送开始事件
        yield {
            "type": "start",
            "message": "开始生成旅行计划",
            "progress": 0
        }
        
        # 加载用户记忆上下文（如果提供了user_id）
        memory_context = ""
        if user_id:
            from sqlalchemy.orm import Session
            from ..models.database import SessionLocal
            from ..services.memory_service import build_memory_context
            
            # 获取数据库会话
            db = SessionLocal()
            try:
                memory_context = build_memory_context(db, user_id, request)
                if memory_context:
                    yield {
                        "type": "info",
                        "message": "已加载用户历史偏好"
                    }
            finally:
                db.close()
        
        # 初始化状态
        state: TripPlanningState = {
            "request": request,
            "attractions": [],
            "weather": [],
            "hotels": [],
            "plan": None,
            "errors": [],
            "progress": {
                "attractions": {"status": "pending", "progress": 0},
                "weather": {"status": "pending", "progress": 0},
                "hotels": {"status": "pending", "progress": 0},
                "planning": {"status": "pending", "progress": 0}
            },
            "messages": [],
            "memory_context": memory_context
        }
        
        # 创建带进度回调的节点函数（包装为协程，收集事件）
        async def search_attractions_with_progress():
            events = []
            try:
                state["progress"]["attractions"]["status"] = "running"
                state["progress"]["attractions"]["progress"] = 10
                events.append({
                    "type": "progress",
                    "agent": "attractions",
                    "status": "running",
                    "progress": 10,
                    "message": "正在搜索景点..."
                })
                
                await self._search_attractions_node(state)
                
                # 确保状态正确更新
                final_status = state["progress"]["attractions"]["status"]
                final_progress = state["progress"]["attractions"]["progress"]
                
                events.append({
                    "type": "progress",
                    "agent": "attractions",
                    "status": final_status,
                    "progress": final_progress,
                    "message": "景点搜索完成" if final_status == "completed" else "景点搜索失败"
                })
                
                if state["attractions"]:
                    events.append({
                        "type": "data",
                        "agent": "attractions",
                        "data": [attr.dict() for attr in state["attractions"][:5]]
                    })
            except Exception as e:
                error_msg = f"景点搜索异常: {str(e)}"
                print(f"❌ {error_msg}")
                state["progress"]["attractions"]["status"] = "failed"
                state["progress"]["attractions"]["progress"] = 0
                events.append({
                    "type": "progress",
                    "agent": "attractions",
                    "status": "failed",
                    "progress": 0,
                    "message": error_msg
                })
            
            return events
        
        async def search_weather_with_progress():
            events = []
            try:
                state["progress"]["weather"]["status"] = "running"
                state["progress"]["weather"]["progress"] = 10
                events.append({
                    "type": "progress",
                    "agent": "weather",
                    "status": "running",
                    "progress": 10,
                    "message": "正在查询天气..."
                })
                
                await self._search_weather_node(state)
                
                # 确保状态正确更新
                final_status = state["progress"]["weather"]["status"]
                final_progress = state["progress"]["weather"]["progress"]
                
                events.append({
                    "type": "progress",
                    "agent": "weather",
                    "status": final_status,
                    "progress": final_progress,
                    "message": "天气查询完成" if final_status == "completed" else "天气查询失败"
                })
                
                if state["weather"]:
                    events.append({
                        "type": "data",
                        "agent": "weather",
                        "data": [w.dict() for w in state["weather"]]
                    })
            except Exception as e:
                error_msg = f"天气查询异常: {str(e)}"
                print(f"❌ {error_msg}")
                state["progress"]["weather"]["status"] = "failed"
                state["progress"]["weather"]["progress"] = 0
                events.append({
                    "type": "progress",
                    "agent": "weather",
                    "status": "failed",
                    "progress": 0,
                    "message": error_msg
                })
            
            return events
        
        async def search_hotels_with_progress():
            events = []
            try:
                state["progress"]["hotels"]["status"] = "running"
                state["progress"]["hotels"]["progress"] = 10
                events.append({
                    "type": "progress",
                    "agent": "hotels",
                    "status": "running",
                    "progress": 10,
                    "message": "正在搜索酒店..."
                })
                
                await self._search_hotels_node(state)
                
                # 确保状态正确更新
                final_status = state["progress"]["hotels"]["status"]
                final_progress = state["progress"]["hotels"]["progress"]
                
                events.append({
                    "type": "progress",
                    "agent": "hotels",
                    "status": final_status,
                    "progress": final_progress,
                    "message": "酒店搜索完成" if final_status == "completed" else "酒店搜索失败"
                })
                
                if state["hotels"]:
                    events.append({
                        "type": "data",
                        "agent": "hotels",
                        "data": state["hotels"][:5]
                    })
            except Exception as e:
                error_msg = f"酒店搜索异常: {str(e)}"
                print(f"❌ {error_msg}")
                state["progress"]["hotels"]["status"] = "failed"
                state["progress"]["hotels"]["progress"] = 0
                events.append({
                    "type": "progress",
                    "agent": "hotels",
                    "status": "failed",
                    "progress": 0,
                    "message": error_msg
                })
            
            return events
        
        # 并行执行三个搜索任务并收集所有事件
        tasks = [
            search_attractions_with_progress(),
            search_weather_with_progress(),
            search_hotels_with_progress()
        ]
        
        # 使用 asyncio.gather 并行执行，并收集所有事件
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理所有事件
        for result in results:
            if isinstance(result, Exception):
                yield {
                    "type": "error",
                    "message": f"任务执行失败: {str(result)}"
                }
                continue
            # result 现在是一个事件列表
            if isinstance(result, list):
                for event in result:
                    yield event
        
        # 生成最终计划
        state["progress"]["planning"]["status"] = "running"
        state["progress"]["planning"]["progress"] = 50
        yield {
            "type": "progress",
            "agent": "planning",
            "status": "running",
            "progress": 50,
            "message": "正在生成行程计划..."
        }
        
        state = await self._plan_trip_node(state)
        
        if state.get("plan"):
            plan = state["plan"]
            yield {
                "type": "complete",
                "plan": plan.dict() if hasattr(plan, "dict") else plan,
                "message": "旅行计划生成完成"
            }
        else:
            yield {
                "type": "error",
                "message": "旅行计划生成失败"
            }


# 全局实例
_multi_agent_planner = None


def get_multi_agent_planner() -> MultiAgentTripPlanner:
    """获取多智能体系统实例(单例模式)"""
    global _multi_agent_planner
    
    if _multi_agent_planner is None:
        _multi_agent_planner = MultiAgentTripPlanner()
    
    return _multi_agent_planner

