"""旅行规划API路由"""

import json
import hashlib
import uuid
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ...models.schemas import (
    TripRequest,
    TripPlanResponse,
    ErrorResponse
)
from ...models.database import get_db, User
from ...agents.trip_planner_agent import get_trip_planner_agent
from ...agents.multi_agent_system import get_multi_agent_planner
from ...services.auth_service import get_current_user_optional
from ...services.memory_service import (
    save_trip_history,
    update_preferences_from_trip,
    save_conversation
)

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
async def plan_trip(
    request: TripRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    # 获取当前用户（可选）
    current_user = get_current_user_optional(http_request, db)
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

        # 生成会话ID（用于对话历史）
        session_id = str(uuid.uuid4())
        user_id = current_user.id if current_user else None

        # 生成旅行计划（传入user_id和session_id以支持记忆）
        print("🚀 开始生成旅行计划...")
        trip_plan = agent.plan_trip(request, user_id=user_id, session_id=session_id)

        print("✅ 旅行计划生成成功,准备返回响应\n")

        # 如果用户已登录，保存历史记录
        if current_user:
            try:
                # 保存旅行历史
                save_trip_history(db, current_user.id, request, trip_plan)
                
                # 更新用户偏好
                update_preferences_from_trip(db, current_user.id, request)
                
                # 保存对话历史
                save_conversation(
                    db,
                    current_user.id,
                    session_id,
                    "user",
                    f"请求规划{request.city}的{request.travel_days}天旅行计划"
                )
                save_conversation(
                    db,
                    current_user.id,
                    session_id,
                    "assistant",
                    f"已生成{request.city}的{request.travel_days}天旅行计划"
                )
            except Exception as e:
                print(f"⚠️ 保存历史记录失败: {str(e)}")

        response = TripPlanResponse(
            success=True,
            message="旅行计划生成成功",
            data=trip_plan,
            requires_login=current_user is None  # 如果用户未登录，提示需要登录
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
async def plan_trip_stream(
    request: TripRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    # 获取当前用户（可选）
    current_user = get_current_user_optional(http_request, db)
    """
    流式生成旅行计划
    
    Args:
        request: 旅行请求参数
        
    Returns:
        Server-Sent Events 流
    """
    async def event_generator():
        session_id = str(uuid.uuid4())
        user_id = current_user.id if current_user else None
        trip_plan = None
        
        try:
            # 发送开始事件
            yield f"data: {json.dumps({'type': 'start', 'message': '开始生成旅行计划'}, ensure_ascii=False)}\n\n"
            
            # 获取多智能体系统
            planner = get_multi_agent_planner()
            
            # 流式生成计划
            async for event in planner.plan_trip_stream(request, user_id=user_id, session_id=session_id):
                # 如果是完成事件，添加 requires_login 字段
                if event.get("type") == "complete":
                    event["requires_login"] = current_user is None
                
                yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"
                
                # 保存最终计划
                if event.get("type") == "complete" and event.get("plan"):
                    trip_plan = event.get("plan")
            
            # 如果用户已登录，保存历史记录
            if current_user and trip_plan:
                try:
                    from ...models.schemas import TripPlan
                    plan_obj = TripPlan(**trip_plan)
                    
                    # 保存旅行历史
                    save_trip_history(db, current_user.id, request, plan_obj)
                    
                    # 更新用户偏好
                    update_preferences_from_trip(db, current_user.id, request)
                    
                    # 保存对话历史
                    save_conversation(
                        db,
                        current_user.id,
                        session_id,
                        "user",
                        f"请求规划{request.city}的{request.travel_days}天旅行计划"
                    )
                    save_conversation(
                        db,
                        current_user.id,
                        session_id,
                        "assistant",
                        f"已生成{request.city}的{request.travel_days}天旅行计划"
                    )
                except Exception as e:
                    print(f"⚠️ 保存历史记录失败: {str(e)}")
            
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

