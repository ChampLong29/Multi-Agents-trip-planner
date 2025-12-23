"""历史记录API路由"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...models.database import get_db, User
from ...models.schemas import UserResponse
from ...services.auth_service import get_current_user
from ...services.memory_service import (
    get_trip_history,
    get_trip_by_id,
    load_conversation_history,
    save_trip_history,
    update_preferences_from_trip,
    delete_trip_history
)
from ...models.schemas import TripRequest, TripPlan

router = APIRouter(prefix="/history", tags=["历史记录"])


@router.get("/trips", summary="获取旅行历史")
async def get_user_trips(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的旅行历史"""
    trips = get_trip_history(db, current_user.id, limit=limit, offset=offset)
    
    return {
        "success": True,
        "message": "获取成功",
        "data": trips,
        "total": len(trips)
    }


@router.get("/trips/{trip_id}", summary="获取单个旅行记录")
async def get_trip(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """根据ID获取单个旅行记录"""
    trip = get_trip_by_id(db, trip_id, current_user.id)
    
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="旅行记录不存在"
        )
    
    return {
        "success": True,
        "message": "获取成功",
        "data": trip
    }


@router.get("/conversations", summary="获取对话历史")
async def get_conversations(
    session_id: Optional[str] = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的对话历史"""
    conversations = load_conversation_history(
        db,
        current_user.id,
        session_id=session_id,
        limit=limit
    )
    
    return {
        "success": True,
        "message": "获取成功",
        "data": conversations,
        "total": len(conversations)
    }


@router.post("/trips/save", summary="保存旅行计划")
async def save_trip_plan(
    request: TripRequest,
    plan: TripPlan,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """直接保存现有的旅行计划到历史记录"""
    try:
        # 保存旅行历史
        trip_id = save_trip_history(db, current_user.id, request, plan)
        
        # 更新用户偏好
        update_preferences_from_trip(db, current_user.id, request)
        
        return {
            "success": True,
            "message": "计划已保存到历史记录",
            "data": {"trip_id": trip_id}
        }
    except Exception as e:
        print(f"⚠️ 保存旅行计划失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存计划失败: {str(e)}"
        )


@router.delete("/trips/{trip_id}", summary="删除旅行记录")
async def delete_trip(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除指定的旅行记录"""
    try:
        success = delete_trip_history(db, trip_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="旅行记录不存在或无权删除"
            )
        
        return {
            "success": True,
            "message": "旅行记录已删除"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"⚠️ 删除旅行记录失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除记录失败: {str(e)}"
        )

