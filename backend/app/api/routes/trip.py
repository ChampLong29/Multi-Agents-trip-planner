"""旅行规划API路由"""

import json
import hashlib
from typing import Dict
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from ...models.schemas import (
    TripRequest,
    TripPlanResponse,
    ErrorResponse
)
from ...agents.trip_planner_agent import get_trip_planner_agent
from ...agents.multi_agent_system import get_multi_agent_planner

# 请求去重缓存（简单实现，生产环境应使用Redis等）
_request_cache: Dict[str, TripPlanResponse] = {}

router = APIRouter(prefix="/trip", tags=["旅行规划"])


def _get_request_hash(request: TripRequest) -> str:
    """生成请求的哈希值用于去重"""
    request_dict = request.dict()
    request_str = json.dumps(request_dict, sort_keys=True)
    return hashlib.md5(request_str.encode()).hexdigest()


@router.post(
    "/plan",
    response_model=TripPlanResponse,
    summary="生成旅行计划",
    description="根据用户输入的旅行需求,生成详细的旅行计划"
)
async def plan_trip(request: TripRequest):
    """
    生成旅行计划

    Args:
        request: 旅行请求参数

    Returns:
        旅行计划响应
    """
    try:
        # 请求去重检查
        request_hash = _get_request_hash(request)
        if request_hash in _request_cache:
            print(f"📋 发现重复请求，返回缓存结果")
            return _request_cache[request_hash]
        
        print(f"\n{'='*60}")
        print(f"📥 收到旅行规划请求:")
        print(f"   城市: {request.city}")
        print(f"   日期: {request.start_date} - {request.end_date}")
        print(f"   天数: {request.travel_days}")
        print(f"{'='*60}\n")

        # 获取Agent实例
        print("🔄 获取多智能体系统实例...")
        agent = get_trip_planner_agent()

        # 生成旅行计划
        print("🚀 开始生成旅行计划...")
        trip_plan = agent.plan_trip(request)

        print("✅ 旅行计划生成成功,准备返回响应\n")

        response = TripPlanResponse(
            success=True,
            message="旅行计划生成成功",
            data=trip_plan
        )
        
        # 缓存结果（限制缓存大小，避免内存溢出）
        if len(_request_cache) < 100:
            _request_cache[request_hash] = response
        
        return response

    except Exception as e:
        print(f"❌ 生成旅行计划失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"生成旅行计划失败: {str(e)}"
        )


@router.post(
    "/plan/stream",
    summary="流式生成旅行计划",
    description="根据用户输入的旅行需求,流式生成详细的旅行计划(SSE格式)"
)
async def plan_trip_stream(request: TripRequest):
    """
    流式生成旅行计划
    
    Args:
        request: 旅行请求参数
        
    Returns:
        Server-Sent Events 流
    """
    async def event_generator():
        try:
            # 发送开始事件
            yield f"data: {json.dumps({'type': 'start', 'message': '开始生成旅行计划'}, ensure_ascii=False)}\n\n"
            
            # 获取多智能体系统
            planner = get_multi_agent_planner()
            
            # 流式生成计划
            async for event in planner.plan_trip_stream(request):
                yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"
            
            # 发送完成事件
            yield f"data: {json.dumps({'type': 'complete', 'message': '旅行计划生成完成'}, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            error_event = {
                "type": "error",
                "message": f"生成旅行计划失败: {str(e)}"
            }
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
            import traceback
            traceback.print_exc()
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用Nginx缓冲
        }
    )


@router.get(
    "/health",
    summary="健康检查",
    description="检查旅行规划服务是否正常"
)
async def health_check():
    """健康检查"""
    try:
        # 检查多智能体系统是否可用
        planner = get_multi_agent_planner()
        
        return {
            "status": "healthy",
            "service": "trip-planner",
            "system": "langgraph-multi-agent",
            "cache_size": len(_request_cache)
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"服务不可用: {str(e)}"
        )

