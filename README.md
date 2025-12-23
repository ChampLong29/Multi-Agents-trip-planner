# 智能旅行规划系统 🌍✈️

> 基于 LangChain 和 LangGraph 的多智能体协作系统，提供个性化的智能旅行规划服务

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3.x-green.svg)](https://vuejs.org/)
[![LangChain](https://img.shields.io/badge/LangChain-0.2+-orange.svg)](https://www.langchain.com/)
[![License](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

## 📋 目录

- [项目概述](#项目概述)
- [功能模块组成](#功能模块组成)
- [技术架构设计](#技术架构设计)
- [核心创新点](#核心创新点)
- [关键代码解析](#关键代码解析)
- [快速开始](#快速开始)
- [操作手册](#操作手册)
- [API 文档](#api-文档)
- [项目结构](#项目结构)
- [技术栈](#技术栈)

---

## 🎯 项目概述

智能旅行规划系统是一个基于 **LangChain** 和 **LangGraph** 构建的多智能体协作系统，旨在为用户提供个性化的旅行规划服务。系统通过多个专业智能体的并行协作，实现景点搜索、天气查询、酒店推荐和行程规划的智能化处理。

### 核心特性

- 🤖 **多智能体协作**：基于 LangGraph 实现真正的多智能体并行协作
- 🔄 **流式响应**：支持 Server-Sent Events (SSE) 实时推送进度和结果
- 🗺️ **高德地图集成**：深度集成高德地图 API，提供 POI 搜索、路线规划、天气查询
- 🎨 **现代化前端**：Vue 3 + TypeScript + Pinia，响应式设计，实时进度显示
- ⚡ **高性能**：并行执行减少等待时间，流式响应提升用户体验
- 👤 **用户认证系统**：支持用户注册、登录，JWT token 身份验证
- 🧠 **智能记忆功能**：集成 LangChain 记忆系统，记住用户偏好和历史对话
- 💾 **数据持久化**：SQLite 数据库存储用户数据、旅行历史和对话记录
- 📋 **历史记录管理**：查看和管理历史旅行计划和对话记录

---

## 🏗️ 功能模块组成

### 1. 后端核心模块

#### 1.1 多智能体系统 (`backend/app/agents/`)

**文件结构：**
- `multi_agent_system.py` - LangGraph 多智能体系统核心实现
- `trip_planner_agent.py` - 旅行规划智能体封装

**功能模块：**

1. **景点搜索智能体 (Attraction Agent)**
   - 根据用户偏好搜索相关景点
   - 调用高德地图 POI 搜索 API
   - 返回景点名称、地址、经纬度、类型等信息

2. **天气查询智能体 (Weather Agent)**
   - 查询旅行期间的天气预报
   - 支持多日天气查询
   - 返回温度、天气状况、风力等信息
   - 自动生成穿着建议和活动建议
   - 根据天气影响行程规划（雨天优先室内、避免步行等）

3. **酒店推荐智能体 (Hotel Agent)**
   - 根据住宿偏好推荐酒店
   - 考虑地理位置和价格区间
   - 返回酒店名称、地址、评分等信息

4. **行程规划智能体 (Planner Agent)**
   - 整合所有智能体的结果
   - 生成详细的每日行程安排
   - 优化路线和时间分配

#### 1.2 工具系统 (`backend/app/tools/`)

**文件结构：**
- `amap_tools.py` - 高德地图 LangChain 工具封装
- `mcp_adapter.py` - MCP 协议适配器（可选）

**工具列表：**

- `AmapPOISearchTool` - POI 搜索工具
- `AmapWeatherTool` - 天气查询工具
- `AmapRouteTool` - 路线规划工具

#### 1.3 服务层 (`backend/app/services/`)

**文件结构：**
- `llm_service.py` - LLM 服务管理（单例模式）
- `amap_service.py` - 高德地图 API 封装
- `unsplash_service.py` - 图片服务（可选）

#### 1.4 数据模型 (`backend/app/models/`)

**文件结构：**
- `schemas.py` - Pydantic 数据模型
- `database.py` - SQLAlchemy 数据库模型

**数据库模型：**
- `User` - 用户表（用户名、邮箱、密码哈希）
- `ConversationHistory` - 对话历史表
- `TripHistory` - 旅行历史表
- `UserPreferences` - 用户偏好表

#### 1.5 认证和记忆服务 (`backend/app/services/`)

**文件结构：**
- `auth_service.py` - 认证服务（密码加密、JWT生成和验证）
- `memory_service.py` - 记忆服务（保存/加载对话历史、用户偏好）

**功能：**
- 用户密码加密（bcrypt）
- JWT token 生成和验证
- 用户偏好自动提取和更新
- 对话历史管理
- LangChain 记忆集成

#### 1.6 API 路由 (`backend/app/api/routes/`)

**文件结构：**
- `trip.py` - 旅行规划相关 API
- `map.py` - 地图相关 API
- `poi.py` - POI 相关 API
- `auth.py` - 认证相关 API
- `history.py` - 历史记录相关 API

**主要端点：**
- `POST /api/trip/plan` - 同步生成旅行计划
- `POST /api/trip/plan/stream` - 流式生成旅行计划（SSE）
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息
- `GET /api/history/trips` - 获取旅行历史
- `GET /api/history/trips/{trip_id}` - 获取单个旅行记录
- `POST /api/history/trips/save` - 保存旅行计划
- `DELETE /api/history/trips/{trip_id}` - 删除旅行记录
- `GET /api/history/conversations` - 获取对话历史

### 2. 前端核心模块

#### 2.1 状态管理 (`frontend/src/stores/`)

**文件结构：**
- `tripStore.ts` - 旅行规划状态管理
- `authStore.ts` - 用户认证状态管理

**管理状态：**
- 请求状态（loading, progress）
- 智能体工作状态
- 流式数据（attractions, weather, hotels）
- 生成的旅行计划
- 错误信息
- 用户登录状态和用户信息

#### 2.2 组件系统 (`frontend/src/components/`)

**文件结构：**
- `AgentStatus.vue` - 智能体状态显示组件
- `StreamingContent.vue` - 流式内容展示组件

#### 2.3 页面视图 (`frontend/src/views/`)

**文件结构：**
- `Home.vue` - 首页（表单输入、实时进度显示）
- `Result.vue` - 结果页（行程展示、地图可视化）
- `Login.vue` - 登录/注册页面
- `History.vue` - 历史记录查看页面

#### 2.4 API 服务 (`frontend/src/services/`)

**文件结构：**
- `api.ts` - 前端 API 服务封装
- `auth.ts` - 认证服务封装

**功能：**
- 流式请求支持
- 请求去重（AbortController）
- 错误重试机制（指数退避）
- JWT token 自动管理
- 请求拦截器（自动添加 token）
- 响应拦截器（处理 401 错误）

---

## 🎨 技术架构设计

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层 (Vue 3)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Home.vue   │  │  Result.vue  │  │  Components  │      │
│  │  (表单输入)   │  │  (结果展示)   │  │  (状态组件)   │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │               │
│         └──────────────────┼──────────────────┘               │
│                            │                                   │
│                    ┌───────▼────────┐                         │
│                    │   Pinia Store   │                         │
│                    │  (状态管理)     │                         │
│                    └───────┬─────────┘                         │
└────────────────────────────┼───────────────────────────────────┘
                             │ HTTP/SSE
┌────────────────────────────▼───────────────────────────────────┐
│                      API 层 (FastAPI)                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  POST /api/trip/plan/stream  (流式响应)                  │  │
│  │  POST /api/trip/plan          (同步响应)                  │  │
│  │  POST /api/auth/login         (用户认证)                  │  │
│  │  GET  /api/history/trips      (历史记录)                  │  │
│  └──────────────────────┬───────────────────────────────────┘  │
└──────────────────────────┼───────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────────┐  ┌──────────────┐
│  认证服务     │  │  多智能体系统      │  │  记忆服务     │
│ (Auth Service)│  │  (LangGraph)     │  │(Memory Service)│
│              │  │                  │  │              │
│ - 用户注册   │  │  ┌────────────┐  │  │ - 保存历史   │
│ - 用户登录   │  │  │协调智能体   │  │  │ - 加载偏好   │
│ - JWT验证    │  │  └─────┬──────┘  │  │ - 对话记录   │
└──────┬───────┘  │        │         │  └──────┬───────┘
       │          │   ┌────┼────┐   │          │
       │          │   │    │    │   │          │
       │          │   ▼    ▼    ▼   │          │
       │          │ ┌──┐ ┌──┐ ┌──┐ │          │
       │          │ │景点│ │天气│ │酒店│ │          │
       │          │ │搜索│ │查询│ │推荐│ │          │
       │          │ └──┘ └──┘ └──┘ │          │
       │          │   │    │    │   │          │
       │          │   └────┼────┘   │          │
       │          │        │         │          │
       │          │        ▼         │          │
       │          │   ┌──────────┐   │          │
       │          │   │行程规划   │   │          │
       │          │   │智能体     │   │          │
       │          │   └──────────┘   │          │
       │          └──────────────────┘          │
       │                                        │
       └────────────────┬───────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  数据库层     │ │  外部API     │ │  外部API     │
│ (SQLite)     │ │ (高德地图)    │ │ (LLM服务)    │
│              │ │              │ │              │
│ - users      │ │ - POI搜索    │ │ - 规划生成   │
│ - trip_history│ │ - 天气查询   │ │ - 对话理解   │
│ - conversation│ │ - 路线规划   │ │              │
│ - preferences│ │              │ │              │
└──────────────┘ └──────────────┘ └──────────────┘
```

### 数据流设计

1. **用户输入** → 前端表单收集用户需求
2. **请求发送** → 前端通过 SSE 或 HTTP 发送请求
3. **并行执行** → 三个智能体并行执行（景点、天气、酒店）
4. **状态更新** → 实时推送进度和部分结果
5. **结果整合** → 行程规划智能体整合所有信息
6. **流式返回** → 逐步返回完整旅行计划
7. **前端渲染** → 实时更新 UI，展示结果

### 状态管理设计

使用 LangGraph 的 `TypedDict` 定义状态：

```python
class TripPlanningState(TypedDict):
    request: TripRequest          # 用户请求
    attractions: List[POIInfo]   # 景点信息
    weather: List[WeatherInfo]    # 天气信息
    hotels: List[Hotel]          # 酒店信息
    plan: Optional[TripPlan]     # 最终计划
    errors: List[str]            # 错误信息
```

---

## 💡 核心创新点

### 1. 从 HelloAgents 到 LangChain 的架构升级

**重构前（HelloAgents）：**
- 使用 `SimpleAgent` 和 `MCPTool`
- 串行执行，性能较差
- 难以实现真正的多智能体协作

**重构后（LangChain + LangGraph）：**
- 使用 `LangGraph` 实现状态机管理
- 并行执行多个智能体任务
- 真正的多智能体协作和通信

### 2. 并行执行优化

**创新点：**
- 使用 `asyncio.gather()` 实现三个智能体并行执行
- 总等待时间从串行的 4 步减少到并行的 3 步
- 性能提升约 40-60%

**实现方式：**
```python
# 并行执行三个智能体
results = await asyncio.gather(
    fetch_attractions_node(state),
    fetch_weather_node(state),
    fetch_hotels_node(state)
)
```

### 3. 流式响应机制

**创新点：**
- 使用 Server-Sent Events (SSE) 实现流式响应
- 实时推送每个智能体的工作状态
- 支持部分结果的逐步渲染

**优势：**
- 用户无需等待全部完成即可看到部分结果
- 实时进度显示提升用户体验
- 减少用户等待焦虑

### 4. 请求去重机制

**创新点：**
- 基于请求内容的 MD5 哈希实现去重
- 防止用户重复提交相同请求
- 前端使用 `AbortController` 取消重复请求

**实现方式：**
```python
def _generate_request_hash(request_data: TripRequest) -> str:
    json_str = json.dumps(request_data.model_dump(), sort_keys=True)
    return hashlib.md5(json_str.encode('utf-8')).hexdigest()
```

### 5. 前端状态管理优化

**创新点：**
- 使用 Pinia 进行全局状态管理
- 智能体工作状态的实时更新
- 流式数据的逐步渲染

### 6. 智能体状态可视化

**创新点：**
- 创建 `AgentStatus` 组件显示每个智能体的工作状态
- 支持动画效果和进度指示
- 实时更新智能体的进度和消息

### 7. 用户记忆和个性化

**创新点：**
- 集成 LangChain 的 ConversationBufferMemory
- 自动提取和更新用户偏好（常用城市、交通方式、住宿类型等）
- 在生成新计划时自动应用历史偏好
- 支持查看历史旅行计划和对话记录

**实现方式：**
```python
# 加载用户记忆上下文
memory_context = build_memory_context(db, user_id, request)

# 注入到规划 prompt 中
prompt += f"**用户历史偏好和对话记忆:**\n{memory_context}\n\n"
```

---

## 💻 关键代码解析

### 1. 多智能体系统核心实现

**文件：** `backend/app/agents/multi_agent_system.py`

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional
from langchain_openai import ChatOpenAI

class TripPlanningState(TypedDict):
    """旅行规划状态定义"""
    request: TripRequest
    attractions: List[POIInfo]
    weather: List[WeatherInfo]
    hotels: List[Hotel]
    plan: Optional[TripPlan]
    errors: List[str]

class MultiAgentTripPlanner:
    """多智能体旅行规划系统"""
    
    def __init__(self):
        self.llm = get_llm()
        self.amap_service = AmapService()
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """构建 LangGraph 状态图"""
        workflow = StateGraph(TripPlanningState)
        
        # 添加节点
        workflow.add_node("fetch_attractions", self._fetch_attractions_node)
        workflow.add_node("fetch_weather", self._fetch_weather_node)
        workflow.add_node("fetch_hotels", self._fetch_hotels_node)
        workflow.add_node("plan_trip_step", self._plan_trip_step_node)
        
        # 定义边（并行执行）
        workflow.add_edge("fetch_attractions", "plan_trip_step")
        workflow.add_edge("fetch_weather", "plan_trip_step")
        workflow.add_edge("fetch_hotels", "plan_trip_step")
        workflow.add_edge("plan_trip_step", END)
        
        return workflow.compile()
    
    async def _fetch_attractions_node(self, state: TripPlanningState):
        """景点搜索节点"""
        # 实现景点搜索逻辑
        pass
```

### 2. LangChain 工具封装

**文件：** `backend/app/tools/amap_tools.py`

```python
from langchain_core.tools import BaseTool
from typing import Optional
import json

class AmapPOISearchTool(BaseTool):
    """高德地图 POI 搜索工具"""
    
    name: str = "amap_poi_search"
    description: str = "使用高德地图搜索POI（兴趣点），如景点、酒店、餐厅等。"
    
    def _run(self, keywords: str, city: str, citylimit: bool = True) -> str:
        """同步执行"""
        service = AmapService()
        pois = service.search_poi(keywords=keywords, city=city, citylimit=citylimit)
        return json.dumps([p.model_dump() for p in pois], ensure_ascii=False)
    
    async def _arun(self, keywords: str, city: str, citylimit: bool = True) -> str:
        """异步执行"""
        service = AmapService()
        pois = await service.asearch_poi(keywords=keywords, city=city, citylimit=citylimit)
        return json.dumps([p.model_dump() for p in pois], ensure_ascii=False)
```

### 3. 流式响应 API

**文件：** `backend/app/api/routes/trip.py`

```python
from fastapi.responses import StreamingResponse
import json

@router.post("/plan/stream")
async def plan_trip_stream(request_data: TripRequest):
    """流式生成旅行计划"""
    request_hash = _generate_request_hash(request_data)
    
    if request_hash in _ongoing_tasks:
        raise HTTPException(status_code=409, detail="请求正在处理中")
    
    async def event_generator():
        try:
            # 发送开始事件
            yield f"data: {json.dumps({'type': 'start', 'message': '开始生成旅行计划'})}\n\n"
            
            agent = get_trip_planner_agent()
            
            # 流式生成计划
            async for event in agent.plan_trip_stream(request_data):
                yield f"data: {json.dumps(event)}\n\n"
            
            # 发送完成事件
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            _ongoing_tasks.pop(request_hash, None)
    
    task = asyncio.create_task(event_generator())
    _ongoing_tasks[request_hash] = task
    return StreamingResponse(task, media_type="text/event-stream")
```

### 4. 前端流式请求处理

**文件：** `frontend/src/services/api.ts`

```typescript
let currentAbortController: AbortController | null = null

export async function generateTripPlanStream(
  formData: TripFormData,
  onProgress: (update: ProgressUpdate) => void
): Promise<TripPlanResponse> {
  // 取消之前的请求
  if (currentAbortController) {
    currentAbortController.abort()
  }
  
  // 创建新请求
  currentAbortController = new AbortController()
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/trip/plan/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData),
      signal: currentAbortController.signal
    })
    
    const reader = response.body?.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    
    while (reader) {
      const { done, value } = await reader.read()
      if (done) break
      
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n\n')
      buffer = lines.pop() || ''
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6))
          onProgress(data)
        }
      }
    }
    
    // 返回最终结果
    return { success: true, data: finalPlan }
  } finally {
    currentAbortController = null
  }
}
```

### 5. Pinia 状态管理

**文件：** `frontend/src/stores/tripStore.ts`

```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useTripStore = defineStore('trip', () => {
  const isRequesting = ref(false)
  const overallProgress = ref(0)
  const progress = ref<Record<string, AgentProgress>>({})
  const streamingData = ref({
    attractions: [] as POIInfo[],
    weather: [] as WeatherInfo[],
    hotels: [] as Hotel[]
  })
  const tripPlan = ref<TripPlan | null>(null)
  const error = ref<string | null>(null)
  
  function startRequest(requestId: string) {
    isRequesting.value = true
    overallProgress.value = 0
    error.value = null
  }
  
  function updateProgress(update: ProgressUpdate) {
    if (update.step) {
      progress.value[update.step] = {
        agent: update.step,
        status: update.type === 'error' ? 'failed' : 
                update.type === 'complete' ? 'completed' : 'running',
        progress: calculateProgress(update.step),
        message: update.message || ''
      }
    }
    
    if (update.data) {
      // 更新流式数据
      if (update.data.attractions) {
        streamingData.value.attractions = update.data.attractions
      }
      // ... 其他数据更新
    }
  }
  
  return {
    isRequesting,
    overallProgress,
    progress,
    streamingData,
    tripPlan,
    error,
    startRequest,
    updateProgress,
    setTripPlan,
    setError,
    reset
  }
})
```

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 16+
- 高德地图 API 密钥
- LLM API 密钥（支持 OpenAI、DeepSeek 等）

### 后端安装

1. **进入后端目录**
```bash
cd backend
```

2. **安装依赖（使用 uv）**
```bash
uv sync
```

或使用 pip：
```bash
pip install -r requirements.txt
```

3. **配置环境变量**

创建 `.env` 文件：
```bash
# 高德地图 API（需要在高德开放平台申请）
AMAP_API_KEY=your_amap_api_key_here

# LLM 配置（支持 OpenAI、DeepSeek 等兼容 OpenAI 格式的 API）
LLM_API_KEY=your_llm_api_key_here
LLM_BASE_URL=https://api.openai.com/v1  # 或你的 LLM 服务地址
LLM_MODEL_ID=gpt-4  # 或你的模型 ID

# JWT 配置（生产环境请务必修改为强密钥）
JWT_SECRET_KEY=your-secret-key-change-in-production

# 可选：图片服务
UNSPLASH_ACCESS_KEY=your_unsplash_key_here
```

4. **数据库初始化**

数据库会在应用启动时自动创建。数据库文件位于 `backend/data/trip_planner.db`。

5. **启动后端服务**
```bash
uv run uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

或使用：
```bash
uv run python run.py
```

### 前端安装

1. **进入前端目录**
```bash
cd frontend
```

2. **安装依赖**
```bash
npm install
```

3. **配置环境变量**

创建 `.env` 文件：
```bash
# 高德地图 Web API Key（用于前端地图显示）
VITE_AMAP_WEB_KEY=your_amap_web_key_here
# 后端 API 地址
VITE_API_BASE_URL=http://localhost:8000
```

4. **启动开发服务器**
```bash
npm run dev
```

5. **访问应用**

打开浏览器访问 `http://localhost:5173`

---

## 📖 操作手册

### 0. 用户注册和登录

#### 注册新用户

1. 打开应用首页
2. 点击右上角 **"登录"** 按钮
3. 切换到 **"注册"** 标签页
4. 填写以下信息：
   - **用户名**：3-50个字符
   - **邮箱**：有效的邮箱地址
   - **密码**：至少6个字符
   - **确认密码**：再次输入密码
5. 点击 **"注册"** 按钮
6. 注册成功后自动切换到登录页面

#### 登录

1. 在登录页面输入用户名或邮箱和密码
2. 点击 **"登录"** 按钮
3. 登录成功后自动跳转到首页

**注意：**
- 未登录用户仍可使用系统生成旅行计划，但不会保存历史记录
- 登录用户可以查看和管理历史记录，系统会记住您的偏好

### 1. 生成旅行计划

#### 步骤 1：填写基本信息

1. 打开应用首页
2. 填写以下信息：
   - **目的地城市**：输入要旅行的城市名称（如：北京、上海）
   - **开始日期**：选择旅行开始日期
   - **结束日期**：选择旅行结束日期
   - **旅行天数**：系统会自动计算（也可手动调整）

#### 步骤 2：设置偏好

1. **交通方式**：选择偏好
   - 公共交通
   - 自驾
   - 步行
   - 混合

2. **住宿偏好**：选择类型
   - 经济型酒店
   - 舒适型酒店
   - 豪华酒店
   - 民宿

3. **旅行偏好**：选择标签（可多选）
   - 🏛️ 历史文化
   - 🏞️ 自然风光
   - 🍜 美食
   - 🛍️ 购物
   - 🎨 艺术
   - ☕ 休闲

4. **额外要求**：输入特殊需求（可选）
   - 例如：想去看升旗、需要无障碍设施、对海鲜过敏等

#### 步骤 3：生成计划

1. 点击 **"开始规划我的旅行"** 按钮
2. 系统将显示实时进度：
   - 🔍 景点搜索智能体：正在搜索...
   - 🌤️ 天气查询智能体：正在查询...
   - 🏨 酒店推荐智能体：正在推荐...
   - 📋 行程规划智能体：正在生成计划...
3. 可以实时查看已找到的景点、天气信息、酒店推荐
4. 生成完成后自动跳转到结果页

### 2. 查看旅行计划

#### 行程概览

- 查看旅行日期范围
- 查看总体建议和注意事项

#### 每日行程

- 点击侧边栏的日期查看每日详细安排
- 包含：
  - 景点游览（名称、地址、建议游览时间）
  - 餐饮推荐（餐厅名称、地址、特色）
  - 交通路线（起点、终点、路线类型）
  - 住宿信息（酒店名称、地址、类型）

#### 景点地图

- 查看所有景点的地图标记
- 点击标记查看景点详情
- 查看景点间的路线规划

#### 天气信息

- 查看旅行期间的天气预报
- 包含温度、天气状况、风力等信息

#### 预算明细

- 查看预估的旅行预算
- 包含交通、住宿、餐饮、门票等费用

### 3. 保存旅行计划

#### 保存到历史记录

1. **重要提示**：请等待旅行计划完全加载完成后再点击保存按钮
   - 如果计划还在加载中，保存按钮会被禁用
   - 在加载完成前点击保存可能导致无响应
   - 保存成功后，按钮会变为不可用状态，防止重复保存

2. 点击 **"💾 保存到我的历史"** 按钮
3. 系统会保存当前旅行计划到您的历史记录
4. 保存成功后，您可以在历史记录页面查看和管理

**注意：**
- 只有登录用户才能保存旅行计划
- 每个计划只能保存一次（保存后按钮会禁用）
- 保存的计划会出现在历史记录中，方便随时查看

### 4. 编辑和导出

#### 编辑行程

1. 点击 **"✏️ 编辑行程"** 按钮
2. 修改行程内容
3. 点击 **"💾 保存修改"** 保存更改
4. 或点击 **"❌ 取消编辑"** 取消修改

#### 导出行程

1. 点击 **"📥 导出行程"** 下拉菜单
2. 选择导出格式：
   - **📷 导出为图片**：生成行程图片
   - **📄 导出为PDF**：生成 PDF 文档

### 5. 查看历史记录

#### 查看旅行历史

1. 登录后，点击右上角 **"历史记录"** 按钮
2. 在 **"旅行记录"** 标签页查看所有历史旅行计划
3. 点击某个记录可以查看详情
4. 点击 **"加载此计划"** 可以重新加载该计划到结果页
5. 点击 **"删除"** 按钮可以删除不需要的记录（会弹出确认对话框）

#### 查看对话历史

1. 在历史记录页面切换到 **"对话历史"** 标签页
2. 查看与系统的历史对话记录
3. 了解系统如何根据您的偏好生成计划

**功能说明：**
- 系统会自动记录每次旅行规划请求和生成的计划
- 系统会学习您的偏好（常用城市、交通方式、住宿类型等）
- 在生成新计划时，系统会参考您的历史偏好，提供更个性化的建议

### 6. 常见问题

#### Q: 为什么生成计划需要较长时间？

A: 系统需要并行调用多个智能体（景点搜索、天气查询、酒店推荐），然后整合信息生成详细计划。通常需要 30-60 秒。

#### Q: 可以取消正在生成的计划吗？

A: 可以。在生成过程中点击 **"取消"** 按钮即可取消请求。

#### Q: 生成的计划不满意怎么办？

A: 可以返回首页重新生成，或使用编辑功能手动调整。

#### Q: 支持哪些城市？

A: 支持高德地图 API 覆盖的所有城市。

#### Q: 为什么要注册登录？

A: 注册登录后，系统可以：
- 记住您的旅行偏好，提供更个性化的建议
- 保存您的旅行历史，方便随时查看
- 记录对话历史，让系统更好地理解您的需求

#### Q: 未登录可以使用吗？

A: 可以。未登录用户可以使用所有核心功能，但不会保存历史记录和偏好。

---

## 📄 API 文档

启动后端服务后，访问以下地址查看完整 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 主要 API 端点

#### 1. 生成旅行计划（同步）

```http
POST /api/trip/plan
Content-Type: application/json

{
  "city": "北京",
  "start_date": "2024-06-01",
  "end_date": "2024-06-03",
  "travel_days": 3,
  "transportation": "公共交通",
  "accommodation": "舒适型酒店",
  "preferences": ["历史文化", "美食"],
  "free_text_input": "想去看升旗"
}
```

**响应：**
```json
{
  "success": true,
  "message": "旅行计划生成成功",
  "data": {
    "city": "北京",
    "start_date": "2024-06-01",
    "end_date": "2024-06-03",
    "days": [...],
    "budget": {...},
    "weather_info": [...]
  }
}
```

#### 2. 生成旅行计划（流式）

```http
POST /api/trip/plan/stream
Content-Type: application/json

{
  "city": "北京",
  ...
}
```

**响应格式（SSE）：**
```
data: {"type": "start", "message": "开始生成旅行计划"}

data: {"type": "progress", "step": "attractions", "message": "正在搜索景点...", "data": {...}}

data: {"type": "progress", "step": "weather", "message": "正在查询天气...", "data": {...}}

data: {"type": "progress", "step": "hotels", "message": "正在推荐酒店...", "data": {...}}

data: {"type": "progress", "step": "plan", "message": "正在生成计划...", "data": {...}}

data: {"type": "complete"}
```

#### 3. 搜索 POI

```http
GET /api/poi/search?keywords=天安门&city=北京
```

#### 4. 查询天气

```http
GET /api/map/weather?city=北京&extensions=all
```

#### 5. 规划路线

```http
POST /api/map/route
Content-Type: application/json

{
  "origin": "天安门",
  "destination": "故宫",
  "strategy": "walking"
}
```

#### 6. 用户注册

```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123"
}
```

**响应：**
```json
{
  "success": true,
  "message": "注册成功",
  "data": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "created_at": "2025-01-01T00:00:00"
  }
}
```

#### 7. 用户登录

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "testuser",
  "password": "password123"
}
```

**响应：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### 8. 获取当前用户信息

```http
GET /api/auth/me
Authorization: Bearer {access_token}
```

#### 9. 获取旅行历史

```http
GET /api/history/trips?limit=20&offset=0
Authorization: Bearer {access_token}
```

#### 10. 获取对话历史

```http
GET /api/history/conversations?limit=20&session_id={session_id}
Authorization: Bearer {access_token}
```

#### 11. 保存旅行计划

```http
POST /api/history/trips/save
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "request": {
    "city": "北京",
    "start_date": "2024-06-01",
    "end_date": "2024-06-03",
    ...
  },
  "plan": {
    "city": "北京",
    "days": [...],
    ...
  }
}
```

#### 12. 删除旅行记录

```http
DELETE /api/history/trips/{trip_id}
Authorization: Bearer {access_token}
```

---

## 📁 项目结构

```
intelligent-trip-planner/  # 或你的项目名称
├── backend/                          # 后端服务
│   ├── app/
│   │   ├── agents/                   # 智能体实现
│   │   │   ├── multi_agent_system.py  # LangGraph 多智能体系统
│   │   │   └── trip_planner_agent.py # 旅行规划智能体封装
│   │   ├── api/                      # FastAPI 路由
│   │   │   ├── main.py               # 主应用
│   │   │   └── routes/
│   │   │       ├── trip.py           # 旅行规划 API
│   │   │       ├── map.py            # 地图 API
│   │   │       └── poi.py            # POI API
│   │   ├── tools/                     # LangChain 工具
│   │   │   ├── amap_tools.py         # 高德地图工具
│   │   │   └── mcp_adapter.py        # MCP 适配器
│   │   ├── services/                 # 服务层
│   │   │   ├── llm_service.py        # LLM 服务
│   │   │   ├── amap_service.py       # 高德地图服务
│   │   │   ├── unsplash_service.py   # Unsplash 图片服务
│   │   │   └── image_service.py      # 多源图片服务（统一接口）
│   │   ├── models/                    # 数据模型
│   │   │   ├── schemas.py            # Pydantic 模型
│   │   │   └── database.py           # SQLAlchemy 数据库模型
│   │   ├── services/                 # 服务层
│   │   │   ├── llm_service.py        # LLM 服务
│   │   │   ├── amap_service.py       # 高德地图服务
│   │   │   ├── unsplash_service.py   # Unsplash 图片服务
│   │   │   ├── image_service.py       # 多源图片服务（统一接口）
│   │   │   ├── auth_service.py        # 认证服务
│   │   │   └── memory_service.py     # 记忆服务
│   │   └── config.py                  # 配置管理
│   ├── requirements.txt               # Python 依赖
│   ├── pyproject.toml                 # 项目配置
│   ├── .env.example                   # 环境变量示例
│   └── run.py                         # 启动脚本
│
├── frontend/                          # 前端应用
│   ├── src/
│   │   ├── components/                # Vue 组件
│   │   │   ├── AgentStatus.vue        # 智能体状态组件
│   │   │   └── StreamingContent.vue   # 流式内容组件
│   │   ├── stores/                    # Pinia 状态管理
│   │   │   ├── tripStore.ts           # 旅行状态管理
│   │   │   └── authStore.ts           # 认证状态管理
│   │   ├── services/                  # API 服务
│   │   │   ├── api.ts                 # API 封装
│   │   │   └── auth.ts                # 认证服务封装
│   │   ├── views/                      # 页面视图
│   │   │   ├── Home.vue               # 首页
│   │   │   ├── Result.vue             # 结果页
│   │   │   ├── Login.vue              # 登录/注册页
│   │   │   └── History.vue            # 历史记录页
│   │   ├── types/                      # TypeScript 类型
│   │   │   └── index.ts               # 类型定义
│   │   ├── App.vue                     # 根组件
│   │   └── main.ts                     # 入口文件
│   ├── package.json                   # 前端依赖
│   ├── vite.config.ts                 # Vite 配置
│   └── tsconfig.json                   # TypeScript 配置
│
└── README.md                          # 项目文档
```

---

## 🛠️ 技术栈

### 后端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 编程语言 |
| FastAPI | 0.104+ | Web 框架 |
| LangChain | 0.2.0+ | LLM 应用框架 |
| LangGraph | 0.0.60+ | 多智能体状态机 |
| LangChain-OpenAI | 0.1.7+ | OpenAI 集成 |
| Pydantic | 2.0+ | 数据验证 |
| httpx | 0.25+ | HTTP 客户端 |
| uvicorn | 0.24+ | ASGI 服务器 |
| SQLAlchemy | 2.0+ | ORM 框架 |
| passlib | 1.7+ | 密码加密 |
| python-jose | 3.3+ | JWT 处理 |

### 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue | 3.x | 前端框架 |
| TypeScript | 5.x | 类型系统 |
| Vite | 5.x | 构建工具 |
| Pinia | 2.1.7+ | 状态管理 |
| Ant Design Vue | 4.x | UI 组件库 |
| Axios | 1.6+ | HTTP 客户端 |
| 高德地图 JS API | - | 地图服务 |

### 外部服务

- **高德地图 API**：POI 搜索、路线规划、天气查询
- **LLM API**：OpenAI、DeepSeek 等（支持兼容 OpenAI 格式的 API）
- **Unsplash API**（可选）：景点图片

---

## 📝 开发日志

### 重构历程

1. **第一阶段：依赖迁移**
   - 移除 `hello-agents` 依赖
   - 添加 `LangChain` 和 `LangGraph` 依赖

2. **第二阶段：核心重构**
   - 重构 LLM 服务（使用 `ChatOpenAI`）
   - 创建 LangChain 工具类
   - 实现 LangGraph 多智能体系统

3. **第三阶段：API 增强**
   - 添加流式响应端点
   - 实现请求去重机制

4. **第四阶段：前端优化**
   - 添加 Pinia 状态管理
   - 实现流式请求处理
   - 创建智能体状态组件
   - 优化用户体验

5. **第五阶段：用户认证和记忆功能**
   - 实现用户注册和登录系统
   - 集成 SQLite 数据库
   - 添加 LangChain 记忆功能
   - 实现用户偏好自动提取
   - 创建历史记录管理功能
   - 前端认证和路由守卫

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发流程

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 🙏 致谢

### 特别感谢

本项目基于 [Hello-Agents](https://github.com/datawhalechina/Hello-Agents) 教程中的示例项目进行重构和优化。Hello-Agents 是 Datawhale 社区的系统性智能体学习教程，提供了从零开始构建智能体系统的完整指南。

- **原项目仓库**: [datawhalechina/Hello-Agents](https://github.com/datawhalechina/Hello-Agents)
- **在线文档**: [Hello-Agents 在线文档](https://datawhalechina.github.io/hello-agents/)

### 技术栈致谢

- [LangChain](https://www.langchain.com/) - LLM 应用框架
- [LangGraph](https://github.com/langchain-ai/langgraph) - 多智能体状态机
- [高德地图开放平台](https://lbs.amap.com/) - 地图服务
- [Vue.js](https://vuejs.org/) - 前端框架
- [Ant Design Vue](https://antdv.com/) - UI 组件库
- [Unsplash](https://unsplash.com/) - 图片服务

---

## 📧 联系方式

如有问题或建议，欢迎通过以下方式联系：

- 提交 [Issue](https://github.com/your-username/your-repo-name/issues)（请替换为你的仓库地址）
- 发送邮件至：wzlong25@stu.pku.edu.cn

---

## 📝 项目说明

### 与原项目的关系

本项目是基于 [Hello-Agents](https://github.com/datawhalechina/Hello-Agents) 教程中第13章的示例项目进行重构和优化的版本。主要改进包括：

1. **架构升级**：从 HelloAgents 框架迁移到 LangChain + LangGraph
2. **性能优化**：实现真正的多智能体并行执行
3. **功能增强**：添加流式响应、请求去重、多源图片服务等
4. **UI 改进**：现代化前端设计，更好的用户体验
5. **代码重构**：优化代码结构，提高可维护性
6. **用户系统**：添加用户认证、数据持久化和历史记录管理
7. **智能记忆**：集成 LangChain 记忆系统，实现个性化推荐

### 开源协议

本项目采用与原项目相同的 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) 协议。

---

**智能旅行规划系统** - 让旅行计划变得简单而智能 🌈

---

*最后更新：2025年12月13日*

## 🆕 最新更新

### v1.2.0 - 功能增强

**新增功能：**
- ✅ 历史记录删除功能
- ✅ 天气功能增强（自动生成穿着建议和活动建议）
- ✅ 智能行程调整（根据天气自动优化行程，雨天优先室内景点）
- ✅ 旅行计划保存功能（支持直接保存现有计划）
- ✅ 行程编辑功能（支持删除、移动景点等操作）
- ✅ 数据格式优化（改进显示格式，修复索引问题）

**技术改进：**
- 改进 JSON 解析错误处理
- 优化流式响应状态同步
- 增强数据验证和修复机制
- 改进前端状态管理

### v1.1.0 - 用户认证和记忆功能

**新增功能：**
- ✅ 用户注册和登录系统（JWT token 认证）
- ✅ SQLite 数据库支持（用户、历史记录、偏好）
- ✅ LangChain 记忆功能集成
- ✅ 用户偏好自动提取和更新
- ✅ 历史记录查看和管理
- ✅ 前端认证状态管理和路由守卫

**技术改进：**
- 使用 SQLAlchemy ORM 进行数据管理
- 使用 bcrypt 进行密码加密
- 使用 python-jose 处理 JWT token
- 集成 LangChain ConversationBufferMemory
- 前端自动 token 管理和错误处理

**使用说明：**
- 未登录用户仍可使用所有核心功能
- 登录用户可以享受个性化推荐和历史记录管理
- 系统会自动学习用户偏好，提供更精准的旅行建议

---

## ⚠️ 已知问题

以下问题已知，将在后续版本中修复：

1. **历史记录重复保存问题**
   - **问题描述**：已保存的历史记录加载后可以再次保存，导致重复记录
   - **表现**：
     - 历史记录页面只显示一个记录
     - 主页的最近旅游历史中会显示多个重复记录
     - 删除时需要删除所有重复记录才能完全删除
   - **临时解决方案**：避免重复保存已加载的历史记录

2. **其他已知问题**
   - 如有其他问题，请通过 Issue 反馈
