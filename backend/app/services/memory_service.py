"""记忆服务模块 - 管理用户对话历史和偏好"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from ..models.database import (
    User, ConversationHistory, TripHistory, UserPreferences, get_db
)
from ..models.schemas import TripRequest, TripPlan
import json
import uuid


def save_conversation(
    db: Session,
    user_id: int,
    session_id: str,
    role: str,
    content: str
):
    """保存对话到数据库"""
    conversation = ConversationHistory(
        user_id=user_id,
        session_id=session_id,
        role=role,
        content=content
    )
    db.add(conversation)
    db.commit()


def load_conversation_history(
    db: Session,
    user_id: int,
    session_id: Optional[str] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """从数据库加载对话历史"""
    query = db.query(ConversationHistory).filter(
        ConversationHistory.user_id == user_id
    )
    
    if session_id:
        query = query.filter(ConversationHistory.session_id == session_id)
    
    conversations = query.order_by(
        ConversationHistory.created_at.desc()
    ).limit(limit).all()
    
    # 转换为列表（按时间正序）
    return [
        {
            "role": conv.role,
            "content": conv.content,
            "created_at": conv.created_at.isoformat()
        }
        for conv in reversed(conversations)
    ]


def get_user_memory(
    db: Session,
    user_id: int,
    session_id: Optional[str] = None,
    limit: int = 10
) -> List[Any]:
    """获取用户的LangChain消息列表"""
    messages = []
    
    # 加载历史对话
    history = load_conversation_history(db, user_id, session_id, limit)
    
    # 将历史对话转换为LangChain消息对象
    for conv in history:
        if conv["role"] == "user":
            messages.append(HumanMessage(content=conv["content"]))
        elif conv["role"] == "assistant":
            messages.append(AIMessage(content=conv["content"]))
        elif conv["role"] == "system":
            messages.append(SystemMessage(content=conv["content"]))
    
    return messages


def get_user_preferences(db: Session, user_id: int) -> Dict[str, Any]:
    """获取用户偏好"""
    preferences = db.query(UserPreferences).filter(
        UserPreferences.user_id == user_id
    ).first()
    
    if preferences:
        return preferences.preferences_json or {}
    return {}


def update_user_preferences(
    db: Session,
    user_id: int,
    preferences: Dict[str, Any]
):
    """更新用户偏好"""
    user_prefs = db.query(UserPreferences).filter(
        UserPreferences.user_id == user_id
    ).first()
    
    if user_prefs:
        # 合并现有偏好
        existing = user_prefs.preferences_json or {}
        existing.update(preferences)
        user_prefs.preferences_json = existing
        user_prefs.updated_at = datetime.utcnow()
    else:
        # 创建新偏好记录
        user_prefs = UserPreferences(
            user_id=user_id,
            preferences_json=preferences
        )
        db.add(user_prefs)
    
    db.commit()


def save_trip_history(
    db: Session,
    user_id: int,
    request: TripRequest,
    plan: TripPlan
):
    """保存旅行历史"""
    trip_history = TripHistory(
        user_id=user_id,
        request_data=request.dict(),
        plan_data=plan.dict(),
        city=request.city,
        start_date=request.start_date,
        end_date=request.end_date,
        travel_days=request.travel_days
    )
    db.add(trip_history)
    db.commit()
    return trip_history.id


def get_trip_history(
    db: Session,
    user_id: int,
    limit: int = 20,
    offset: int = 0,
    include_plan_data: bool = False  # 新增参数，控制是否返回完整计划数据
) -> List[Dict[str, Any]]:
    """获取用户的旅行历史"""
    trips = db.query(TripHistory).filter(
        TripHistory.user_id == user_id
    ).order_by(
        TripHistory.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    result = []
    for trip in trips:
        try:
            trip_dict = {
                "id": trip.id,
                "city": trip.city or "",
                "start_date": trip.start_date or "",
                "end_date": trip.end_date or "",
                "created_at": trip.created_at.isoformat() if trip.created_at else datetime.utcnow().isoformat()
            }
            # 只有明确要求时才包含详细数据
            if include_plan_data:
                trip_dict["request_data"] = trip.request_data
                trip_dict["plan_data"] = trip.plan_data
            
            result.append(trip_dict)
        except Exception as e:
            print(f"⚠️ 处理旅行记录 {trip.id} 时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            # 跳过有问题的记录，继续处理其他记录
            continue
    
    return result


def get_trip_by_id(db: Session, trip_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """根据ID获取单个旅行记录"""
    trip = db.query(TripHistory).filter(
        TripHistory.id == trip_id,
        TripHistory.user_id == user_id
    ).first()
    
    if not trip:
        return None
    
    return {
        "id": trip.id,
        "city": trip.city,
        "start_date": trip.start_date,
        "end_date": trip.end_date,
        "request_data": trip.request_data,
        "plan_data": trip.plan_data,
        "created_at": trip.created_at.isoformat()
    }


def delete_trip_history(db: Session, trip_id: int, user_id: int) -> bool:
    """删除旅行历史记录"""
    trip = db.query(TripHistory).filter(
        TripHistory.id == trip_id,
        TripHistory.user_id == user_id
    ).first()
    
    if not trip:
        return False
    
    db.delete(trip)
    db.commit()
    return True


def extract_user_preferences_from_request(request: TripRequest) -> Dict[str, Any]:
    """从请求中提取用户偏好"""
    preferences = {
        "recent_cities": [request.city],
        "common_transportation": request.transportation,
        "common_accommodation": request.accommodation,
        "common_preferences": request.preferences,
    }
    return preferences


def update_preferences_from_trip(
    db: Session,
    user_id: int,
    request: TripRequest
):
    """从旅行请求更新用户偏好"""
    current_prefs = get_user_preferences(db, user_id)
    
    # 更新常用城市
    recent_cities = current_prefs.get("recent_cities", [])
    if request.city not in recent_cities:
        recent_cities.insert(0, request.city)
        recent_cities = recent_cities[:10]  # 保留最近10个城市
    
    # 更新常用交通方式
    transportation_history = current_prefs.get("transportation_history", {})
    transportation_history[request.transportation] = transportation_history.get(request.transportation, 0) + 1
    
    # 更新常用住宿类型
    accommodation_history = current_prefs.get("accommodation_history", {})
    accommodation_history[request.accommodation] = accommodation_history.get(request.accommodation, 0) + 1
    
    # 更新偏好标签
    preference_tags = current_prefs.get("preference_tags", {})
    for pref in request.preferences:
        preference_tags[pref] = preference_tags.get(pref, 0) + 1
    
    new_preferences = {
        "recent_cities": recent_cities,
        "transportation_history": transportation_history,
        "accommodation_history": accommodation_history,
        "preference_tags": preference_tags,
        "last_updated": datetime.utcnow().isoformat()
    }
    
    update_user_preferences(db, user_id, new_preferences)


def build_memory_context(
    db: Session,
    user_id: int,
    current_request: TripRequest
) -> str:
    """构建记忆上下文字符串，用于注入到prompt中"""
    context_parts = []
    
    # 获取用户偏好
    preferences = get_user_preferences(db, user_id)
    
    if preferences:
        # 常用城市
        recent_cities = preferences.get("recent_cities", [])
        if recent_cities:
            context_parts.append(f"用户最近访问过的城市: {', '.join(recent_cities[:5])}")
        
        # 常用交通方式
        trans_history = preferences.get("transportation_history", {})
        if trans_history:
            most_common_trans = max(trans_history.items(), key=lambda x: x[1])[0]
            context_parts.append(f"用户偏好的交通方式: {most_common_trans}")
        
        # 常用住宿类型
        acc_history = preferences.get("accommodation_history", {})
        if acc_history:
            most_common_acc = max(acc_history.items(), key=lambda x: x[1])[0]
            context_parts.append(f"用户偏好的住宿类型: {most_common_acc}")
        
        # 偏好标签
        pref_tags = preferences.get("preference_tags", {})
        if pref_tags:
            top_tags = sorted(pref_tags.items(), key=lambda x: x[1], reverse=True)[:3]
            if top_tags:
                tags_str = ", ".join([tag for tag, _ in top_tags])
                context_parts.append(f"用户常选的偏好标签: {tags_str}")
    
    # 获取最近的对话历史（简化版）
    recent_history = load_conversation_history(db, user_id, limit=5)
    if recent_history:
        context_parts.append("\n最近的对话历史:")
        for conv in recent_history[-3:]:  # 只取最近3条
            role_name = "用户" if conv["role"] == "user" else "助手"
            context_parts.append(f"{role_name}: {conv['content'][:100]}...")
    
    if context_parts:
        return "\n".join(context_parts)
    return ""

