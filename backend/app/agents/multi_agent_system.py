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
                
                poi_info = POIInfo(
                    id=poi_data.get("id", ""),
                    name=poi_data.get("name", ""),
                    address=poi_data.get("address", ""),
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
            
            # 调用工具查询天气
            result_str = await self.weather_tool._arun(city=request.city)
            result = json.loads(result_str)
            
            if result.get("error"):
                state["errors"].append(f"天气查询失败: {result['error']}")
                state["progress"]["weather"]["status"] = "failed"
                return state
            
            # 解析天气数据
            forecasts = result.get("forecasts", [])
            weather_list = []
            
            # 计算日期范围
            start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
            end_date = datetime.strptime(request.end_date, "%Y-%m-%d")
            
            for i in range(request.travel_days):
                current_date = start_date + timedelta(days=i)
                date_str = current_date.strftime("%Y-%m-%d")
                
                # 查找匹配的天气数据
                weather_data = None
                for forecast in forecasts:
                    if forecast.get("date") == date_str:
                        weather_data = forecast
                        break
                
                if weather_data:
                    weather_info = WeatherInfo(
                        date=date_str,
                        day_weather=weather_data.get("dayweather", ""),
                        night_weather=weather_data.get("nightweather", ""),
                        day_temp=weather_data.get("daytemp", 0),
                        night_temp=weather_data.get("nighttemp", 0),
                        wind_direction=weather_data.get("daywind", ""),
                        wind_power=weather_data.get("daypower", "")
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
            planner_prompt = self._build_planner_prompt(
                request, 
                state["attractions"], 
                state["weather"], 
                state["hotels"]
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
        hotels: List[Dict[str, Any]]
    ) -> str:
        """构建规划提示词"""
        attractions_text = "\n".join([
            f"- {attr.name} ({attr.address})"
            for attr in attractions[:20]
        ])
        
        weather_text = "\n".join([
            f"- {w.date}: 白天{w.day_weather} {w.day_temp}°C, 夜间{w.night_weather} {w.night_temp}°C"
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

**可用景点:**
{attractions_text}

**天气信息:**
{weather_text}

**可用酒店:**
{hotels_text}

**要求:**
1. 每天安排2-3个景点
2. 每天必须包含早中晚三餐
3. 每天推荐一个具体的酒店(从可用酒店中选择)
4. 考虑景点之间的距离和交通方式
5. 返回完整的JSON格式数据
6. 景点的经纬度坐标要真实准确

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
            
            # 解析JSON
            data = json.loads(json_str)
            
            # 转换为TripPlan对象
            trip_plan = TripPlan(**data)
            
            return trip_plan
            
        except Exception as e:
            print(f"⚠️  解析响应失败: {str(e)}")
            print(f"   将使用备用方案生成计划")
            return self._create_fallback_plan(request)
    
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
    
    async def plan_trip(self, request: TripRequest) -> TripPlan:
        """生成旅行计划"""
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
            "messages": []
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
        request: TripRequest
    ) -> AsyncIterator[Dict[str, Any]]:
        """流式生成旅行计划"""
        # 发送开始事件
        yield {
            "type": "start",
            "message": "开始生成旅行计划",
            "progress": 0
        }
        
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
            "messages": []
        }
        
        # 创建带进度回调的节点函数（包装为协程，收集事件）
        async def search_attractions_with_progress():
            events = []
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
            
            events.append({
                "type": "progress",
                "agent": "attractions",
                "status": state["progress"]["attractions"]["status"],
                "progress": state["progress"]["attractions"]["progress"],
                "message": "景点搜索完成"
            })
            
            if state["attractions"]:
                events.append({
                    "type": "data",
                    "agent": "attractions",
                    "data": [attr.dict() for attr in state["attractions"][:5]]
                })
            
            return events
        
        async def search_weather_with_progress():
            events = []
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
            
            events.append({
                "type": "progress",
                "agent": "weather",
                "status": state["progress"]["weather"]["status"],
                "progress": state["progress"]["weather"]["progress"],
                "message": "天气查询完成"
            })
            
            if state["weather"]:
                events.append({
                    "type": "data",
                    "agent": "weather",
                    "data": [w.dict() for w in state["weather"]]
                })
            
            return events
        
        async def search_hotels_with_progress():
            events = []
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
            
            events.append({
                "type": "progress",
                "agent": "hotels",
                "status": state["progress"]["hotels"]["status"],
                "progress": state["progress"]["hotels"]["progress"],
                "message": "酒店搜索完成"
            })
            
            if state["hotels"]:
                events.append({
                    "type": "data",
                    "agent": "hotels",
                    "data": state["hotels"][:5]
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
            yield {
                "type": "complete",
                "plan": state["plan"].dict(),
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

