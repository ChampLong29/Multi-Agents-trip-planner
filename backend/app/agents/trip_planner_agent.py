"""多智能体旅行规划系统 - 基于 LangChain"""

import json
from typing import Dict, Any, List, Optional, Union
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from ..services.llm_service import get_llm
from ..models.schemas import TripRequest, TripPlan, DayPlan, Attraction, Meal, WeatherInfo, Location, Hotel
from ..config import get_settings
from ..tools import AmapPOISearchTool, AmapWeatherTool, AmapRouteTool

# ============ Agent提示词 ============

ATTRACTION_AGENT_PROMPT = """你是景点搜索专家。你的任务是根据城市和用户偏好搜索合适的景点。

**重要提示:**
你必须使用 amap_poi_search 工具来搜索景点!不要自己编造景点信息!

**工具使用说明:**
- 使用 amap_poi_search 工具时，需要提供：
  - keywords: 搜索关键词，如"景点"、"历史文化"、"公园"等
  - city: 城市名称，如"北京"、"上海"等
  - citylimit: 是否限制在城市范围内（默认true）

**示例:**
用户: "搜索北京的历史文化景点"
你应该调用: amap_poi_search(keywords="历史文化", city="北京", citylimit=True)

用户: "搜索上海的公园"
你应该调用: amap_poi_search(keywords="公园", city="上海", citylimit=True)

**注意:**
1. 必须使用工具,不要直接回答
2. 根据用户偏好选择合适的关键词
3. 返回的POI信息要包含名称、地址、经纬度等详细信息
"""

WEATHER_AGENT_PROMPT = """你是天气查询专家。你的任务是查询指定城市的天气信息。

**重要提示:**
你必须使用 amap_weather 工具来查询天气!不要自己编造天气信息!

**工具使用说明:**
- 使用 amap_weather 工具时，需要提供：
  - city: 城市名称，如"北京"、"上海"等

**示例:**
用户: "查询北京天气"
你应该调用: amap_weather(city="北京")

用户: "上海的天气怎么样"
你应该调用: amap_weather(city="上海")

**注意:**
1. 必须使用工具,不要直接回答
2. 返回的天气信息要包含未来几天的预报
3. 包括日期、白天/夜间天气、温度、风向、风力等信息
"""

HOTEL_AGENT_PROMPT = """你是酒店推荐专家。你的任务是根据城市和景点位置推荐合适的酒店。

**重要提示:**
你必须使用 amap_poi_search 工具来搜索酒店!不要自己编造酒店信息!

**工具使用说明:**
- 使用 amap_poi_search 工具时，需要提供：
  - keywords: 搜索关键词，使用"酒店"或"宾馆"
  - city: 城市名称
  - citylimit: 是否限制在城市范围内（默认true）

**示例:**
用户: "搜索北京的酒店"
你应该调用: amap_poi_search(keywords="酒店", city="北京", citylimit=True)

**注意:**
1. 必须使用工具,不要直接回答
2. 关键词使用"酒店"或"宾馆"
3. 返回的酒店信息要包含名称、地址、经纬度、价格范围、评分等
"""

PLANNER_AGENT_PROMPT = """你是行程规划专家。你的任务是根据景点信息和天气信息,生成详细的旅行计划。

请严格按照以下JSON格式返回旅行计划:
```json
{
  "city": "城市名称",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "days": [
    {
      "date": "YYYY-MM-DD",
      "day_index": 0,
      "description": "第1天行程概述",
      "transportation": "交通方式",
      "accommodation": "住宿类型",
      "hotel": {
        "name": "酒店名称",
        "address": "酒店地址",
        "location": {"longitude": 116.397128, "latitude": 39.916527},
        "price_range": "300-500元",
        "rating": "4.5",
        "distance": "距离景点2公里",
        "type": "经济型酒店",
        "estimated_cost": 400
      },
      "attractions": [
        {
          "name": "景点名称",
          "address": "详细地址",
          "location": {"longitude": 116.397128, "latitude": 39.916527},
          "visit_duration": 120,
          "description": "景点详细描述",
          "category": "景点类别",
          "ticket_price": 60
        }
      ],
      "meals": [
        {"type": "breakfast", "name": "早餐推荐", "description": "早餐描述", "estimated_cost": 30},
        {"type": "lunch", "name": "午餐推荐", "description": "午餐描述", "estimated_cost": 50},
        {"type": "dinner", "name": "晚餐推荐", "description": "晚餐描述", "estimated_cost": 80}
      ]
    }
  ],
  "weather_info": [
    {
      "date": "YYYY-MM-DD",
      "day_weather": "晴",
      "night_weather": "多云",
      "day_temp": 25,
      "night_temp": 15,
      "wind_direction": "南风",
      "wind_power": "1-3级"
    }
  ],
  "overall_suggestions": "总体建议",
  "budget": {
    "total_attractions": 180,
    "total_hotels": 1200,
    "total_meals": 480,
    "total_transportation": 200,
    "total": 2060
  }
}
```

**重要提示:**
1. weather_info数组必须包含每一天的天气信息
2. 温度必须是纯数字(不要带°C等单位)
3. 每天安排2-3个景点
4. 考虑景点之间的距离和游览时间
5. 每天必须包含早中晚三餐
6. 提供实用的旅行建议
7. **必须包含预算信息**:
   - 景点门票价格(ticket_price)
   - 餐饮预估费用(estimated_cost)
   - 酒店预估费用(estimated_cost)
   - 预算汇总(budget)包含各项总费用
"""


class MultiAgentTripPlanner:
    """多智能体旅行规划系统 - 基于 LangChain"""

    def __init__(self):
        """初始化多智能体系统"""
        print("🔄 开始初始化多智能体旅行规划系统（LangChain）...")

        try:
            settings = get_settings()
            self.llm = get_llm()

            # 创建 LangChain 工具实例（共享）
            print("  - 创建 LangChain 高德地图工具...")
            self.poi_tool = AmapPOISearchTool()
            self.weather_tool = AmapWeatherTool()
            self.route_tool = AmapRouteTool()
            
            # 使用 LangChain 工具
            attraction_tools = [self.poi_tool]
            weather_tools = [self.weather_tool]
            hotel_tools = [self.poi_tool]
            
            # 创建景点搜索Agent
            print("  - 创建景点搜索Agent...")
            self.attraction_agent = self._create_agent(
                name="景点搜索专家",
                system_prompt=ATTRACTION_AGENT_PROMPT,
                tools=attraction_tools
            )

            # 创建天气查询Agent
            print("  - 创建天气查询Agent...")
            self.weather_agent = self._create_agent(
                name="天气查询专家",
                system_prompt=WEATHER_AGENT_PROMPT,
                tools=weather_tools
            )

            # 创建酒店推荐Agent
            print("  - 创建酒店推荐Agent...")
            self.hotel_agent = self._create_agent(
                name="酒店推荐专家",
                system_prompt=HOTEL_AGENT_PROMPT,
                tools=hotel_tools
            )

            # 创建行程规划Agent(不需要工具)
            print("  - 创建行程规划Agent...")
            self.planner_agent = self._create_agent(
                name="行程规划专家",
                system_prompt=PLANNER_AGENT_PROMPT,
                tools=[]
            )

            print(f"✅ 多智能体系统初始化成功")
            print(f"   景点搜索Agent: {len(attraction_tools)} 个工具")
            print(f"   天气查询Agent: {len(weather_tools)} 个工具")
            print(f"   酒店推荐Agent: {len(hotel_tools)} 个工具")

        except Exception as e:
            print(f"❌ 多智能体系统初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def _create_agent(self, name: str, system_prompt: str, tools: List) -> Any:
        """
        创建 LangChain Agent (使用新版本 API)
        
        Args:
            name: Agent 名称
            system_prompt: 系统提示词
            tools: 工具列表
            
        Returns:
            Agent graph 实例或简单的 LLM 链
        """
        if tools:
            # 使用新的 create_agent API
            agent_graph = create_agent(
                model=self.llm,
                tools=tools,
                system_prompt=system_prompt,
                debug=True
            )
            
            # 包装为兼容的接口
            class AgentWrapper:
                def __init__(self, graph, name):
                    self.graph = graph
                    self.name = name
                
                def invoke(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
                    # 新 API 使用 messages 格式
                    from langchain_core.messages import HumanMessage
                    messages = [HumanMessage(content=input_data.get("input", ""))]
                    result = self.graph.invoke({"messages": messages})
                    # 提取最后一条消息的内容
                    if isinstance(result, dict) and "messages" in result:
                        last_message = result["messages"][-1]
                        output = last_message.content if hasattr(last_message, "content") else str(last_message)
                    else:
                        output = str(result)
                    return {"output": output}
            
            return AgentWrapper(agent_graph, name)
        else:
            # 没有工具时，使用简单的 LLM 链
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "{input}"),
            ])
            
            chain = prompt | self.llm | StrOutputParser()
            
            # 包装为兼容的接口
            class SimpleAgentWrapper:
                def __init__(self, chain, name):
                    self.chain = chain
                    self.name = name
                
                def invoke(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
                    result = self.chain.invoke(input_data)
                    return {"output": result}
            
            return SimpleAgentWrapper(chain, name)
    
    def plan_trip(self, request: TripRequest, user_id: Optional[int] = None, session_id: Optional[str] = None) -> TripPlan:
        """
        使用多智能体协作生成旅行计划

        Args:
            request: 旅行请求
            user_id: 用户ID（可选，用于加载记忆）
            session_id: 会话ID（可选，用于对话历史）

        Returns:
            旅行计划
        """
        try:
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
            print(f"偏好: {', '.join(request.preferences) if request.preferences else '无'}")
            print(f"{'='*60}\n")

            # 步骤1: 景点搜索Agent搜索景点
            print("📍 步骤1: 搜索景点...")
            attraction_query = self._build_attraction_query(request)
            if hasattr(self.attraction_agent, 'invoke'):
                attraction_result = self.attraction_agent.invoke({"input": attraction_query})
                attraction_response = attraction_result.get("output", str(attraction_result))
            else:
                attraction_response = str(self.attraction_agent.invoke({"input": attraction_query}))
            print(f"景点搜索结果: {attraction_response[:200]}...\n")

            # 步骤2: 天气查询Agent查询天气
            print("🌤️  步骤2: 查询天气...")
            weather_query = f"请查询{request.city}的天气信息"
            if hasattr(self.weather_agent, 'invoke'):
                weather_result = self.weather_agent.invoke({"input": weather_query})
                weather_response = weather_result.get("output", str(weather_result))
            else:
                weather_response = str(self.weather_agent.invoke({"input": weather_query}))
            print(f"天气查询结果: {weather_response[:200]}...\n")

            # 步骤3: 酒店推荐Agent搜索酒店
            print("🏨 步骤3: 搜索酒店...")
            hotel_query = f"请搜索{request.city}的{request.accommodation}酒店"
            if hasattr(self.hotel_agent, 'invoke'):
                hotel_result = self.hotel_agent.invoke({"input": hotel_query})
                hotel_response = hotel_result.get("output", str(hotel_result))
            else:
                hotel_response = str(self.hotel_agent.invoke({"input": hotel_query}))
            print(f"酒店搜索结果: {hotel_response[:200]}...\n")

            # 步骤4: 行程规划Agent整合信息生成计划
            print("📋 步骤4: 生成行程计划...")
            planner_query = self._build_planner_query(request, attraction_response, weather_response, hotel_response, memory_context)
            if hasattr(self.planner_agent, 'invoke'):
                planner_result = self.planner_agent.invoke({"input": planner_query})
                planner_response = planner_result.get("output", str(planner_result))
            else:
                planner_response = str(self.planner_agent.invoke({"input": planner_query}))
            print(f"行程规划结果: {planner_response[:300]}...\n")

            # 解析最终计划
            trip_plan = self._parse_response(planner_response, request)

            print(f"{'='*60}")
            print(f"✅ 旅行计划生成完成!")
            print(f"{'='*60}\n")

            return trip_plan

        except Exception as e:
            print(f"❌ 生成旅行计划失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._create_fallback_plan(request)
    
    def _build_attraction_query(self, request: TripRequest) -> str:
        """构建景点搜索查询"""
        keywords = []
        if request.preferences:
            # 只取第一个偏好作为关键词
            keywords = request.preferences[0]
        else:
            keywords = "景点"

        # 使用自然语言描述，让 Agent 自动调用工具
        query = f"请搜索{request.city}的{keywords}相关景点。关键词使用'{keywords}'，城市是'{request.city}'。"
        return query

    def _build_planner_query(self, request: TripRequest, attractions: str, weather: str, hotels: str = "", memory_context: str = "") -> str:
        """构建行程规划查询"""
        query = f"""请根据以下信息生成{request.city}的{request.travel_days}天旅行计划:

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
            query += f"**用户历史偏好和对话记忆:**\n{memory_context}\n\n"
        
        query += f"""**景点信息:**
{attractions}

**天气信息:**
{weather}

**酒店信息:**
{hotels}

**要求:**
1. 每天安排2-3个景点
2. 每天必须包含早中晚三餐
3. 每天推荐一个具体的酒店(从酒店信息中选择)
3. 考虑景点之间的距离和交通方式
4. 返回完整的JSON格式数据
5. 景点的经纬度坐标要真实准确
6. 如果提供了用户历史偏好，请参考这些偏好来优化计划
"""
        if request.free_text_input:
            query += f"\n**额外要求:** {request.free_text_input}"

        return query
    
    def _parse_response(self, response: str, request: TripRequest) -> TripPlan:
        """
        解析Agent响应
        
        Args:
            response: Agent响应文本
            request: 原始请求
            
        Returns:
            旅行计划
        """
        try:
            # 尝试从响应中提取JSON
            # 查找JSON代码块
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "{" in response and "}" in response:
                # 直接查找JSON对象
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
        """创建备用计划(当Agent失败时)"""
        from datetime import datetime, timedelta
        
        # 解析日期
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
        
        # 创建每日行程
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


# 全局多智能体系统实例
_multi_agent_planner = None


def get_trip_planner_agent() -> MultiAgentTripPlanner:
    """获取多智能体旅行规划系统实例(单例模式)"""
    global _multi_agent_planner

    if _multi_agent_planner is None:
        _multi_agent_planner = MultiAgentTripPlanner()

    return _multi_agent_planner

